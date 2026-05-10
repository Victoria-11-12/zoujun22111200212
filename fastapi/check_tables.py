import pymysql
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

conn = pymysql.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASS'),
    database=os.getenv('DB_NAME')
)

tables = ['user_chat_logs', 'admin_chat_logs', 'chart_generation_logs', 'security_warning_logs', 'eval_results']

with conn.cursor(pymysql.cursors.DictCursor) as cursor:
    for table in tables:
        print(f"\n========== {table} ==========")
        cursor.execute(f"DESCRIBE {table}")
        rows = cursor.fetchall()
        for row in rows:
            print(f"  {row['Field']:25s} {row['Type']:30s} Null={row['Null']:5s} Key={row['Key']:5s} Extra={row['Extra']:20s}")

conn.close()
