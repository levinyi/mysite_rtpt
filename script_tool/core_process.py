import os
import subprocess
import json
import time

def process_order(order_data):
    # 处理一个 order 的数据
    # 返回临时文件路径和输出文件路径
    # 实现你的处理逻辑，调用 MATLAB 程序等
    pass

def process_orders_in_file(file_path):
    # 处理文件中的所有订单数据
    with open(file_path, 'r') as file:
        data = json.load(file)

    temp_files = []
    for order_id, order_data in data.items():
        temp_file, output_file = process_order(order_data)
        temp_files.append(temp_file)

    return temp_files

def update_process_done(temp_files):
    # 更新 process_done.json
    date_str = time.strftime("%Y-%m-%d", time.localtime())
    process_done_path = f"/process/{date_str}/process_done.json"

    processed_data = []
    if os.path.exists(process_done_path):
        with open(process_done_path, 'r') as file:
            processed_data = json.load(file)

    for temp_file in temp_files:
        with open(temp_file, 'r') as file:
            processed_data.append(json.load(file))

    with open(process_done_path, 'w') as file:
        json.dump(processed_data, file)

def update_error_process(temp_files):
    # 更新 error_process.json
    date_str = time.strftime("%Y-%m-%d", time.localtime())
    error_process_path = f"/process/{date_str}/error_process.json"

    error_data = []
    if os.path.exists(error_process_path):
        with open(error_process_path, 'r') as file:
            error_data = json.load(file)

    for temp_file in temp_files:
        with open(temp_file, 'r') as file:
            error_data.append(json.load(file))

    with open(error_process_path, 'w') as file:
        json.dump(error_data, file)

# 主循环
while True:
    try:
        date_str = time.strftime("%Y-%m-%d", time.localtime())
        pre_data_path = f"/process/{date_str}/pre_data/"
        latest_file = sorted(os.listdir(pre_data_path))[-1]

        if latest_file not in ["error_process.json", "process_done.json"]:
            temp_files = process_orders_in_file(os.path.join(pre_data_path, latest_file))
            update_process_done(temp_files)
            update_error_process(temp_files)
        
        time.sleep(600)  # 休眠10分钟
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(600)  # 出错时也休眠10分钟
