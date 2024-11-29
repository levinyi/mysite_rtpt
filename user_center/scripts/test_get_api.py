import requests

# 配置请求URL
url = "https://rootpath-file-download.bubbleapps.io/version-test/api/1.1/wf/get-genes-by-sac-status"
url = "http://192.168.3.185:8000/user_center/condon_optimization_api"

params = {
   "status": "pending"
}
# 发送 GET 请求
try:
    response = requests.get(url, params=params)

    # 检查响应状态码
    if response.status_code == 200:
        # 请求成功，打印响应内容
        print("Response JSON:", response.json())
    else:
        # 请求失败，打印状态码和响应内容
        print(f"Request failed with status code {response.status_code}")
        print("Response Text:", response.text)
except requests.exceptions.RequestException as e:
    # 捕获请求异常并打印错误信息
    print(f"An error occurred: {e}")


'''
# 处理响应
if response.status_code == 200:
    # 保存下载的文件
    with open('downloaded_genbank_file.gb', 'wb') as file:
        file.write(response.content)
    print("GenBank file downloaded successfully.")
elif response.status_code == 404:
    try:
        error_message = response.json().get("error")
    except ValueError:
        error_message = response.text  # 处理非JSON响应
    print("Error: ", error_message)
else:
    try:
        print("Unexpected error:", response.status_code, response.json())
    except ValueError:
        print("Unexpected error:", response.status_code, response.text)

'''