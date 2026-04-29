import os
import pymysql
from app.config import MODEL_NAME


def log_user_chat(session_id: str, role: str, content: str, intent: str = None, user_name: str = ""):
    try:
        conn = pymysql.connect(
            host=os.getenv('DB_HOST'), user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'), database=os.getenv('DB_NAME')
        )
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO user_chat_logs (session_id, user_name, role, content, intent, model_name) VALUES (%s, %s, %s, %s, %s, %s)",
                (session_id, user_name, role, content, intent, MODEL_NAME)
            )
            conn.commit()
    except Exception as e:
        print(f"用户日志记录失败: {e}")
    finally:
        conn.close()


def log_admin_chat(session_id: str, role: str, content: str, user_name: str = ""):
    try:
        conn = pymysql.connect(
            host=os.getenv('DB_HOST'), user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'), database=os.getenv('DB_NAME')
        )
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO admin_chat_logs (session_id, user_name, role, content, model_name) VALUES (%s, %s, %s, %s, %s)",
                (session_id, user_name, role, content, MODEL_NAME)
            )
            conn.commit()
    except Exception as e:
        print(f"管理员日志记录失败: {e}")
    finally:
        conn.close()


def log_chart_generation(session_id, user_name, question, sql_result, code, is_success, error_msg=""):
    try:
        conn = pymysql.connect(
            host=os.getenv('DB_HOST'), user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'), database=os.getenv('DB_NAME')
        )
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO chart_generation_logs (session_id, user_name, question, sql_result, generated_code, is_success, error_msg, model_name) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (session_id, user_name, question, sql_result, code, is_success, error_msg, MODEL_NAME)
            )
            conn.commit()
    except Exception as e:
        print(f"图表生成日志记录失败: {e}")
    finally:
        conn.close()


def log_security_warning(session_id, user_name, client_ip, role, content, warning_type):
    try:
        conn = pymysql.connect(
            host=os.getenv('DB_HOST'), user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'), database=os.getenv('DB_NAME')
        )
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO security_warning_logs (session_id, user_name, client_ip, role, content, warning_type, model_name) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (session_id, user_name, client_ip, role, content, warning_type, MODEL_NAME)
            )
            conn.commit()
    except Exception as e:
        print(f"安全警告日志记录失败: {e}")
    finally:
        conn.close()
