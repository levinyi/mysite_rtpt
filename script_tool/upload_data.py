import os
import requests
import json
import time
from setting import *

logger = get_logger(os.path.join(path_cfg['base_path'], path_cfg['upload_log_path']))
logger.info(upload_cfg)

def upload_data(data):
    """上传数据到云服务器

    :param data: 待上传数据
    :return: 成功与否的状态
    """
    headers = {'Content-Type': 'application/json;charset=utf-8',
               'token': upload_cfg['token']}
    logger.debug(f"{upload_cfg['upload_url']}, {headers}, {data}")
    res = requests.post(url=upload_cfg['upload_url'], json=data, headers=headers)
    if res.status_code == 200 and res.json()['status'] == 'success':
        logger.info(f"Upload {len(data)} data success!")
        return True
    else:
        logger.error(f"Upload {len(data)} data failed!")
        return False


def update_uploaded(uploaded_path, uploaded_data):
    # 更新 uploaded.json
    with open(uploaded_path, 'w') as file:
        json.dump(uploaded_data, file, indent=4)


def run():
    date_str = time.strftime(path_cfg["datestr_in_path"], time.localtime())
    folder_path = os.path.join(path_cfg['base_path'], date_str)
    done_path = os.path.join(folder_path, path_cfg['done_path'])
    uploaded_path = os.path.join(folder_path, path_cfg['uploaded_path'])

    if not os.path.exists(done_path):
        return

    uploaded_data = {}
    if os.path.exists(uploaded_path):
        with open(uploaded_path, 'r') as file:
            uploaded_data = json.load(file)

    with open(done_path, 'r') as file:
        processed_data = json.load(file)

    wait_upload_data = {}
    upload_total = 0
    for user_id, value in processed_data.items():
        processed_req = set(value.keys())
        uploaded_req = set(uploaded_data.keys())
        wait_upload_req = processed_req - uploaded_req

        upload_total += len(wait_upload_req)
        for req in wait_upload_req:
            logger.debug(value[req])
            if req in wait_upload_data:
                logger.error(f"Duplicate req: {req}")
            wait_upload_data[req] = {
                'datas': value[req],
                'user_id': user_id
            }
        # 累积上传数据量，达到UPLOAD_ONCE条上传一次
        if upload_total >= UPLOAD_ONCE:
            if upload_data(wait_upload_data):
                uploaded_data.update(wait_upload_data)
                update_uploaded(uploaded_path, uploaded_data)
            wait_upload_data = {}
            upload_total = 0

    if wait_upload_data:
        if upload_data(wait_upload_data):
            uploaded_data.update(wait_upload_data)
            update_uploaded(uploaded_path, uploaded_data)


logger.info("Running upload_data.py")
while not DEBUG:
    try:
        run()
        logger.info(f"Wait {UPLOAD_WAIT} seconds")
        time.sleep(UPLOAD_WAIT)  # 休眠
    except Exception as e:
        logger.error(f"Error: {e}")
        time.sleep(UPLOAD_WAIT)  # 出错时也休眠

if DEBUG:
    logger.info("Running on debug mode. 该模式下Logger不会输入文件中该模式下Logger不会输入文件中，并且只会执行一次")
    run()
