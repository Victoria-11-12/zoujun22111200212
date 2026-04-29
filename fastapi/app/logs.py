import os
import pymysql
from app.config import MODEL_NAME


#用户对话日志记录
#参数为会话id，用户角色（user或者AI），消息内容，用户意图（需不需要SQL查询），用户姓名
#这里详写一个函数，其余三个的逻辑和这个是一样的
def log_user_chat(session_id: str, role: str, content: str, intent: str = None, user_name: str = ""):
    try:
        #连接数据库
        conn = pymysql.connect(
            host=os.getenv('DB_HOST'), user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'), database=os.getenv('DB_NAME')
        )
        #conn.cursor()创建游标对象，用于执行SQL语句,with语句会自动关闭游标和连接
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO user_chat_logs (session_id, user_name, role, content, intent, model_name) VALUES (%s, %s, %s, %s, %s, %s)",
                (session_id, user_name, role, content, intent, MODEL_NAME)
            )
            #提交事务，将数据写入数据库
            conn.commit()
        #可以把这个过程想象成送信，游标是送信员，cursor.execute()是写信（SQL+数据），conn.commit()寄出信
    except Exception as e:
        print(f"用户日志记录失败: {e}")
    #关闭数据库连接，无论是否出错都要关闭，否则会占用数据库连接
    finally:
        conn.close()

#管理员对话日志记录
#参数为会话id，用户角色（user或者AI，注意这里的role不是在系统中的权限，只是为了区分用户输入信息和AI回复信息），消息内容，管理员姓名
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

#图表生成日志记录
#参数为会话id，用户姓名，问题，SQL结果，生成的代码，是否成功，错误信息
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

#安全警告日志记录
#参数为会话id，用户姓名，客户端IP，用户角色（user或者AI），警告内容，警告类型（意图路由检测和系统警告回复），
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
