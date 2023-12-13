# 脚本使用说明

## 依赖
1. setting.ini
    配置文件，用于配置脚本运行的参数

2. setting.py
    用于读取配置文件

3. run_script.py, run_script.sh
    用于运行脚本，任选其一即可

## 核心脚本
1. down_data.py
    用于轮询下载数据，并处理为json格式

2. core_process.py
    a) 处理数据，生成matlab需要的执行文件
    b) 调用matlab执行，获取结果文件中的数据
    c) 将结果数据写入json文件

3. upload_data.py
    上传数据到服务器

## 运行
1. 配置setting.ini文件
    可以参考原有setting.ini文件

2. 运行脚本
    ```shell
    python run_script.py
    ```
    或者
    ```shell
    sh run_script.sh
    ```

3. 守护进程
    可以将其添加入systemctl中，实现守护进程

## 简单说明
1. 之所以将脚本分为三个部分，是因为matlab的执行需要很长的时间，将其分开可以提高效率，避免下载和上传过程中等待matlab执行的时间。

2. 目前还没有写matlab的执行，需要在core_process.py中添加matlab的执行命令，以及处理matlab结果的代码。

3. 脚本有检查长时间未处理的数据的功能，很长时间未处理的数据会存在long_wait.json文件中，可以进行查阅。

4. 脚本提供检查执行Matlab结果的接口，需要的话可以自信添加。
