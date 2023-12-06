import requests
import subprocess
import time
import logging

# 配置日志
logging.basicConfig(filename='script_log.txt', level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(message)s')


def send_request():
    # 发送HTTP请求到服务器
    url = "https://example.com/api"  # 替换为你的服务器地址
    response = requests.get(url)

    # 返回服务器响应的JSON内容
    return response.json()


def execute_matlab_program(data):
    # 执行Matlab程序
    matlab_script = "path/to/your/matlab_script.m"  # 替换为你的Matlab程序的路径

    for item in data:
        result = item['result']  # 从服务器返回的JSON中提取每条信息的结果
        command = f"matlab -nodisplay -nosplash -r 'run(\"{matlab_script}\", \"{result}\");exit;'"

        # 使用subprocess执行Matlab程序
        subprocess.run(command, shell=True)


def send_results_to_server(results):
    # 将结果分批提交回服务器，这里使用POST请求
    post_url = "https://example.com/post_results"  # 替换为你的服务器提交结果的地址
    payload = {'results': results}

    response = requests.post(post_url, json=payload)

    if response.status_code == 200:
        logging.info("Results submitted successfully.")
    else:
        logging.error(f"Error submitting results. Status code: {response.status_code}")


if __name__ == "__main__":
    while True:
        try:
            # 发送请求并获取结果
            response_data = send_request()

            # 处理多条信息并执行Matlab程序
            execute_matlab_program(response_data['data'])

            logging.info("Matlab execution successful.")

            # 提取结果，准备提交回服务器
            results_to_submit = [item['result'] for item in response_data['data']]

            # 将结果分批提交回服务器
            send_results_to_server(results_to_submit)

            logging.info("Results submitted successfully.")

        except Exception as e:
            logging.error(f"Error: {e}")

        # 每隔10分钟执行一次
        time.sleep(600)  # 600秒 = 10分钟
