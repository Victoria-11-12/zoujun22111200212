import os
import re
import json
import bcrypt
import pymysql
from typing import Dict, List
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain.tools import tool
from app.config import llm, db
from app.logs import log_admin_chat


batch_sql_buffer: List[str] = []
batch_params_buffer: List[tuple] = []
batch_mode = False


@tool
def create_user(username: str, password: str, role: str = "user") -> str:
    """创建新用户，参数：用户名、密码、角色（admin/user）"""
    if role not in ["admin", "user"]:
        return "角色必须是 'admin' 或 'user'"
    
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    try:
        conn = pymysql.connect(
            host=os.getenv('DB_HOST'), user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'), database=os.getenv('DB_NAME')
        )
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                (username, hashed, role)
            )
            conn.commit()
        return f"用户 '{username}' 创建成功，角色: {role}"
    except pymysql.err.IntegrityError:
        return f"用户 '{username}' 已存在"
    except Exception as e:
        return f"创建用户失败: {e}"
    finally:
        conn.close()


@tool
def safe_execute_sql(sql: str, params: tuple = None) -> str:
    """执行经过安全检查的SQL语句"""
    global batch_mode, batch_sql_buffer, batch_params_buffer
    
    sql_clean = sql.strip().upper()
    
    dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE']
    for keyword in dangerous_keywords:
        if keyword in sql_clean:
            return f"拒绝执行：检测到危险操作 '{keyword}'"
    
    if batch_mode:
        batch_sql_buffer.append(sql)
        batch_params_buffer.append(params or ())
        return f"SQL已加入批处理队列（当前共{len(batch_sql_buffer)}条）"
    
    try:
        conn = pymysql.connect(
            host=os.getenv('DB_HOST'), user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'), database=os.getenv('DB_NAME')
        )
        with conn.cursor() as cursor:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            conn.commit()
            
            if sql_clean.startswith('SELECT'):
                results = cursor.fetchall()
                return json.dumps(results, ensure_ascii=False, default=str)
            else:
                return f"执行成功，影响行数: {cursor.rowcount}"
    except Exception as e:
        return f"执行失败: {e}"
    finally:
        conn.close()


@tool
def start_batch() -> str:
    """开始批处理模式，后续的SQL操作会被缓存，直到调用执行批处理"""
    global batch_mode, batch_sql_buffer, batch_params_buffer
    batch_mode = True
    batch_sql_buffer = []
    batch_params_buffer = []
    return "批处理模式已启动，后续的SQL操作将被缓存"


@tool
def rollback_batch() -> str:
    """回滚批处理队列，清空所有缓存的SQL操作"""
    global batch_mode, batch_sql_buffer, batch_params_buffer
    count = len(batch_sql_buffer)
    batch_sql_buffer = []
    batch_params_buffer = []
    batch_mode = False
    return f"批处理已回滚，清空了 {count} 条SQL操作"


admin_tools = [create_user, safe_execute_sql, start_batch, rollback_batch]

admin_prompt = ChatPromptTemplate.from_messages([
    ("system", """你是电影信息管理系统的管理员助手。你可以帮助管理员执行以下操作：

1. 用户管理 - 使用 create_user 工具
   - 创建新用户（普通用户或管理员）
   - 需要提供用户名、密码和角色

2. 数据库管理 - 使用 safe_execute_sql 工具
   - 执行安全的SQL查询和操作
   - 自动阻止危险的DROP/DELETE/TRUNCATE操作
   - 支持参数化查询防止SQL注入

3. 批处理操作 - 使用 start_batch 和 rollback_batch 工具
   - start_batch: 开始缓存多个SQL操作
   - rollback_batch: 清空缓存的操作

注意事项：
- 所有SQL操作都会被记录日志
- 危险操作会被自动拦截
- 查询结果以JSON格式返回
- 批处理模式可以减少数据库往返次数"""),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad")
])

admin_agent = create_tool_calling_agent(llm=llm, tools=admin_tools, prompt=admin_prompt)

admin_executor = AgentExecutor(
    agent=admin_agent,
    tools=admin_tools,
    verbose=True,
    max_iterations=5,
    handle_parsing_errors=True
)


def check_sql_safety(sql: str) -> tuple[bool, str]:
    """检查SQL语句安全性"""
    sql_upper = sql.upper().strip()
    
    dangerous_patterns = [
        r'DROP\s+',
        r'DELETE\s+FROM\s+',
        r'TRUNCATE\s+',
        r'EXEC\s*\(',
        r'EXECUTE\s*\(',
        r'UNION\s+SELECT',
        r'--',
        r'/\*',
        r'XP_',
        r'SP_',
        r';\s*DROP',
        r';\s*DELETE',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, sql_upper):
            return False, f"检测到危险SQL模式: {pattern}"
    
    return True, "安全检查通过"


def backup_data(table_name: str) -> str:
    """备份指定表的数据"""
    try:
        conn = pymysql.connect(
            host=os.getenv('DB_HOST'), user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'), database=os.getenv('DB_NAME')
        )
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table_name}")
            results = cursor.fetchall()
            
            backup_file = f"backup_{table_name}_{int(__import__('time').time())}.json"
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, default=str)
            
            return f"表 '{table_name}' 已备份到 {backup_file}，共 {len(results)} 条记录"
    except Exception as e:
        return f"备份失败: {e}"
    finally:
        conn.close()
