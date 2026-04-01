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
    lgb_model = joblib.load('lightgbm_model.pkl')
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
    """准备 LightGBM 模型输入特征"""
    df = df.copy()
    
    # 基础数值特征
    numeric_cols = ['budget', 'director_facebook_likes', 'actor_1_facebook_likes',
                    'actor_2_facebook_likes', 'actor_3_facebook_likes', 'movie_facebook_likes',
                    'num_voted_users', 'num_user_for_reviews', 'imdb_score',
                    'duration', 'title_year', 'facenumber_in_poster']
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col] = df[col].fillna(0)
    
    # log_budget
    df['log_budget'] = np.log1p(df['budget'].fillna(0))
    
    # country_freq, language_freq
    for col in ['country', 'language']:
        if col in df.columns:
            freq_map = df[col].value_counts().to_dict()
            df[col + '_freq'] = df[col].map(freq_map).fillna(0)
        else:
            df[col + '_freq'] = 0
    
    # genres 多标签编码
    if 'genres' in df.columns:
        df['genres_list'] = df['genres'].astype(str).str.split('|')
        all_genres = set()
        for genres in df['genres_list']:
            all_genres.update(genres)
        for genre in all_genres:
            df[genre] = df['genres_list'].apply(lambda x: 1 if genre in x else 0)
    
    # content_rating one-hot
    if 'content_rating' in df.columns:
        df['content_rating'] = df['content_rating'].fillna('Unknown')
        content_dummies = pd.get_dummies(df['content_rating'], prefix='content_rating')
        df = pd.concat([df, content_dummies], axis=1)
    
    # 类别特征编码
    categorical_cols = ['director_name', 'actor_1_name', 'actor_2_name', 'actor_3_name']
    for col in categorical_cols:
        if col in df.columns:
            df[col] = df[col].fillna('unknown')
            if col not in label_encoders:
                label_encoders[col] = LabelEncoder()
                df[col + '_cat'] = label_encoders[col].fit_transform(df[col])
            else:
                df[col + '_cat'] = df[col].map(lambda x: label_encoders[col].transform([x])[0] if x in label_encoders[col].classes_ else -1)
        else:
            df[col + '_cat'] = 0
    
    return df

@app.route('/api/flask/dark_horses', methods=['GET'])
def get_dark_horses():
    try:
        # 检查缓存是否有效
        current_time = time.time()
        if (dark_horses_cache['data'] is not None and 
            current_time - dark_horses_cache['timestamp'] < dark_horses_cache['expire_seconds']):
            print("返回缓存数据")
            return jsonify({"code": 200, "data": dark_horses_cache['data']})
        
        print("重新计算预测...")
        response = requests.get(f"{NODE_API_URL}/movies")
        movies = response.json()
        df = pd.DataFrame(movies)
        
        if df.empty:
            return jsonify({"code": 200, "data": []})
        
        # 数据清洗
        df['budget'] = pd.to_numeric(df['budget'], errors='coerce')
        df['imdb_score'] = pd.to_numeric(df['imdb_score'], errors='coerce')
        df['num_voted_users'] = pd.to_numeric(df['num_voted_users'], errors='coerce')
        df = df.dropna(subset=['budget', 'imdb_score', 'num_voted_users'])
        df = df[df['budget'] > 0]
        
        if df.empty:
            return jsonify({"code": 200, "data": []})
        
        # 准备特征
        df = prepare_features(df)
        
        # 获取模型特征名
        feature_names = lgb_model.booster_.feature_name()
        
        # 确保所有特征存在
        for col in feature_names:
            if col not in df.columns:
                df[col] = 0
        
        # LightGBM 预测
        X = df[feature_names]
        predictions = lgb_model.predict(X)
        df['predicted_gross'] = np.expm1(predictions)
        df['predicted_roi'] = df['predicted_gross'] / df['budget']
        
        # 按ROI排序返回前30条
        dark_horses = df.sort_values('predicted_roi', ascending=False).head(30)
        
        result = dark_horses[['movie_title', 'director_name', 'actor_1_name', 
                              'budget', 'predicted_gross', 'predicted_roi', 
                              'imdb_score', 'genres']].to_dict('records')
        
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
        predicted = rf_model.predict(input_data)[0]
        print("模型预测的原始值:", predicted)
        
        return jsonify({"code": 200, "predicted_gross": float(predicted)})
    except Exception as e:
        print("预测接口异常:", str(e))
        return jsonify({"code": 500, "msg": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
