from langchain_core.messages import HumanMessage, AIMessage


#这个字典用于存储每个会话的对话历史，str是会话id，由前端生成并传过来，list是对话历史列表，里面是元组，每个元组包含用户消息和AI消息
conversation_history: dict[str, list] = {}
#最大历史记录数，超过这个数的记录会被删除
MAX_HISTORY = 10

#获取会话历史
#根据会话id返回会话历史，如果会话id不存在，返回空列表
def get_history(session_id: str) -> list:
    return conversation_history.get(session_id, [])

#保存会话历史
#根据会话id保存会话历史，如果会话id不存在，创建一个新的会话历史列表
def save_history(session_id: str, user_msg: str, ai_msg: str):
    history = conversation_history.get(session_id, [])
    #langchain的消息格式，不能传字符串，必须用HumanMessage和AIMessage进行封装，否则会报错HumanMessage是用户消息，AIMessage是AI消息
    history.append(HumanMessage(content=user_msg))
    history.append(AIMessage(content=ai_msg))
    #一轮对话包含用户信息和AI信息，保存十轮对话，所以最大历史记录数是2倍的MAX_HISTORY
    if len(history) > MAX_HISTORY * 2:
        history = history[-MAX_HISTORY * 2:]
    conversation_history[session_id] = history
