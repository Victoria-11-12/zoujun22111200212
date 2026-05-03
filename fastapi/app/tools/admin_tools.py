# 管理员工具集
# 包含创建用户、安全执行SQL、批次管理、回滚等工具

import os
import json
import re
import uuid
import bcrypt
import pymysql
from langchain.tools import tool
from app.config import engine
from app.logs import log_security_warning


# 危险关键词列表
DANGEROUS_KEYWORDS = [r'\bDROP\b', r'\bTRUNCATE\b', r'\bALTER\b', r'\bCREATE\b', r'\bGRANT\b', r'\bREVOKE\b', r'--', r';\s*\w']

# 全局变量：当前管理员名称和批次ID
_current_admin_name = ""
_current_batch_id = ""


# 正则检查函数，检查SQL语句是否包含危险词
def check_sql_safety(sql: str) -> tuple[bool, str]:
    # 转大写，去掉首尾空格
    sql_upper = sql.upper().strip()
    # 遍历正则匹配，包含危险词直接返回
    for pattern in DANGEROUS_KEYWORDS:
        if re.search(pattern, sql_upper):
            return False, f"包含禁止操作: {pattern}"
    return True, "通过"


# 数据备份函数
def backup_data(table_name: str, action: str, data: list):
    global _current_admin_name, _current_batch_id
    try:
        # 使用连接池获取连接
        conn = engine.raw_connection()
        # 执行SQL语句，将操作记录写入回滚日志表
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO rollback_logs (table_name, action, affected_data, username, batch_id) VALUES (%s,%s,%s,%s,%s)",
                (table_name, action, json.dumps(data, ensure_ascii=False, default=str), _current_admin_name, _current_batch_id)
            )
            conn.commit()
            print(f"[回滚备份] {action} {table_name}: 备份了 {len(data)} 条数据")
    except Exception as e:
        print(f"[回滚备份失败] {e}")
    finally:
        conn.close()


# 工具1：创建用户
@tool
def create_user(username: str, password: str, role: str = "user") -> str:
    """创建新用户，密码会自动加密，role 默认为 user，管理员可设置为 admin"""
    conn = engine.raw_connection()
    try:
        cursor = conn.cursor()
        # 检查用户是否存在
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return f"用户 {username} 已存在"
        # 密码加密，使用bcrypt进行安全哈希
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
            (username, hashed, role)
        )
        conn.commit()
        # 备份新插入的用户（回滚时需要删除）
        # 查询新插入的用户数据
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        # 获取列名
        columns = [desc[0] for desc in cursor.description]
        # 将查询结果转换为字典
        row = dict(zip(columns, cursor.fetchone()))
        # 调用函数备份数据
        backup_data("users", "INSERT", [row])
        return f"用户 {username} 创建成功，角色：{role}"
    except Exception as e:
        return f"创建用户失败: {str(e)}"
    finally:
        conn.close()


# 工具2：安全执行 SQL
@tool
def safe_execute_sql(query: str) -> str:
    """执行 SQL 操作。可以查询(SELECT)、修改(UPDATE)、删除(DELETE)数据。
    
    示例：
    - 查询：SELECT * FROM users WHERE role='user'
    - 修改：UPDATE users SET role='admin' WHERE username='test3'
    - 删除：DELETE FROM users WHERE username='test3'
    
    参数：query(要执行的SQL语句)"""

    # 调用正则检查函数，检查SQL语句是否包含危险词
    is_safe, reason = check_sql_safety(query)
    if not is_safe:
        return f"🚫 安全拦截：{reason}，该操作已被记录。"
    sql_upper = query.upper().strip()

    try:
        # 使用连接池获取连接
        conn = engine.raw_connection()
        # 创建游标
        with conn.cursor() as cursor:
            # DELETE/UPDATE 执行前备份数据
            if sql_upper.startswith('DELETE') or sql_upper.startswith('UPDATE'):
                # 正则FROM匹配DELETE表名，UPDATE匹配UPDATE表名，这边只是匹配对象，还没有提取
                table_match = re.search(r'FROM\s+(\w+)|UPDATE\s+(\w+)', sql_upper)
                # 正则匹配WHERE之后的内容
                where_match = re.search(r'WHERE\s+(.+)$', sql_upper)

                # 表名和条件都匹配成功才备份数据
                if table_match and where_match:

                    # 列表推导式过滤空值，取第一个非空值作为表名
                    table_name = [t for t in table_match.groups() if t][0]
                    # where只有一个捕获组，不需要过滤空值，直接取第一个捕获组内容
                    where_clause = where_match.group(1).strip()
                    # 根据操作类型判断备份操作是DELETE还是UPDATE
                    action = "DELETE" if sql_upper.startswith('DELETE') else "UPDATE"

                    # 查询要备份的数据
                    cursor.execute(f"SELECT * FROM {table_name} WHERE {where_clause}")
                    # 列表推导式拿到返回结果的列名
                    columns = [desc[0] for desc in cursor.description]
                    # cursor.fetchall()返回所有结果行,
                    # zip(columns, row)将列名和行数据对应起来，转换为字典
                    rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
                    if rows:
                        backup_data(table_name, action, rows)
            
            # 执行SQL语句
            cursor.execute(query)
            # 判断是否为查询操作
            if query.upper().strip().startswith('SELECT'):
                results = cursor.fetchall()  # 获取所有结果
                columns = [desc[0] for desc in cursor.description]  # 获取列名
                rows = [dict(zip(columns, row)) for row in results[:15]]  # 获取前15条数据
                if not rows:
                    return "查询结果为空"
                return f"查询到 {len(rows)} 条数据:\n" + "\n".join(" | ".join(str(v) for v in r.values()) for r in rows)
            else:
                conn.commit()  # 提交事务
                return f"操作成功，影响 {cursor.rowcount} 行。（已自动备份，可通过回滚功能恢复）"
    except Exception as e:
        return f"SQL 执行错误: {str(e)}"
    finally:
        conn.close()


# 工具3：开始批次
@tool
def start_batch() -> str:
    """开始一个操作批次。在执行数据库增删改操作之前调用，之后可以用 rollback_batch 一次性回滚整个批次。无需参数。"""
    global _current_batch_id
    _current_batch_id = str(uuid.uuid4())[:8]
    # 生成批次代码，global修改全局变量，让后续备份操作都共享这个批次号
    return f"已创建新批次 {_current_batch_id}，后续操作将归入此批次。"


# 工具4：回滚批次
@tool
def rollback_batch() -> str:
    """撤销一个批次的指定或所有操作。数据库增删改操作后使用此工具可以一次性回滚。无需参数。"""
    try:
        # 使用连接池获取连接
        conn = engine.raw_connection()
        # 创建游标
        with conn.cursor() as cursor:
            # 获取最近的批次ID
            # 这里只能取最近的一个批次id，跨批次回滚会报错，顺序错乱
            # 去掉DISTINCT，因为LIMIT 1已经只返回一条记录，避免与ORDER BY不兼容的错误
            cursor.execute("SELECT batch_id FROM rollback_logs ORDER BY id DESC LIMIT 1")
            batch_row = cursor.fetchone()
            if not batch_row:
                return "没有可回滚的操作记录"
            # 取第0个元素，返回的结果大概是（'1314sada',）的元组
            batch_id = batch_row[0]

            # 获取该批次所有记录，按 id 倒序（后执行的先回滚）
            # ORDER BY id DESC，倒序排列，后执行的操作先回滚，很重要，否则会先回滚先执行的操作，导致数据不一致
            # 获取的是一个批次的记录，不是整个表的记录，不依次操作一条记录会导致数据错乱
            cursor.execute("SELECT * FROM rollback_logs WHERE batch_id=%s ORDER BY id DESC", (batch_id,))
            records = cursor.fetchall()

            # 计算回滚数据的条数
            total_restored = 0

            # 取值
            for record in records:
                log_id = record[0]
                table_name = record[1]
                action = record[2]
                affected_data = record[3]
                rows = json.loads(affected_data)

                # 下面分三种情况处理
                # 删除操作重新插入
                if action == "DELETE":
                    columns = list(rows[0].keys())  # 获取列名
                    placeholders = ",".join(["%s"] * len(columns))  # 生成占位符，有几个列名生成几个
                    col_str = ",".join(columns)  # 生成列名字符串
                    for row in rows:
                        values = [row[c] for c in columns]  # 按列名顺序取值
                        cursor.execute(f"INSERT INTO {table_name} ({col_str}) VALUES ({placeholders})", values)
                    total_restored += len(rows)
                    # 删除示例：
                    # 假设数据rows = [
                    #     {'id': 3, 'name': '张三', 'age': 28},
                    #     {'id': 4, 'name': '李四', 'age': 32}
                    # ]
                    # columuns = ['id', 'name', 'age']
                    # placeholders = '%s, %s, %s'
                    # col_str = 'id, name, age'
                    # for row in rows:
                    #     values 会依次=[3,'张三', 28]
                    #     SQL语句传参并执行
                    # 计算操作数量

                # 修改操作，将除了id外的所有值恢复旧值
                # id是主键，用户可能有重名，但id不会重复
                elif action == "UPDATE":
                    for row in rows:
                        if 'id' in row:
                            set_parts = [f"{k}=%s" for k in row.keys() if k != 'id']  # 生成占位符，类似['name=%s', 'age=%s']
                            values = [row[k] for k in row.keys() if k != 'id']  # 从备份中取旧值，类似['张三', 32]
                            values.append(row['id'])  # 加入id，类似[3, '张三', 32]
                            cursor.execute(f"UPDATE {table_name} SET {','.join(set_parts)} WHERE id=%s", values)  # 执行SQL
                    total_restored += len(rows)

                # 插入操作，根据id或者username删除数据
                elif action == "INSERT":
                    for row in rows:
                        if 'id' in row:
                            cursor.execute(f"DELETE FROM {table_name} WHERE id=%s", (row['id'],))
                        elif 'username' in row:
                            cursor.execute(f"DELETE FROM {table_name} WHERE username=%s", (row['username'],))
                    total_restored += len(rows)

                # 删除操作，根据id删除在回滚日志表中的数据记录
                cursor.execute("DELETE FROM rollback_logs WHERE id=%s", (log_id,))

            conn.commit()
            return f"批次回滚成功：共恢复 {total_restored} 条数据（{len(records)} 个操作）"
    except Exception as e:
        return f"批次回滚失败: {str(e)}"
    finally:
        conn.close()


# 设置当前管理员名称（供外部调用）
def set_current_admin_name(name: str):
    """设置当前管理员名称"""
    global _current_admin_name
    _current_admin_name = name


# 管理员工具列表
admin_tools = [create_user, safe_execute_sql, rollback_batch, start_batch]
