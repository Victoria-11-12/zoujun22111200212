from flask import Flask, jsonify, request
from flask_cors import CORS
import joblib
import pandas as pd
import numpy as np
import requests
from sklearn.preprocessing import LabelEncoder
import time

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# 1. 加载模型
try:
    lgb_model = joblib.load('lightgbm_model_1.pkl')
    rf_model = joblib.load('random_forest_model.pkl')
    print("模型加载成功！")
    print(f"随机森林模型期望特征数: {rf_model.n_features_in_}")
except Exception as e:
    print(f"模型加载失败，请检查文件路径: {e}")

NODE_API_URL = "http://127.0.0.1:3000/api"

# LabelEncoder 缓存
label_encoders = {}

# 黑马预测结果缓存
dark_horses_cache = {
    'data': None,
    'timestamp': 0,
    'expire_seconds': 300  # 5分钟过期
}

def prepare_features(df):
    df = df.copy()
    
    # 1. genres（保持原样）
    if 'genres' not in df.columns:
        df['genres'] = 'unknown'
    else:
        df['genres'] = df['genres'].fillna('unknown')
    
    # 2. New_Director 判断
    if 'director_facebook_likes' in df.columns:
        df['New_Director'] = df['director_facebook_likes'].apply(
            lambda x: 'No' if pd.isna(x) or float(x) == 0 else 'Yes'
        )
    else:
        df['New_Director'] = 'No'
    
    # 3. New_Actor 判断
    if 'actor_1_facebook_likes' in df.columns:
        df['New_Actor'] = df['actor_1_facebook_likes'].apply(
            lambda x: 'No' if pd.isna(x) or float(x) == 0 else 'Yes'
        )
    else:
        df['New_Actor'] = 'No'
    
    # 4. budget（确保数值型）
    if 'budget' in df.columns:
        df['budget'] = pd.to_numeric(df['budget'], errors='coerce').fillna(1000)
    else:
        df['budget'] = 1000
    
    # 返回所需特征
    return df[['genres', 'New_Director', 'New_Actor', 'budget']]

@app.route('/api/flask/dark_horses', methods=['GET'])
def get_dark_horses():
    try:
        # 检查缓存是否有效
        current_time = time.time()
        if (dark_horses_cache['data'] is not None and 
            current_time - dark_horses_cache['timestamp'] < dark_horses_cache['expire_seconds']):
            return jsonify({"code": 200, "data": dark_horses_cache['data']})
        
        response = requests.get(f"{NODE_API_URL}/movies")
        movies = response.json()
        df = pd.DataFrame(movies)
        
        if df.empty:
            return jsonify({"code": 200, "data": []})
        
        # 数据清洗（过滤 budget 为空的记录）
        if 'budget' in df.columns:
            df['budget'] = pd.to_numeric(df['budget'], errors='coerce')
            df = df.dropna(subset=['budget'])
            df = df[df['budget'] > 0]
        else:
            return jsonify({"code": 200, "data": []})
        
        if df.empty:
            return jsonify({"code": 200, "data": []})
        
        # 准备特征（保留原始列用于结果展示）
        df_features = prepare_features(df.copy())
        
        # 手动类别特征编码（临时方案）
        cat_cols = ['genres', 'New_Director', 'New_Actor']
        for col in cat_cols:
            if col in df_features.columns:
                if col in ['New_Director', 'New_Actor']:
                    df_features[col] = df_features[col].apply(lambda x: 1 if str(x).strip().lower() == 'yes' else 0)
                else:
                    df_features[col] = df_features[col].apply(lambda x: hash(str(x)) % 2)
        
        # 使用新模型预测
        X = df_features[['genres', 'New_Director', 'New_Actor', 'budget']]
        predictions = lgb_model.predict(X)
        
        # 将预测结果添加回原始 DataFrame
        df['predicted_gross'] = predictions
        df['predicted_roi'] = df['predicted_gross'] / df['budget']
        
        # 按 ROI 排序返回前 30 条
        dark_horses = df.sort_values('predicted_roi', ascending=False).head(30)
        
        # 只返回 4 个核心字段 + 电影名
        result = dark_horses[['movie_title', 'budget', 'predicted_gross', 'predicted_roi', 'genres']].to_dict('records')
        
        # 更新缓存
        dark_horses_cache['data'] = result
        dark_horses_cache['timestamp'] = current_time
        
        return jsonify({"code": 200, "data": result})
    except Exception as e:
        print(f"黑马筛选报错：{e}")
        import traceback
        traceback.print_exc()
        return jsonify({"code": 500, "msg": str(e)})

@app.route('/api/flask/predict_deep', methods=['POST'])
def predict_deep():
    try:
        data = request.json
        print("接收到的数据:", data)
        
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
        predicted_log = rf_model.predict(input_data)[0]
        predicted = np.expm1(predicted_log)  # 对数转换回原始票房
        print("模型预测的对数值:", predicted_log)
        print("转换后的票房预测:", predicted)
        
        return jsonify({"code": 200, "predicted_gross": float(predicted)})
    except Exception as e:
        print("预测接口异常:", str(e))
        return jsonify({"code": 500, "msg": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
