from langchain_core.callbacks import AsyncCallbackHandler
from app.metrics import agent_token_usage_total


class TokenTrackerCallback(AsyncCallbackHandler):

    def __init__(self, agent_name: str):
        self.agent_name = agent_name

    async def on_llm_end(self, response, **kwargs):
        usage = {}
        if response.llm_output:
            usage = response.llm_output.get("usage", {})
        if not usage:
            for gen_list in response.generations:
                for gen in gen_list:
                    msg = getattr(gen, 'message', None)
                    if msg and hasattr(msg, 'usage_metadata') and msg.usage_metadata:
                        usage = msg.usage_metadata
                        break
                if usage:
                    break
        input_tokens = usage.get("input_tokens", 0) or usage.get("prompt_tokens", 0)
        output_tokens = usage.get("output_tokens", 0) or usage.get("completion_tokens", 0)
        if input_tokens:
            agent_token_usage_total.labels(agent=self.agent_name, token_type="input").inc(input_tokens)
        if output_tokens:
            agent_token_usage_total.labels(agent=self.agent_name, token_type="output").inc(output_tokens)
