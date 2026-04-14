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


@app.route('/api/flask/roi_comparison', methods=['GET'])
def get_roi_comparison():
    try:
        response = requests.get(f"{NODE_API_URL}/movies")
        movies = response.json()
        df = pd.DataFrame(movies)
        
        if df.empty:
            return jsonify({"code": 200, "data": []})
        
        print(f"原始数据量：{len(df)}")
        
        if 'budget' in df.columns:
            df['budget'] = pd.to_numeric(df['budget'], errors='coerce')
        if 'gross' in df.columns:
            df['gross'] = pd.to_numeric(df['gross'], errors='coerce')
        
        df = df.dropna(subset=['budget', 'gross'])
        df = df[(df['budget'] > 0) & (df['gross'] > 0)]
        
        print(f"过滤预算和票房后的数据量：{len(df)}")
        
        if df.empty:
            return jsonify({"code": 200, "data": []})
        
        df['actual_roi'] = df['gross'] / df['budget']
        
        df_features = prepare_features(df.copy())
        predictions_log = rf_model.predict(df_features)
        predictions = np.expm1(predictions_log)
        
        df['predicted_roi'] = predictions / df['budget']
        
        df = df[df['actual_roi'] > 0]
        
        df_before_outlier = len(df)
        df = df[df['actual_roi'] <= 6]
        df = df[df['predicted_roi'] <= 6]
        
        print(f"过滤异常值前的数据量：{df_before_outlier}")
        print(f"过滤异常值后的数据量：{len(df)} (移除了 {df_before_outlier - len(df)} 条极端异常值)")
        print(f"最终 ROI 对比数据量：{len(df)}")
        
        result = df[['movie_title', 'actual_roi', 'predicted_roi']].to_dict('records')
        
        return jsonify({"code": 200, "data": result})
    except Exception as e:
        print(f"ROI对比接口异常：{e}")
        import traceback
        traceback.print_exc()
        return jsonify({"code": 500, "msg": str(e)})


@app.route('/api/flask/gross_comparison', methods=['GET'])
def get_gross_comparison():
    try:
        if lgb_model is None:
            return jsonify({"code": 500, "msg": "LightGBM模型未加载"})
        
        response = requests.get(f"{NODE_API_URL}/movies")
        movies = response.json()
        df = pd.DataFrame(movies)
        
        if df.empty:
            return jsonify({"code": 200, "data": []})
        
        print(f"票房对比(LightGBM) - 原始数据量：{len(df)}")
        
        required_cols = ['budget', 'gross', 'genres']
        for col in required_cols:
            if col in df.columns:
                if col == 'genres':
                    df[col] = df[col].astype(str).apply(lambda x: x.split('|')[0] if '|' in x else x)
                else:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df = df.dropna(subset=['budget', 'gross', 'genres'])
        df = df[(df['budget'] > 0) & (df['gross'] > 0)]
        
        print(f"票房对比(LightGBM) - 过滤后数据量：{len(df)}")
        
        if df.empty:
            return jsonify({"code": 200, "data": []})
        
        if 'director_name' in df.columns:
            director_counts = df['director_name'].value_counts()
            df['New_Director'] = df['director_name'].apply(lambda x: 'Yes' if director_counts.get(x, 0) == 1 else 'No')
        else:
            df['New_Director'] = 'No'
        
        if 'actor_1_name' in df.columns:
            actor_counts = df['actor_1_name'].value_counts()
            df['New_Actor'] = df['actor_1_name'].apply(lambda x: 'Yes' if actor_counts.get(x, 0) == 1 else 'No')
        else:
            df['New_Actor'] = 'No'
        
        input_df = df[['genres', 'New_Director', 'New_Actor', 'budget']].copy()
        
        cat_cols = ['genres', 'New_Director', 'New_Actor']
        for col in cat_cols:
            input_df[col] = pd.factorize(input_df[col].astype(str))[0]
        
        predictions = lgb_model.predict(input_df)
        
        df['predicted_gross'] = predictions
        
        df = df[(df['gross'] > 0) & (df['predicted_gross'] > 0)]
        
        max_gross = df['gross'].max()
        df = df[df['predicted_gross'] <= max_gross * 2]
        
        print(f"票房对比(LightGBM) - 最终数据量：{len(df)}")
        
        result = df[['movie_title', 'gross', 'predicted_gross']].to_dict('records')
        
        return jsonify({"code": 200, "data": result})
    except Exception as e:
        print(f"票房对比接口异常：{e}")
        import traceback
        traceback.print_exc()
        return jsonify({"code": 500, "msg": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
