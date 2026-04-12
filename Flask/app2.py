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
    lgb_model = joblib.load('lightgbm_model_1.pkl')
    rf_model = joblib.load('random_forest_model.pkl')
    print("模型加载成功！")
except Exception as e:
    print(f"模型加载失败，请检查文件路径: {e}")

NODE_API_URL = "http://127.0.0.1:3000/api"

label_encoders = {}

dark_horses_cache = {
    'data': None,
    'timestamp': 0,
    'expire_seconds': 300
}

def prepare_features(df):
    df = df.copy()
    if 'genres' not in df.columns:
        df['genres'] = 'unknown'
    else:
        df['genres'] = df['genres'].fillna('unknown')
    if 'director_facebook_likes' in df.columns:
        df['New_Director'] = df['director_facebook_likes'].apply(
            lambda x: 'No' if pd.isna(x) or float(x) == 0 else 'Yes'
        )
    else:
        df['New_Director'] = 'No'
    if 'actor_1_facebook_likes' in df.columns:
        df['New_Actor'] = df['actor_1_facebook_likes'].apply(
            lambda x: 'No' if pd.isna(x) or float(x) == 0 else 'Yes'
        )
    else:
        df['New_Actor'] = 'No'
    if 'budget' in df.columns:
        df['budget'] = pd.to_numeric(df['budget'], errors='coerce').fillna(1000)
    else:
        df['budget'] = 1000
    return df[['genres', 'New_Director', 'New_Actor', 'budget']]


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

        if 'budget' in df.columns:
            df['budget'] = pd.to_numeric(df['budget'], errors='coerce')
            df = df.dropna(subset=['budget'])
            df = df[df['budget'] > 0]
        else:
            return jsonify({"code": 200, "data": []})

        if df.empty:
            return jsonify({"code": 200, "data": []})

        df_features = prepare_features(df.copy())

        cat_cols = ['genres', 'New_Director', 'New_Actor']
        for col in cat_cols:
            if col in df_features.columns:
                if col in ['New_Director', 'New_Actor']:
                    df_features[col] = df_features[col].apply(lambda x: 1 if str(x).strip().lower() == 'yes' else 0)
                else:
                    df_features[col] = df_features[col].apply(lambda x: hash(str(x)) % 2)

        X = df_features[['genres', 'New_Director', 'New_Actor', 'budget']]
        predictions = lgb_model.predict(X)

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
        predicted = np.expm1(predicted_log)
        print("模型预测的对数值:", predicted_log)
        print("转换后的票房预测:", predicted)

        return jsonify({"code": 200, "predicted_gross": float(predicted)})
    except Exception as e:
        print("预测接口异常:", str(e))
        return jsonify({"code": 500, "msg": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
