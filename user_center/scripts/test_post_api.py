import requests

# 配置请求URL
url = 'http://192.168.3.185:8000/user_center/api/generate-genbank/'
url = 'https://www.rootpath.com.cn/user_center/api/generate-genbank/'

# 设置POST请求的数据
data = {
    'Plasmid_GZID': 'pGZ1455(Amp)',
    'NT_Sequence': 'ATGCGTACTGACTGAC',  # 核苷酸序列
    'start_feature_label': 'iU20',
    'end_feature_label': 'iD20',
    'new_feature_name': 'example_feature'
}

# 发送POST请求
response = requests.post(url, data=data)

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
