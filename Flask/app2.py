import os
import joblib
import pandas as pd
import numpy as np
import time
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import pymysql
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ============================================================
# 一、数据库连接配置
# ============================================================

# 数据库连接参数从环境变量读取
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER_READONLY', os.getenv('DB_USER', ''))
DB_PASS = os.getenv('DB_PASS_READONLY', os.getenv('DB_PASS', ''))
DB_NAME = os.getenv('DB_NAME', '')

# 创建数据库连接函数
def get_db_connection():
    """
    获取MySQL数据库连接
    
    Returns:
        pymysql.connections.Connection: 数据库连接对象
    """
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor  # 返回字典形式的结果
    )

# 获取所有电影数据
def get_movies_from_db():
    """
    从数据库获取所有电影数据
    
    Returns:
        list: 电影数据列表，每个元素为字典
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 查询movies表所有数据
            sql = "SELECT * FROM movies"
            cursor.execute(sql)
            result = cursor.fetchall()
            return result
    finally:
        conn.close()

# ============================================================
# 二、机器学习模块
# ============================================================

# 加载随机森林模型
try:
    rf_model = joblib.load('random_forest_model.pkl')
    print("随机森林模型加载成功！")
except Exception as e:
    print(f"随机森林模型加载失败: {e}")
    rf_model = None

# 加载LightGBM模型
try:
    lgb_model = joblib.load('lightgbm_model_1.pkl')
    print("LightGBM模型加载成功！")
except Exception as e:
    print(f"LightGBM模型加载失败: {e}")
    lgb_model = None

label_encoders = {}

# 黑马数据缓存配置
dark_horses_cache = {
    'data': None,
    'timestamp': 0,
    'expire_seconds': 300
}

def prepare_features(df):
    """
    准备模型输入特征
    
    Args:
        df (DataFrame): 原始数据DataFrame
        
    Returns:
        DataFrame: 处理后的特征DataFrame
    """
    df = df.copy()
    # 定义需要的特征列
    feature_columns = [
        'budget', 'director_facebook_likes', 'actor_1_facebook_likes',
        'actor_2_facebook_likes', 'actor_2_facebook_likes', 'movie_facebook_likes',
        'num_voted_users', 'num_user_for_reviews', 'imdb_score'
    ]
    # 遍历特征列，转换为数值类型并填充缺失值
    for col in feature_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        else:
            df[col] = 0
    return df[feature_columns]

# ============================================================
# 三、API接口
# ============================================================

# 随机森林模型预测接口 - 黑马电影筛选
@app.route('/api/flask/dark_horses', methods=['GET'])
def get_dark_horses():
    """
    获取黑马电影列表（预测ROI最高的电影）
    
    Returns:
        jsonify: 包含黑马电影列表的JSON响应
    """
    try:
        current_time = time.time()
        # 检查缓存是否有效
        if (dark_horses_cache['data'] is not None and
            current_time - dark_horses_cache['timestamp'] < dark_horses_cache['expire_seconds']):
            return jsonify({"code": 200, "data": dark_horses_cache['data']})

        # 从数据库获取电影数据
        movies = get_movies_from_db()
        df = pd.DataFrame(movies)

        if df.empty:
            return jsonify({"code": 200, "data": []})

        # 定义模型需要的特征列
        required_features = [
            'budget', 'director_facebook_likes', 'actor_1_facebook_likes',
            'actor_2_facebook_likes', 'movie_facebook_likes',
            'num_voted_users', 'num_user_for_reviews', 'imdb_score'
        ]
        
        # 将特征列转换为数值类型
        for col in required_features:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 删除特征缺失的行
        df = df.dropna(subset=required_features)
        # 过滤预算小于等于0的数据
        df = df[df['budget'] > 0]

        if df.empty:
            return jsonify({"code": 200, "data": []})

        # 准备特征数据
        df_features = prepare_features(df.copy())

        # 使用随机森林模型预测票房（对数尺度）
        predictions_log = rf_model.predict(df_features)
        # 将对数预测值转换回原始尺度
        predictions = np.expm1(predictions_log)

        # 计算预测票房和ROI
        df['predicted_gross'] = predictions
        df['predicted_roi'] = df['predicted_gross'] / df['budget']

        # 按预测ROI排序，取前30名
        dark_horses = df.sort_values('predicted_roi', ascending=False).head(30)
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

# LightGBM模型预测接口 - 深度预测
@app.route('/api/flask/predict_deep', methods=['POST'])
def predict_deep():
    """
    使用LightGBM模型预测电影票房
    
    Returns:
        jsonify: 包含预测票房的JSON响应
    """
    try:
        # 检查模型是否加载成功
        if lgb_model is None:
            return jsonify({"code": 500, "msg": "LightGBM模型未加载"})
        
        # 获取请求数据
        data = request.json
        print("接收到的数据:", data)
        
        # 提取输入参数
        budget = float(data.get('budget', 0))
        genres = data.get('genres', '')
        new_director = data.get('New_Director', 'No')
        new_actor = data.get('New_Actor', 'No')
        
        # 构建输入DataFrame
        input_df = pd.DataFrame({
            'genres': [genres],
            'New_Director': [new_director],
            'New_Actor': [new_actor],
            'budget': [budget]
        })
        
        print("构造的DataFrame:", input_df)
        
        # 对分类变量进行编码
        cat_cols = ['genres', 'New_Director', 'New_Actor']
        for col in cat_cols:
            input_df[col] = pd.factorize(input_df[col])[0]
        
        print("编码后的DataFrame:", input_df)
        
        # 执行预测
        predicted = lgb_model.predict(input_df)[0]
        print("预测票房:", predicted)
        
        return jsonify({"code": 200, "predicted_gross": float(predicted)})
    except Exception as e:
        print("预测接口异常:", str(e))
        import traceback
        traceback.print_exc()
        return jsonify({"code": 500, "msg": str(e)})

# 随机森林模型 - ROI对比接口
@app.route('/api/flask/roi_comparison', methods=['GET'])
def get_roi_comparison():
    """
    获取实际ROI与预测ROI对比数据（随机森林模型）
    
    Returns:
        jsonify: 包含ROI对比数据的JSON响应
    """
    try:
        # 从数据库获取电影数据
        movies = get_movies_from_db()
        df = pd.DataFrame(movies)
        
        if df.empty:
            return jsonify({"code": 200, "data": []})
        
        print(f"原始数据量：{len(df)}")
        
        # 转换预算和票房为数值类型
        if 'budget' in df.columns:
            df['budget'] = pd.to_numeric(df['budget'], errors='coerce')
        if 'gross' in df.columns:
            df['gross'] = pd.to_numeric(df['gross'], errors='coerce')
        
        # 删除预算或票房缺失的数据
        df = df.dropna(subset=['budget', 'gross'])
        # 过滤预算和票房小于等于0的数据
        df = df[(df['budget'] > 0) & (df['gross'] > 0)]
        
        print(f"过滤预算和票房后的数据量：{len(df)}")
        
        if df.empty:
            return jsonify({"code": 200, "data": []})
        
        # 计算实际ROI
        df['actual_roi'] = df['gross'] / df['budget']
        
        # 准备特征并进行预测
        df_features = prepare_features(df.copy())
        predictions_log = rf_model.predict(df_features)
        predictions = np.expm1(predictions_log)
        
        # 计算预测ROI
        df['predicted_roi'] = predictions / df['budget']
        
        # 过滤实际ROI小于等于0的数据
        df = df[df['actual_roi'] > 0]
        
        # 过滤异常值（ROI > 6视为异常）
        df_before_outlier = len(df)
        df = df[df['actual_roi'] <= 6]
        df = df[df['predicted_roi'] <= 6]
        
        print(f"过滤异常值前的数据量：{df_before_outlier}")
        print(f"过滤异常值后的数据量：{len(df)} (移除了 {df_before_outlier - len(df)} 条极端异常值)")
        print(f"最终 ROI 对比数据量：{len(df)}")
        
        # 转换为字典列表返回
        result = df[['movie_title', 'actual_roi', 'predicted_roi']].to_dict('records')
        
        return jsonify({"code": 200, "data": result})
    except Exception as e:
        print(f"ROI对比接口异常：{e}")
        import traceback
        traceback.print_exc()
        return jsonify({"code": 500, "msg": str(e)})

# LightGBM模型 - 票房对比接口
@app.route('/api/flask/gross_comparison', methods=['GET'])
def get_gross_comparison():
    """
    获取实际票房与预测票房对比数据（LightGBM模型）
    
    Returns:
        jsonify: 包含票房对比数据的JSON响应
    """
    try:
        # 检查模型是否加载成功
        if lgb_model is None:
            return jsonify({"code": 500, "msg": "LightGBM模型未加载"})
        
        # 从数据库获取电影数据
        movies = get_movies_from_db()
        df = pd.DataFrame(movies)
        
        if df.empty:
            return jsonify({"code": 200, "data": []})
        
        print(f"票房对比(LightGBM) - 原始数据量：{len(df)}")
        
        # 处理必需列
        required_cols = ['budget', 'gross', 'genres']
        for col in required_cols:
            if col in df.columns:
                if col == 'genres':
                    # 处理genres列，取第一个类型
                    df[col] = df[col].astype(str).apply(lambda x: x.split('|')[0] if '|' in x else x)
                else:
                    # 转换为数值类型
                    df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 删除缺失数据
        df = df.dropna(subset=['budget', 'gross', 'genres'])
        # 过滤预算和票房小于等于0的数据
        df = df[(df['budget'] > 0) & (df['gross'] > 0)]
        
        print(f"票房对比(LightGBM) - 过滤后数据量：{len(df)}")
        
        if df.empty:
            return jsonify({"code": 200, "data": []})
        
        # 判断是否为新导演（只执导过一部电影）
        if 'director_name' in df.columns:
            director_counts = df['director_name'].value_counts()
            df['New_Director'] = df['director_name'].apply(lambda x: 'Yes' if director_counts.get(x, 0) == 1 else 'No')
        else:
            df['New_Director'] = 'No'
        
        # 判断是否为新演员（只出演过一部电影）
        if 'actor_1_name' in df.columns:
            actor_counts = df['actor_1_name'].value_counts()
            df['New_Actor'] = df['actor_1_name'].apply(lambda x: 'Yes' if actor_counts.get(x, 0) == 1 else 'No')
        else:
            df['New_Actor'] = 'No'
        
        # 准备模型输入数据
        input_df = df[['genres', 'New_Director', 'New_Actor', 'budget']].copy()
        
        # 对分类变量进行编码
        cat_cols = ['genres', 'New_Director', 'New_Actor']
        for col in cat_cols:
            input_df[col] = pd.factorize(input_df[col].astype(str))[0]
        
        # 执行预测
        predictions = lgb_model.predict(input_df)
        
        df['predicted_gross'] = predictions
        
        # 过滤无效数据
        df = df[(df['gross'] > 0) & (df['predicted_gross'] > 0)]
        
        # 限制预测票房不超过实际最大票房的两倍
        max_gross = df['gross'].max()
        df = df[df['predicted_gross'] <= max_gross * 2]
        
        print(f"票房对比(LightGBM) - 最终数据量：{len(df)}")
        
        # 转换为字典列表返回
        result = df[['movie_title', 'gross', 'predicted_gross']].to_dict('records')
        
        return jsonify({"code": 200, "data": result})
    except Exception as e:
        print(f"票房对比接口异常：{e}")
        import traceback
        traceback.print_exc()
        return jsonify({"code": 500, "msg": str(e)})

# ============================================================
# 四、主程序入口
# ============================================================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
