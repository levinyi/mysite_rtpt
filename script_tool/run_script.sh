#!/bin/bash

# 启动三个进程，分别执行这三个文件
python down_data.py &
pid1=$!

python core_process.py &
pid2=$!

python upload.py &
pid3=$!

# 输出进程的 PID
echo "Process 1 PID: $pid1"
echo "Process 2 PID: $pid2"
echo "Process 3 PID: $pid3"
