import os
import subprocess
import json
import time
import pandas as pd
from setting import *

logger = get_logger(os.path.join(path_cfg['base_path'], path_cfg['process_log_path']))
logger.info(process_cfg)

REQ = int(process_cfg["start_req"])  # 启动时初始REQ值，默认为0
MAX_REQ = int(process_cfg["max_req"])  # 最大REQ值，默认为100，即REQ范围是（0,99）
LATEST_FILE = None


def create_symlink(source_path, target_path, overwrite=False):
    try:
        # 创建符号链接
        os.symlink(source_path, target_path)
        print(f"符号链接已成功创建: {target_path} -> {source_path}")
    except FileExistsError:
        if overwrite:
            # 如果文件已存在并且指定了覆盖选项，则先删除目标文件，然后重新创建符号链接
            os.remove(target_path)
            os.symlink(source_path, target_path)
            print(f"已覆盖并成功创建符号链接: {target_path} -> {source_path}")
        else:
            print(f"创建符号链接失败: 目标文件已存在 ({target_path})")
    except OSError as e:
        print(f"创建符号链接失败: {e}")


def generate_file(folder, user_id, gene_data):
    """生成输入文件，返回输入文件路径和输出文件路径

    :param folder (path): 输入和输出文件的文件夹路径
    :param user_id (int): user id
    :param gene_data (dict): 要处理的基因数据

    :return: tuple: (输入文件路径, 输出文件路径)
    """
    logger.info(f"Generate file for user: {user_id}")
    fm = "R%y%m%d{:" + f'0{len(str(MAX_REQ - 1))}d' + "}"
    req_str = time.strftime(fm.format(REQ), time.localtime())
    time_str = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    length = sum([i['length'] for i in gene_data])
    len_str = 'WF3p1' if length <= 650 else 'MWF5p2'
    name = f'REQIN_{len_str}_[{req_str}]_{time_str}.txt'
    df = pd.DataFrame(gene_data)
    columns_to_keep = ["GeneName", "Seq5NC", "SeqAA", "Seq3NC", "VectorID", "Species", "ForbiddenSeqs", 'IntraREQSN']
    df = df[columns_to_keep]
    desired_columns_order = COLUMNS
    df_reordered = df.reindex(columns=desired_columns_order)
    # 设置Plate和WellPos列的值为NS，REQID列值为req_str
    df_reordered['Plate'] = 'NS'
    df_reordered['WellPos'] = 'NS'
    df_reordered['REQID'] = req_str

    # 这里文件夹是什么来着
    input_folder = os.path.join(folder, req_str, "Database_REQ")
    output_folder = os.path.join(folder, req_str, "Database_PRJ")
    os.makedirs(input_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)
    
    # 创建链接, 用于 MATLAB 程序读取
    create_symlink('/cygene4/pipeline/Dev_20231130_ForShiyi/*.txt', os.path.join(folder, req_str), overwrite=True)
    create_symlink('/cygene4/pipeline/Dev_20231130_ForShiyi/*.m',   os.path.join(folder, req_str), overwrite=True)

    temp_file = os.path.join(input_folder, name)
    df_reordered.to_csv(temp_file, index=False, sep='\t')
    if DEBUG:
        output_file = os.path.join(output_folder, '0_PRJIN_MWF5p2_[R2312120]_20231212_225210_IDcorrected.txt')
    else:
        output_file = os.path.join(output_folder, f"0_PRJIN_{len_str}_[{req_str}]_{time_str}_IDcorrected.txt")
    return temp_file, output_file


def process_genes_in_file(folder, file_path):
    """处理最新下载的json文件中的所有基因数据, 返回输入输出文件路径列表。
    将会生成输入文件在file_path中，然后调用 MATLAB 程序，
    执行完后将会在file_path中生成输出文件

    :param folder (path): Matlab输入输出文件夹路径；
    :param file_path (path): 最新下载的json文件路径

    :return: list[tuple(path,path)]: 输入输出文件路径列表
    """
    # 
    # 实现你的处理逻辑，调用 MATLAB 程序等
    global REQ
    logger.info(f"Process file: {file_path} REQ: {REQ}")
    with open(file_path, 'r') as file:
        data = json.load(file)

    io_files = []
    process_list = []
    err_files = []
    for user_id, gene_data in data.items():
        temp_file, output_file = generate_file(folder, user_id, gene_data)
        io_files.append((user_id, temp_file, output_file))

        # 调用 MATLAB 程序
        subprocess.run(['matlab', '-nodisplay', '-nosplash', '-nodesktop', '-r', "run('Script1_REQtoSACfI_5p2_3p1.m'); exit;"], shell=True)
        subprocess.run(['matlab', '-nodisplay', '-nosplash', '-nodesktop', '-r', "run('Script2_SACfI_to_SACfO.m'); exit;"], shell=True)
        subprocess.run(['matlab', '-nodisplay', '-nosplash', '-nodesktop', '-r', "run('Script3_SACfOtoDone_5p2_3p1.m'); exit;"], shell=True)
        # process_list.append(process)
        err_files.append((user_id, temp_file, output_file))
        REQ = (REQ + 1) % MAX_REQ

    # # 等待所有 MATLAB 程序运行结束
    # for process in process_list:
    #     process.wait()

    return io_files, err_files


def update_process_done(done_path, io_files):
    """更新 done.json 文件"""
    processed_data = {}
    if os.path.exists(done_path):
        with open(done_path, 'r') as file:
            processed_data = json.load(file)

    for user_id, infile, outfile in io_files:
        df = pd.read_csv(outfile, sep='\t')
        ## 取其中的部分列
        columns_to_keep = ["REQID", "IntraREQSN", "VectorID", "FullSeqREAL"]
        datas = df[columns_to_keep].to_dict(orient='records')
        req = datas[0]["REQID"]
        if user_id in processed_data:
            processed_data[user_id][req] = datas
        else:
            # 若processed_data中没有user_id，则新建一个，且key为req
            processed_data[user_id] = {req: datas}

    with open(done_path, 'w') as file:
        json.dump(processed_data, file, indent=4)

    logger.info(f"Update done.json: {done_path}")


def update_error_process(error_path, err_files):
    """更新 error_process.json 文件"""
    if not err_files or len(err_files) == 0:
        return
    logger.info(f"Find error files: {err_files}")
    error_data = []
    if os.path.exists(error_path):
        with open(error_path, 'r') as file:
            error_data = json.load(file)

    for user_id, input, output in err_files:
        error_data.append((user_id, input, output))

    with open(error_path, 'w') as file:
        json.dump(error_data, file, indent=4)


def run():
    global LATEST_FILE
    date_str = time.strftime(path_cfg["datestr_in_path"], time.localtime())
    folder_path = os.path.join(path_cfg['base_path'], date_str)
    pre_data_folder = os.path.join(folder_path, path_cfg['pre_data_path'])
    io_files_folder = os.path.join(folder_path, path_cfg['io_files_path'])

    if not os.path.exists(pre_data_folder):
        return False
    if not os.path.exists(io_files_folder):
        logger.info(f'Make io files folder {io_files_folder}')
        os.makedirs(io_files_folder)

    done_path = os.path.join(folder_path, path_cfg['done_path'])
    error_path = os.path.join(folder_path, path_cfg['error_path'])

    if len(os.listdir(pre_data_folder)):
        return 0
    latest_file = sorted(os.listdir(pre_data_folder))[-1]

    if LATEST_FILE is not None and LATEST_FILE == latest_file:
        return 0
    else:
        LATEST_FILE = latest_file

    io_files, error_files = process_genes_in_file(io_files_folder, os.path.join(pre_data_folder, latest_file))
    update_process_done(done_path, io_files)
    update_error_process(error_path, error_files)
    return len(io_files) > 0


logger.info("Running core_process.py")
while not DEBUG:
    try:
        # 如果有值被处理，则尝试马上进入下一轮处理，这是因为一轮处理可能长达几十分钟，可能已经有新的值了
        if run():
            continue
        else:
            logger.info("No files need to be processed")
            logger.info(f"Sleep {PROCESS_WAIT} seconds")
            time.sleep(PROCESS_WAIT)
    except Exception as e:
        logger.error(f"Error: {e}")
        time.sleep(PROCESS_WAIT)

if DEBUG:
    logger.info("Running on debug mode. 该模式下Logger不会输入文件中，并且只会执行一次")
    run()
