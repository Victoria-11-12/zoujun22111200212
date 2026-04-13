import joblib
import pandas as pd
import numpy as np
import requests
import time
from flask import Flask, jsonify, request, Response
from flask_cors import CORS


app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ============================================================
# 一、原有机器学习模块（保持不变）
# ============================================================

try:
    rf_model = joblib.load('random_forest_model.pkl')
    print("随机森林模型加载成功！")
except Exception as e:
    print(f"随机森林模型加载失败: {e}")
    rf_model = None

try:
    lgb_model = joblib.load('lightgbm_model_1.pkl')
    print("LightGBM模型加载成功！")
except Exception as e:
    print(f"LightGBM模型加载失败: {e}")
    lgb_model = None

NODE_API_URL = "http://127.0.0.1:3000/api"

label_encoders = {}

dark_horses_cache = {
    'data': None,
    'timestamp': 0,
    'expire_seconds': 300
}

def prepare_features(df):
    df = df.copy()
    feature_columns = [
        'budget', 'director_facebook_likes', 'actor_1_facebook_likes',
        'actor_2_facebook_likes', 'actor_2_facebook_likes', 'movie_facebook_likes',
        'num_voted_users', 'num_user_for_reviews', 'imdb_score'
    ]
    for col in feature_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        else:
            df[col] = 0
    return df[feature_columns]


@app.route('/api/flask/dark_horses', methods=['GET'])
def get_dark_horses():
    try:
        current_time = time.time()
        if (dark_horses_cache['data'] is not None and
            current_time - dark_horses_cache['timestamp'] < dark_horses_cache['expire_seconds']):
            return jsonify({"code": 200, "data": dark_horses_cache['data']})

        response = requests.get(f"{NODE_API_URL}/movies")
        movies = response.json()
        df = pd.DataFrame(movies)

        if df.empty:
            return jsonify({"code": 200, "data": []})

        required_features = [
            'budget', 'director_facebook_likes', 'actor_1_facebook_likes',
            'actor_2_facebook_likes', 'movie_facebook_likes',
            'num_voted_users', 'num_user_for_reviews', 'imdb_score'
        ]
        
        for col in required_features:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df = df.dropna(subset=required_features)
        df = df[df['budget'] > 0]

        if df.empty:
            return jsonify({"code": 200, "data": []})

        df_features = prepare_features(df.copy())

        predictions_log = rf_model.predict(df_features)
        predictions = np.expm1(predictions_log)

        df['predicted_gross'] = predictions
        df['predicted_roi'] = df['predicted_gross'] / df['budget']

        dark_horses = df.sort_values('predicted_roi', ascending=False).head(30)
        result = dark_horses[['movie_title', 'budget', 'predicted_gross', 'predicted_roi', 'genres']].to_dict('records')

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
        if lgb_model is None:
            return jsonify({"code": 500, "msg": "LightGBM模型未加载"})
        
        data = request.json
        print("接收到的数据:", data)
        
        budget = float(data.get('budget', 0))
        genres = data.get('genres', '')
        new_director = data.get('New_Director', 'No')
        new_actor = data.get('New_Actor', 'No')
        
        input_df = pd.DataFrame({
            'genres': [genres],
            'New_Director': [new_director],
            'New_Actor': [new_actor],
            'budget': [budget]
        })
        
        print("构造的DataFrame:", input_df)
        
        cat_cols = ['genres', 'New_Director', 'New_Actor']
        for col in cat_cols:
            input_df[col] = pd.factorize(input_df[col])[0]
        
        print("编码后的DataFrame:", input_df)
        
        predicted = lgb_model.predict(input_df)[0]
        print("预测票房:", predicted)
        
        return jsonify({"code": 200, "predicted_gross": float(predicted)})
    except Exception as e:
        print("预测接口异常:", str(e))
        import traceback
        traceback.print_exc()
        return jsonify({"code": 500, "msg": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
