import os
import subprocess
import json
import time
import pandas as pd
from setting import *

logger = get_logger(os.path.join(path_cfg['base_path'], path_cfg['process_log_path']))
REQ = int(process_cfg["start_req"])  # 启动时初始REQ值，默认为0
MAX_REQ = int(process_cfg["max_req"])  # 最大REQ值，默认为100，即REQ范围是（0,99）
LATEST_FILE = None


def generate_file(folder, user_id, gene_data):
    # 处理一个 order 的数据
    # 返回临时文件路径和输出文件路径
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
    temp_file = os.path.join(folder, name)
    df_reordered.to_csv(temp_file, index=False, sep='\t')
    if DEBUG:
        output_file = os.path.join(folder, '0_PRJIN_MWF5p2_[R2312120]_20231212_225210_IDcorrected.txt')
    else:
        output_file = os.path.join(folder, f"0_PRJIN_{len_str}_[{req_str}]_{time_str}_IDcorrected.txt")
    return temp_file, output_file


def process_genes_in_file(folder, file_path):
    # 处理文件中的所有基因数据
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
        # process = subprocess.Popen(["matlab", "-nodisplay", "-nosplash", "-nodesktop", "-r", f"run('{temp_file}', '{output_file}')"])
        # process_list.append(process)
        # err_files.append((user_id, temp_file, output_file))
        REQ = (REQ + 1) % MAX_REQ

    # 等待所有 MATLAB 程序运行结束
    # for process in process_list:
    #     process.wait()

    return io_files, err_files


def update_process_done(done_path, io_files):
    # 更新 done.json

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
    # 更新 error_process.json
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
        os.makedirs(io_files_folder)

    done_path = os.path.join(folder_path, path_cfg['done_path'])
    error_path = os.path.join(folder_path, path_cfg['error_path'])
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
            logger.info(f"Sleep {PROCESS_WAIT} seconds")
            time.sleep(PROCESS_WAIT)
    except Exception as e:
        logger.error(f"Error: {e}")
        time.sleep(PROCESS_WAIT)

if DEBUG:
    logger.info("Run debug mode. 该模式下Logger不会输入文件中")
    run()
