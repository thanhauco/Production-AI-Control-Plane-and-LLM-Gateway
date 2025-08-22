from prometheus_client import Counter, Histogram, Gauge

# Gateway Metrics
REQUESTS_TOTAL = Counter(
    "aicp_gateway_requests_total",
    "Total number of LLM requests",
    ["provider", "model", "status"]
)

LATENCY_SECONDS = Histogram(
    "aicp_gateway_latency_seconds",
    "Request latency in seconds",
    ["provider", "model"]
)

TOKENS_TOTAL = Counter(
    "aicp_gateway_tokens_total",
    "Total tokens consumed",
    ["provider", "type"] # type: prompt, completion
)

CIRCUIT_BREAKER_STATE = Gauge(
    "aicp_circuit_breaker_state",
    "State of the circuit breaker (0=Closed, 1=Open, 2=Half-Open)",
    ["breaker"]
)

# Pipeline Metrics
PIPELINE_RUNS = Counter(
    "aicp_pipeline_runs_total",
    "Total number of pipeline runs",
    ["pipeline", "status"]
)

STAGE_LATENCY = Histogram(
    "aicp_pipeline_stage_latency_seconds",
    "Pipeline stage latency",
    ["pipeline", "stage"]
)
