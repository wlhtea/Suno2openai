import requests

def stream_response(url, payload):
    # 发送POST请求，stream=True参数允许请求以流式方式接收响应
    response = requests.post(url, json=payload, stream=True)

    # 确保请求成功
    if response.status_code == 200:
        # 循环遍历响应内容
        for line in response.iter_lines():
            # 解码每一行数据
            if line:
                decoded_line = line.decode('utf-8')
                print(decoded_line)
    else:
        print("请求失败，状态码：", response.status_code)

# Flask应用的URL
url = "http://127.0.0.1:5000/v1/chat/completions"

# 根据您的Flask应用期望的数据调整payload
payload = {
    "model": "gpt-3.5-turbo",
    "messages":[
        {"role": "user", "content": "i like you song"}
    ],
    "stream":True
}

# 发送请求并处理响应
stream_response(url, payload)
