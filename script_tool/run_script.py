# 使用python启动进程
import os
import subprocess

# 定义三个要执行的文件路径
file_paths = ["./down_data.py", "./core_process.py", "./upload.py"]

# 启动三个进程，分别执行这三个文件
processes = []
for file_path in file_paths:
    process = subprocess.Popen(["python", file_path])
    processes.append(process)
    print(f"Process {len(processes)} PID: {process.pid}")

print("All processes running.")
