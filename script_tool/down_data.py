from datetime import datetime, timedelta
import os
import time
import requests
import json
from setting import *

logger = get_logger(os.path.join(path_cfg['base_path'], path_cfg['down_log_path']))

def poll_cloud_api():
    """轮询云服务API，获取未处理数据
    返回数据格式：{user_id:[{'gene_id':id,'name':xxxx, 'seq':xxx,'nc':xxx,...},{}],
    """
    # 调用云服务的API，获取未处理数据
    # 返回数据格式：{user_id:[{'gene_id':id,'name':xxxx, 'seq':xxx,'nc':xxx,...},{}],
    #               user_id:[{'gene_id':id,'name':xxxx, 'seq':xxx,'nc':xxx,...},{}]}
    params = {'token': down_cfg.get('token')}
    res = requests.get(down_cfg.get('down_url'), params=params)
    logger.info(f"Get data from cloud api. Status code: {res.status_code}")
    return res.json()


def save_data_to_file(file_path, data):
    """将获取到的数据保存到文件

    :param file_path: 保存文件的路径
    :param data: 获取到的数据
    """
    # 将获取到的数据保存到文件
    for u, l in data.items():
        cnt = 0
        for i in l:
            i['IntraREQSN'] = cnt
            cnt += 1
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)
    logger.info(f"Save data to file: {file_path}")


def find_last_file_hours_ago(pre_data_folder):
    """找到给定TIMEDELTA_HOUR小时前的最后文件
    TIMEDELTA_HOUR可以在setting.ini中设置，默认为6小时

    :param pre_data_folder: 预处理数据文件夹
    :return: 文件路径
    """
    # 找到六小时前的最后文件
    files = os.listdir(pre_data_folder)
    # 将文件名转换为时间对象
    file_times = [datetime.strptime(file[:-5], "%H-%M") for file in files]
    current_time = datetime.now().replace(second=0, microsecond=0, day=1, month=1, year=1900)

    hours_ago = current_time - timedelta(hours=TIMEDELTA_HOUR)
    recent_files = [file for file, time in zip(files, file_times) if hours_ago > time]
    # 按照时间排序
    if not recent_files:
        return None
    else:
        t = sorted(recent_files, key=lambda x: file_times[files.index(x)])[-1]
        logger.info(f"Find last file six hours ago: {t}")
        return t


def find_long_wait_data(pre_data_folder, long_wait_path, new_data):
    """找到长时间未处理的数据

    :param pre_data_folder: 预处理数据文件夹
    :param long_wait_path: 保存长时间未处理数据的文件的路径
    :param new_data: 新获取的数据
    """
    # 找到长时间未处理的数据
    filepath = find_last_file_hours_ago(pre_data_folder)
    if filepath is None:
        return None
    with open(os.path.join(pre_data_folder, filepath), 'r') as file:
        old_data = json.load(file)
    old_ids = set(old_data.keys())
    new_ids = set(new_data.keys())
    # 返回长时间未处理的订单号
    long_wait_ids = old_ids.intersection(new_ids)
    # 添加到 long_wait.json
    long_wait_vs = {}
    for user_id in long_wait_ids:
        old_vs = set([i['VectorID'] for i in old_data[user_id]])
        new_vs = set([i['VectorID'] for i in new_data[user_id]])
        long_wait_vs[user_id] = list(old_vs.intersection(new_vs))

    with open(long_wait_path, 'w') as file:
        json.dump(long_wait_vs, file, indent=4)


def run():
    data = poll_cloud_api()
    date_str = time.strftime(path_cfg["datestr_in_path"], time.localtime())
    time_str = time.strftime("%H-%M", time.localtime())
    folder_path = os.path.join(path_cfg['base_path'], date_str)
    pre_data_folder = os.path.join(folder_path, path_cfg['pre_data_path'])
    if not os.path.exists(pre_data_folder):
        os.mkdir(pre_data_folder)

    pre_data_path = os.path.join(pre_data_folder, f"{time_str}.json")
    long_wait_path = os.path.join(folder_path, path_cfg['long_wait_path'])

    if data:
        save_data_to_file(pre_data_path, data)
        if USE_CHECK:
            find_long_wait_data(pre_data_folder, long_wait_path, data)

logger.info("Running down_data.py")
while not DEBUG:
    try:
        run()
        logger.info(f"Wait {DOWN_WAIT} seconds")
        time.sleep(DOWN_WAIT)  # 休眠10分钟
    except Exception as e:
        logger.error(f"Error: {e}")
        time.sleep(DOWN_WAIT)  # 出错时也休眠10分钟

if DEBUG:
    logger.info("Running on debug mode. 该模式下Logger不会输入文件中，并且只会执行一次")
    run()
