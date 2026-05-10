import os
import httpx
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

_http_client = httpx.Client(
    limits=httpx.Limits(max_keepalive_connections=20, max_connections=40, keepalive_expiry=30),
    timeout=httpx.Timeout(60.0, connect=30.0)
)
_http_async_client = httpx.AsyncClient(
    limits=httpx.Limits(max_keepalive_connections=20, max_connections=40, keepalive_expiry=10),
    timeout=httpx.Timeout(60.0, connect=30.0)
)

llm = ChatOpenAI(
    model=os.getenv('MODEL_NAME'),
    openai_api_key=os.getenv('API_KEY'),
    openai_api_base=os.getenv('API_BASE'),
    temperature=0.1,
    extra_body={"thinking": {"type": "disabled"}},
    http_client=_http_client,
    http_async_client=_http_async_client
)

# 同步 invoke 调用
result = llm.invoke("简单介绍一下自己，用一句话")
print("=== type of result ===")
print(type(result))
print()

print("=== dir of result(过滤) ===")
attrs = [a for a in dir(result) if not a.startswith('_')]
for a in attrs:
    print(f"  {a}")
print()

print("=== result.content ===")
print(repr(result.content))
print()

print("=== result.response_metadata ===")
import json
try:
    print(json.dumps(result.response_metadata, ensure_ascii=False, indent=2))
except:
    print(result.response_metadata)
print()

print("=== result.usage_metadata ===")
try:
    print(json.dumps(result.usage_metadata, ensure_ascii=False, indent=2))
except:
    print(result.usage_metadata)
print()

# 检查是否有 token 相关信息
print("=== 是否有 token 相关信息 ===")
if hasattr(result, 'usage_metadata') and result.usage_metadata:
    print("usage_metadata 存在!")
    print(f"  prompt_tokens: {result.usage_metadata.get('input_tokens')}")
    print(f"  completion_tokens: {result.usage_metadata.get('output_tokens')}")
    print(f"  total_tokens: {result.usage_metadata.get('total_tokens')}")

if hasattr(result, 'response_metadata') and result.response_metadata:
    rm = result.response_metadata
    print("response_metadata 中的 token 信息:")
    for key in rm:
        if 'token' in key.lower():
            print(f"  {key}: {rm[key]}")
