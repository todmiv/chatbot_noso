from prometheus_client import Counter, Histogram, start_http_server

REQUESTS_TOTAL = Counter('sro_bot_requests_total', 'Total number of requests to the bot')
LATENCY_SECONDS = Histogram('sro_bot_latency_seconds', 'Request latency in seconds', buckets=[0.1, 0.5, 1, 2, 5, 10])
TOKENS_USED = Counter('openai_tokens_used', 'Total tokens used in OpenAI API calls')

def start_prometheus_server(port=8000):
    start_http_server(port)
