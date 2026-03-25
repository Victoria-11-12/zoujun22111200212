import requests

url = 'http://127.0.0.1:5000/predict'
# 注意：这里的 features 列表长度和顺序必须与训练时 X 的特征数量一致
# 你可以从训练数据中取一行作为示例，或者先随意填几个数测试（但模型会报特征数量不匹配）
data = {"features": [1, 2, 3]}  # 暂时用3个，之后需要替换为真实特征值
response = requests.post(url, json=data)
print(response.status_code)
print(response.json())