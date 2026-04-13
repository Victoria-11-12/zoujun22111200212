# 数据分析师模块开发指南

## 一、数据库

### 1.1 新建评估结果表

```sql
CREATE TABLE eval_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source_table VARCHAR(50),
    source_id INT,
    eval_type VARCHAR(20),
    score INT,
    dimensions JSON,
    issues TEXT,
    verdict VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 1.2 新增分析师角色

在 users 表中插入分析师账号：

```sql
INSERT INTO users (username, password, role) VALUES ('analyst', '加密后的密码', 'analyst');
```

---

## 二、Node.js 改动

### 2.1 登录接口支持 analyst 角色

登录成功后，根据 role 返回不同页面：

| role | 跳转页面 |
|------|---------|
| user | index.html |
| admin | admin.html |
| analyst | analyst.html |

---

## 三、FastAPI（app3.py）新增路由

### 3.1 数据概览

```
GET /api/analyst/overview
```

用 pymysql 直接查 4 张表，返回以下数据：

```json
{
    "chat_trend": [
        {"date": "2026-04-01", "count": 45},
        {"date": "2026-04-02", "count": 52}
    ],
    "intent_distribution": [
        {"intent": "NEED_SQL", "count": 120},
        {"intent": "DIRECT_REPLY", "count": 80},
        {"intent": "WARNING", "count": 15}
    ],
    "chart_success_rate": {
        "success": 85,
        "fail": 15
    },
    "attack_distribution": [
        {"warning_type": "SQL注入", "count": 10},
        {"warning_type": "社会工程", "count": 5}
    ]
}
```

SQL 参考：

```sql
-- 对话量趋势
SELECT DATE(created_at) as date, COUNT(*) as count 
FROM user_chat_logs 
GROUP BY DATE(created_at) 
ORDER BY date DESC 
LIMIT 30;

-- 意图分布
SELECT intent, COUNT(*) as count 
FROM user_chat_logs 
GROUP BY intent;

-- 绘图成功率
SELECT is_success, COUNT(*) as count 
FROM chart_generation_logs 
GROUP BY is_success;

-- 攻击类型分布
SELECT warning_type, COUNT(*) as count 
FROM security_warning_logs 
GROUP BY warning_type;
```

### 3.2 触发质量评估

```
POST /api/analyst/evaluate
```

请求体：

```json
{
    "tables": ["user_chat_logs", "admin_chat_logs", "chart_generation_logs", "security_warning_logs"],
    "start_date": "2026-04-01",
    "end_date": "2026-04-13"
}
```

处理逻辑：

1. 根据筛选条件从 4 张表取数据
2. 对每条记录调 DeepSeek API 评分
3. 评分结果存入 eval_results 表
4. 返回评估任务 ID 和总记录数

**重要：评估是异步的，因为要调很多次 LLM。用后台线程执行，前端轮询进度。**

### 3.3 查询评估进度

```
GET /api/analyst/evaluate/status
```

返回：

```json
{
    "status": "running",
    "total": 200,
    "completed": 150,
    "progress": 75
}
```

实现方式：用全局变量记录进度，评估线程每处理一条就更新。

### 3.4 获取评估结果

```
GET /api/analyst/results?min_score=4&source_table=user_chat_logs
```

返回：

```json
{
    "score_distribution": [
        {"score": 5, "count": 80},
        {"score": 4, "count": 60},
        {"score": 3, "count": 30},
        {"score": 2, "count": 20},
        {"score": 1, "count": 10}
    ],
    "dimension_avg": {
        "相关性": 4.2,
        "完整性": 3.8,
        "准确性": 4.5,
        "格式": 4.0
    },
    "low_score_cases": [
        {
            "id": 1,
            "source_table": "user_chat_logs",
            "score": 2,
            "issues": "答非所问，回复内容与用户问题无关",
            "user_content": "查询2012年票房前十",
            "ai_content": "您好，请问有什么可以帮您的？"
        }
    ]
}
```

### 3.5 导出 JSONL

```
POST /api/analyst/export
```

请求体：

```json
{
    "min_score": 4,
    "tables": ["user_chat_logs", "admin_chat_logs"],
    "start_date": "2026-04-01",
    "end_date": "2026-04-13"
}
```

处理逻辑：

1. 从 eval_results 查出 score >= min_score 的记录
2. 根据 source_table 和 source_id 回查原始对话
3. 组装成 JSONL 格式
4. 返回文件流下载

JSONL 格式：

```jsonl
{"messages": [{"role": "user", "content": "查询2012年票房前十的电影"}, {"role": "assistant", "content": "2012年票房前十的电影如下：\n1. 复仇者联盟..."}]}
{"messages": [{"role": "user", "content": "帮我画一个票房趋势图"}, {"role": "assistant", "content": "好的，已为您生成票房趋势图..."}]}
```

---

## 四、评估 Prompt

### 4.1 对话质量评估（user_chat_logs / admin_chat_logs / security_warning_logs）

```python
RESPONSE_EVAL_PROMPT = """你是一个 LLM 输出质量评估员。请对以下对话记录进行质量评估。

用户输入：{user_content}
AI 回复：{ai_response}

请从以下维度打分（1-5分）：
1. 相关性：AI 回复是否准确回答了用户的问题
2. 完整性：回复是否包含充分的信息，有无遗漏
3. 准确性：回复中的数据是否正确无误
4. 格式：回复是否清晰易读，结构良好

评分标准：
- 5分：完全符合要求，无任何问题
- 4分：基本符合，有小瑕疵但不影响使用
- 3分：部分符合，有明显不足
- 2分：严重不足，影响使用
- 1分：完全不符合，答非所问或数据错误

请严格以 JSON 格式输出，不要输出其他内容：
{"score": 4, "dimensions": {"相关性": 5, "完整性": 4, "准确性": 5, "格式": 3}, "issues": "格式可以更清晰", "verdict": "pass"}

verdict 规则：
- score >= 4：pass
- score == 3：review
- score <= 2：fail"""
```

### 4.2 绘图代码评估（chart_generation_logs）

```python
CODE_EVAL_PROMPT = """你是一个代码质量评估员。请评估以下 pyecharts 绘图代码的质量。

用户需求：{question}
生成的代码：{code}
执行结果：{"success": true/false, "error": "错误信息"}

请从以下维度打分（1-5分）：
1. 可运行性：代码是否能正确执行并生成图表
2. 图表完整性：是否包含标题、坐标轴名称
3. 工具箱：是否包含 ToolboxOpts（用户可下载图片）
4. 单位标注：坐标轴是否有单位说明（如"票房（万美元）"）
5. 类型匹配：图表类型是否符合用户需求（如趋势用折线图、对比用柱状图）

评分标准：
- 5分：完全符合要求
- 4分：基本符合，有小瑕疵
- 3分：部分符合，有明显不足
- 2分：严重不足
- 1分：完全不符合

请严格以 JSON 格式输出，不要输出其他内容：
{"score": 4, "dimensions": {"可运行性": 5, "图表完整性": 4, "工具箱": 3, "单位标注": 4, "类型匹配": 5}, "issues": "缺少工具箱配置", "verdict": "pass"}

verdict 规则：
- score >= 4：pass
- score == 3：review
- score <= 2：fail"""
```

---

## 五、评估逻辑（Python 伪代码）

```python
import json
import threading
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="deepseek-chat", temperature=0)

# 全局进度
eval_progress = {"total": 0, "completed": 0, "status": "idle"}

def evaluate_records(records, eval_type):
    """后台线程执行评估"""
    eval_progress["status"] = "running"
    eval_progress["total"] = len(records)
    eval_progress["completed"] = 0

    for record in records:
        if eval_type == "response":
            prompt = RESPONSE_EVAL_PROMPT.format(
                user_content=record["user_content"],
                ai_response=record["ai_content"]
            )
        elif eval_type == "code":
            prompt = CODE_EVAL_PROMPT.format(
                question=record["question"],
                code=record["code"]
            )

        try:
            result = llm.invoke(prompt).content
            # 去掉可能的 markdown 包裹
            result = result.strip()
            if result.startswith("```"):
                result = result.split("\n", 1)[1].rsplit("```", 1)[0]
            eval_data = json.loads(result)
        except:
            eval_data = {"score": 0, "dimensions": {}, "issues": "JSON解析失败", "verdict": "fail"}

        # 存入 eval_results 表
        save_eval_result(
            source_table=record["source_table"],
            source_id=record["id"],
            eval_type=eval_type,
            score=eval_data.get("score", 0),
            dimensions=json.dumps(eval_data.get("dimensions", {}), ensure_ascii=False),
            issues=eval_data.get("issues", ""),
            verdict=eval_data.get("verdict", "fail")
        )

        eval_progress["completed"] += 1

    eval_progress["status"] = "done"
```

---

## 六、前端页面（analyst.html）

### 6.1 页面结构

```
顶部导航栏：数据分析平台 | [导出JSONL] 按钮
三个 Tab：数据概览 | 质量评估 | 微调数据
```

### 6.2 数据概览 Tab

页面加载时自动请求 `/api/analyst/overview`，展示 4 个 ECharts 图表：

| 图表 | 类型 | 数据 |
|------|------|------|
| 对话量趋势 | 折线图 | chat_trend |
| 意图分布 | 饼图 | intent_distribution |
| 绘图成功率 | 环形图 | chart_success_rate |
| 攻击类型分布 | 柱状图 | attack_distribution |

### 6.3 质量评估 Tab

左侧筛选区：
- 时间范围：开始日期 ~ 结束日期
- 数据来源：4 个复选框（user_chat_logs / admin_chat_logs / chart_generation_logs / security_warning_logs）
- [开始评估] 按钮
- 进度条（轮询 /api/analyst/evaluate/status）

右侧展示区（评估完成后展示）：
- 评分分布柱状图（1-5 分各多少条）
- 各维度平均分雷达图
- 低分案例表格（score <= 3，显示问题原因）

### 6.4 微调数据 Tab

筛选区：
- 最低评分：下拉选择（3/4/5）
- 数据来源：复选框
- 时间范围
- [预览] 按钮 | [导出JSONL] 按钮

预览区：展示前 10 条 JSONL 数据
导出：调 `/api/analyst/export` 下载文件

---

## 七、开发顺序

1. 建表 eval_results + 插入 analyst 用户
2. Node.js 登录接口支持 analyst 角色跳转
3. FastAPI：/api/analyst/overview（数据概览）
4. 前端 analyst.html：数据概览 Tab + 4 个图表
5. FastAPI：/api/analyst/evaluate + /status（质量评估）
6. 前端：质量评估 Tab + 进度条 + 结果图表
7. FastAPI：/api/analyst/export（JSONL 导出）
8. 前端：微调数据 Tab + 导出功能
9. 测试完整流程

---

## 八、注意事项

- 评估是异步的，用 threading.Thread 在后台执行，前端轮询进度
- LLM 返回的 JSON 可能被 markdown 包裹（```json ... ```），需要去掉
- JSON 解析失败时给 0 分，不要让程序崩溃
- 导出 JSONL 时，对话记录要按 session 分组，每组是一个训练样本
- eval_results 表的 dimensions 字段用 JSON 类型存储各维度得分
- 所有 API 都要验证 analyst 身份（从请求头或 token 获取）
