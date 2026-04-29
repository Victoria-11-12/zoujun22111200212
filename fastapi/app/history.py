from langchain_core.messages import HumanMessage, AIMessage


conversation_history: dict[str, list] = {}
MAX_HISTORY = 10


def get_history(session_id: str) -> list:
    return conversation_history.get(session_id, [])


def save_history(session_id: str, user_msg: str, ai_msg: str):
    history = conversation_history.get(session_id, [])
    history.append(HumanMessage(content=user_msg))
    history.append(AIMessage(content=ai_msg))
    if len(history) > MAX_HISTORY * 2:
        history = history[-MAX_HISTORY * 2:]
    conversation_history[session_id] = history
