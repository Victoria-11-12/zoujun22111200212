from prometheus_client import Counter, Histogram, CollectorRegistry

registry = CollectorRegistry()

# HTTP 请求计数器
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['service', 'method', 'endpoint', 'status'],
    registry=registry
)

# HTTP 请求延迟直方图
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['service', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1, 2, 5],
    registry=registry
)

# Agent token 消耗计数器
agent_token_usage_total = Counter(
    'agent_token_usage_total',
    'Total token usage by agent',
    ['agent', 'token_type'],
    registry=registry
)
