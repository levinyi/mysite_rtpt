import datetime
import os
import time
import requests
import json

def poll_cloud_api():
    # 调用云服务的API，获取未处理数据
    # 返回数据格式：[order_id:[{'gene_id':id,'name':xxxx, 'seq':xxx,'nc':xxx,...},{}],order_id:[{'gene_id':id,'name':xxxx, 'seq':xxx,'nc':xxx,...},{}]]
    # 使用 requests 库发送 HTTP 请求
    params={'token':'65f4c2c7143d4a1a90050f193859dc4b'}
    res = requests.get('http://127.0.0.1:8000/data_process/request_order',params=params)
    return res.json()

def save_data_to_file(file_path, data):
    # 将获取到的数据保存到文件
    with open(file_path, 'w') as file:
        json.dump(data, file)

def find_last_file_six_hours_ago(folder_path):
    # 找到六小时前的最后文件
    files = os.listdir(folder_path)
    # 将文件名转换为时间对象
    file_times = [datetime.strptime(file[:-5], "%H-%M") for file in files]
    current_time = datetime.now().replace(second=0, microsecond=0)

    six_hours_ago = current_time - datetime.timedelta(hours=6)
    recent_files = [file for file, time in zip(files, file_times) if six_hours_ago > time]
    # 按照时间排序
    if not recent_files:
        return None
    else:
        return sorted(recent_files, key=lambda x: file_times[files.index(x)])[-1]

def find_long_wait_data(folder_path, long_wait_path, new_data):
    # 找到长时间未处理的数据
    filepath = find_last_file_six_hours_ago(folder_path)
    if filepath is None:
        return None
    with open(filepath, 'r') as file:
        old_data = json.load(file)
    old_order_ids = set(old_data.keys())
    new_order_ids = set(new_data.keys())
    # 返回长时间未处理的订单号
    long_wait_order_ids = old_order_ids - new_order_ids
    # 添加到 long_wait.json

    if os.path.exists(long_wait_path):
        with open(long_wait_path, 'r') as file:
            long_wait_data = json.load(file)
        
        long_wait_data.update({order_id: old_data[order_id] for order_id in long_wait_order_ids})
        with open(long_wait_path, 'w') as file:
            json.dump(long_wait_data, file)


def check_long_wait_and_remove_duplicates(long_wait_path, new_data):
    # 检测长时间未处理的数据并移除重复项

    if os.path.exists(long_wait_path):
        with open(long_wait_path, 'r') as file:
            long_wait_data = json.load(file)
        
        for order_id in long_wait_data:
            if order_id not in new_data:
                long_wait_data.pop(order_id)

        with open(long_wait_path, 'w') as file:
            json.dump(long_wait_data, file)

# 主循环
while True:
    try:
        data = poll_cloud_api()

        date_str = time.strftime("%Y-%m-%d", time.localtime())
        time_str = time.strftime("%H-%M", time.localtime())
        folder_path = f"/process/{date_str}"
        long_wait_path = os.path.join(folder_path, "long_wait.json")
        pre_data_path = os.path.join(folder_path, "pre_data", f"{time_str}.json")

        if data:
            save_data_to_file(pre_data_path, data)
            find_long_wait_data(folder_path, long_wait_path, data)
            check_long_wait_and_remove_duplicates(long_wait_path, data)

        time.sleep(600)  # 休眠10分钟
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(600)  # 出错时也休眠10分钟
