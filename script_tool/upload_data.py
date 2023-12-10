import os
import requests
import json
import time

def upload_data(data):
    # 上传数据到云服务器
    # 返回成功与否的状态

def update_upload_done(uploaded_data):
    # 更新 upload_done.json
    date_str = time.strftime("%Y-%m-%d", time.localtime())
    upload_done_path = f"/process/{date_str}/upload_done.json"

    uploaded_data_list = []
    if os.path.exists(upload_done_path):
        with open(upload_done_path, 'r') as file:
            uploaded_data_list = json.load(file)

    uploaded_data_list.extend(uploaded_data)

    with open(upload_done_path, 'w') as file:
        json.dump(uploaded_data_list, file)

# 主循环
while True:
    try:
        date_str = time.strftime("%Y-%m-%d", time.localtime())
        process_done_path = f"/process/{date_str}/process_done.json"

        if os.path.exists(process_done_path):
            with open(process_done_path, 'r') as file:
                processed_data = json.load(file)

            uploaded_data = []
            for data in processed_data:
                status = upload_data(data)
                if status:
                    uploaded_data.append(data)

            update_upload_done(uploaded_data)
        
        time.sleep(600)  # 休眠10分钟
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(600)  # 出错时也休眠10分钟
