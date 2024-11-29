import requests

url = "https://rootpath-file-download.bubbleapps.io/version-test/api/1.1/wf/post-sac-results"

data = {
    "gene_id": "1730864700615x737032770491923400",
    "sac_result": "test"
}

response = requests.post(url, json=data)

print("Status Code:", response.status_code)
print("Response Data:", response.json() if response.status_code == 200 else response.text)
