from flask import Flask, jsonify, request
from flask_cors import CORS
import joblib
import pandas as pd
import numpy as np
import requests

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# 1. 加载模型
try:
    lgb_model = joblib.load('lightgbm_model.pkl')
    rf_model = joblib.load('random_forest_model.pkl')
    print("模型加载成功！")
    print(f"随机森林模型期望特征数: {rf_model.n_features_in_}")
except Exception as e:
    print(f"模型加载失败，请检查文件路径: {e}")

NODE_API_URL = "http://127.0.0.1:3000/api"

@app.route('/api/flask/dark_horses', methods=['GET'])
def get_dark_horses():
    try:
        response = requests.get(f"{NODE_API_URL}/movies")
        movies = response.json()
        df = pd.DataFrame(movies)
        
        # 将关键列转换为数值类型，无法转换的设为 NaN
        df['imdb_score'] = pd.to_numeric(df['imdb_score'], errors='coerce')
        df['budget'] = pd.to_numeric(df['budget'], errors='coerce')
        
        # 删除包含 NaN 的行（也可以填充，但黑马需要完整数据）
        df = df.dropna(subset=['imdb_score', 'budget'])
        
        # 进行筛选
        dark_horses = df[(df['num_voted_users'] > 2*1e5) & (df['budget'] < 1e7)].to_dict('records')
        
        return jsonify({"code": 200, "data": dark_horses[:30]})
    except Exception as e:
        print(f"黑马筛选报错: {e}")
        return jsonify({"code": 500, "msg": str(e)})

@app.route('/api/flask/predict_deep', methods=['POST'])
def predict_deep():
    try:
        data = request.json
        # 打印接收到的原始数据
        print("接收到的数据:", data)
        
        # 严格按照模型特征顺序提取
        features = [
            float(data.get('budget', 0)),
            float(data.get('director_likes', 0)),
            float(data.get('actor1_likes', 0)),
            float(data.get('actor2_likes', 0)),
            float(data.get('actor3_likes', 0)),
            float(data.get('movie_likes', 0)),
            float(data.get('voted_users', 0)),
            float(data.get('review_count', 0)),
            float(data.get('imdb_score', 0))
        ]
        print("构造的特征列表:", features)
        
        input_data = np.array([features])
        predicted = rf_model.predict(input_data)[0]
        print("模型预测的原始值:", predicted)
        
        return jsonify({"code": 200, "predicted_gross": float(predicted)})
    except Exception as e:
        print("预测接口异常:", str(e))
        return jsonify({"code": 500, "msg": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)