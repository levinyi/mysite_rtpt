import requests
import json
import re

# API 的 URL，请根据实际情况修改
# url = "http://192.168.3.185:8000/user_center/api/generate-genbank/"
url = "https://www.rootpath.com.cn/user_center/api/generate-genbank/"

# 构造请求数据（与 API 文档中描述的 JSON 格式一致）
payload = {
    # "Plasmid_GZID": "pGZ1580(Amp)",  # rootpath 中的 Plasmid_GZID
    # "Plasmid_GZID": "pGZ1477(Kan)",  # rootpath 中的 Plasmid_Name
    "Plasmid_GZID": "pCVa061(Amp)",  # rootpath 中的 Plasmid_Name
    "features": [
        {"sequence": "ATGCGTAA", "name": "i5NC"},
        {"sequence": "ggggggggggggAAAAAAAAAAAAAAAAAAAAAAGGGGGGGGGaaaaaaaGGGGGGGGGCCCCCCCCCCCCCCCCCCTTTTTTTTTTTTTTT", "name": "gene03"},
        {"sequence": "TACCGGTA", "name": "i3NC"}
    ],
    "start_feature_label": "iU20",
    "end_feature_label": "iD20",
    "filename": "test.gb"
}

headers = {"Content-Type": "application/json"}

# 发送 POST 请求
response = requests.post(url, headers=headers, data=json.dumps(payload))

# 检查请求是否成功
if response.status_code == 200:
    print("请求成功！")

    # 解析 header 中的 X-GenBank-Sequence
    genbank_seq_header = response.headers.get("X-GenBank-Sequence")
    if genbank_seq_header:
        try:
            # header 中保存的是 JSON 格式的字符串
            plasmid_sequence = json.loads(genbank_seq_header)
            print("从 header 中解析到的 GenBank 序列：")
            print(plasmid_sequence)
        except Exception as e:
            print("解析 X-GenBank-Sequence header 时出错:", e)
    else:
        print("没有找到 X-GenBank-Sequence header。")

    # 解析返回的 GenBank 文件
    # 从 Content-Disposition header 中提取文件名（如果有）
    content_disposition = response.headers.get("Content-Disposition", "")
    filename_match = re.search(r'filename="([^"]+)"', content_disposition)
    if filename_match:
        output_filename = filename_match.group(1)
    else:
        output_filename = "downloaded.gb"

    # 将返回的文件保存到本地
    with open(output_filename, "wb") as f:
        f.write(response.content)
    print(f"GenBank 文件已保存为：{output_filename}")
else:
    print("请求失败，状态码：", response.status_code)
    print("返回内容：", response.text)
