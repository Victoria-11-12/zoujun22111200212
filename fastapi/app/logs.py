import os
import pymysql
from contextlib import contextmanager
from app.config import MODEL_NAME


# 公共数据库连接工具
# 使用contextmanager自动管理连接的创建和关闭，避免重复代码
@contextmanager
def get_db_connection():
    """获取数据库连接的上下文管理器，自动处理连接关闭"""
    conn = pymysql.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASS'),
        database=os.getenv('DB_NAME')
    )
    try:
        yield conn
    finally:
        conn.close()


# 用户对话日志记录
# 参数为会话id，用户角色（user或者AI），消息内容，用户意图（需不需要SQL查询），用户姓名
def log_user_chat(session_id: str, role: str, content: str, intent: str = None, user_name: str = ""):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO user_chat_logs (session_id, user_name, role, content, intent, model_name) VALUES (%s, %s, %s, %s, %s, %s)",
                    (session_id, user_name, role, content, intent, MODEL_NAME)
                )
                conn.commit()
    except Exception as e:
        print(f"用户日志记录失败: {e}")


# 管理员对话日志记录
# 参数为会话id，用户角色（user或者AI，注意这里的role不是在系统中的权限，只是为了区分用户输入信息和AI回复信息），消息内容，管理员姓名
def log_admin_chat(session_id: str, role: str, content: str, user_name: str = ""):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO admin_chat_logs (session_id, user_name, role, content, model_name) VALUES (%s, %s, %s, %s, %s)",
                    (session_id, user_name, role, content, MODEL_NAME)
                )
                conn.commit()
    except Exception as e:
        print(f"管理员日志记录失败: {e}")


# 图表生成日志记录
# 参数为会话id，用户姓名，问题，SQL结果，生成的代码，是否成功，错误信息
def log_chart_generation(session_id, user_name, question, sql_result, code, is_success, error_msg=""):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO chart_generation_logs (session_id, user_name, question, sql_result, generated_code, is_success, error_msg, model_name) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                    (session_id, user_name, question, sql_result, code, is_success, error_msg, MODEL_NAME)
                )
                conn.commit()
    except Exception as e:
        print(f"图表生成日志记录失败: {e}")


# 安全警告日志记录
# 参数为会话id，用户姓名，客户端IP，用户角色（user或者AI），警告内容，警告类型（意图路由检测和系统警告回复）
def log_security_warning(session_id, user_name, client_ip, role, content, warning_type):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO security_warning_logs (session_id, user_name, client_ip, role, content, warning_type, model_name) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    (session_id, user_name, client_ip, role, content, warning_type, MODEL_NAME)
                )
                conn.commit()
    except Exception as e:
        print(f"安全警告日志记录失败: {e}")
