# SQL查询Agent
# 用于查询电影数据，支持本地数据库和百度百科搜索

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from app.config import llm
from app.tools.sql_tools import sql_db_query
from app.tools.web_tools import baike_search_tool


# 工具组装，将sql_db_query和baike_search_tool添加到user_toolkit中
user_toolkit = [sql_db_query, baike_search_tool]


# SQL Agent的提示词
SQL_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是一个专业的电影信息查询助手。你有两个工具可以使用：

1. sql_db_query - 查询本地数据库
   - 输入：完整的 SQL 查询语句
   - 用途：查询本地 movies 表中的电影数据

2. baike_search_tool - 从百度百科搜索电影信息
   - 输入：电影名称
   - 用途：当本地数据库没有找到电影信息时，从百度百科搜索

数据库表结构：
CREATE TABLE movies (
    id INT PRIMARY KEY AUTO_INCREMENT,
    movie_title VARCHAR(255),
    director_name VARCHAR(255),
    actor_1_name VARCHAR(255),
    actor_2_name VARCHAR(255),
    actor_3_name VARCHAR(255),
    genres VARCHAR(255),
    title_year INT,
    imdb_score DECIMAL(3,1),
    gross BIGINT,
    budget BIGINT,
    duration INT,
    language VARCHAR(100),
    country VARCHAR(100),
    content_rating VARCHAR(255)
);

工具使用规则：
1. 优先使用 sql_db_query 查询本地数据库
2. SQL查询规则：
   - 只使用 SELECT 语句，禁止修改操作
   - 禁止 SELECT *，必须明确列出字段名
   - 必须包含 WHERE 条件，禁止全表扫描
   - 查询结果必须包含 LIMIT，默认 LIMIT 20
   - movie_title 字段包含中文和英文电影名，查询中文电影时使用 LIKE '%关键词%'
3. 如果本地数据库查询结果为空或没有找到相关信息，再使用 baike_search_tool
4. 不要同时调用两个工具，按顺序使用
5. 只调用必要的工具，避免重复调用"""),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad")
])


# SQL Agent的组装
sql_agent = create_tool_calling_agent(llm=llm, tools=user_toolkit, prompt=SQL_PROMPT)


# 执行SQL Agent
sql_executor = AgentExecutor(
    agent=sql_agent,
    tools=user_toolkit,
    verbose=True,
    max_iterations=4,
    handle_parsing_errors=True
)
