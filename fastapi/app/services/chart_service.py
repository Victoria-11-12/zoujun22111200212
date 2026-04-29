# 图表服务
# 处理图表生成业务逻辑

import json
from fastapi.responses import StreamingResponse

from app.models import ChartRequest
from app.chains.chart_chains import chart_intent_chain, chart_not_chain
from app.workflows.chart_workflow import chart_graph


# 图表生成接口
async def chart_generate(request: ChartRequest):
    """图表生成流式接口"""
    chart_message = request.message
    session_id = request.sessionId
    user_name = request.username

    intent = await chart_intent_chain.ainvoke({"question": chart_message})
    intent = intent.strip().upper()
    print(f"绘图意图判断: {intent}, 问题: {chart_message}")

    async def generate():
        try:
            if "NOT_CHART" in intent:
                reply = await chart_not_chain.ainvoke({"question": chart_message})
                yield f"data: {json.dumps({'type': 'text', 'content': reply}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
                return

            result = await chart_graph.ainvoke(
                {
                    "question": chart_message,
                    "session_id": session_id,
                    "user_name": user_name,
                    "feedback": "",
                    "attempts": 0,
                }
            )

            if result.get("chart_html"):
                yield f"data: {json.dumps({'type': 'chart', 'chart_html': result['chart_html']}, ensure_ascii=False)}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'text', 'content': result.get('error', '图表生成失败')}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            print(f"绘图接口报错: {e}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'text', 'content': str(e)}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )
