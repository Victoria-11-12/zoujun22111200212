# 评估链
# 用于评估AI回复质量和代码质量

from langchain_core.prompts import ChatPromptTemplate
from app.config import eval_llm
from app.models import ResponseEvalResult, CodeEvalResult


# 文本类回复评估链
response_eval_prompt = ChatPromptTemplate.from_template("""你是一个 LLM 输出质量评估员。请对以下对话记录进行质量评估。

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

verdict 规则：
- score >= 4：pass
- score == 3：review
- score <= 2：fail

请只输出 JSON，不要其他内容，格式如下：
{{
    "score": <整数1-5>,
    "dimensions": {{
        "relevance": <整数1-5>,
        "completeness": <整数1-5>,
        "accuracy": <整数1-5>,
        "format": <整数1-5>
    }},
    "issues": "<问题描述>",
    "verdict": "<pass/review/fail>"
}}""")

response_eval_chain = response_eval_prompt | eval_llm.with_structured_output(
    ResponseEvalResult,
    method="json_mode"
)


# 代码类评估链
code_eval_prompt = ChatPromptTemplate.from_template("""你是一个代码质量评估员。请评估以下 pyecharts 绘图代码的质量。

用户需求：{question}
生成的代码：{code}
执行结果：{exec_result}

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

verdict 规则：
- score >= 4：pass
- score == 3：review
- score <= 2：fail

请只输出 JSON，不要其他内容，格式如下：
{{
    "score": <整数1-5>,
    "dimensions": {{
        "runnable": <整数1-5>,
        "chart_completeness": <整数1-5>,
        "toolbox": <整数1-5>,
        "unit_label": <整数1-5>,
        "chart_type_match": <整数1-5>
    }},
    "issues": "<问题描述>",
    "verdict": "<pass/review/fail>"
}}""")

code_eval_chain = code_eval_prompt | eval_llm.with_structured_output(
    CodeEvalResult,
    method="json_mode"
)
