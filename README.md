# Production AI Control Plane

A unified platform for managing AI workloads from experimentation to production, combining an **intelligent LLM Gateway** with an **ML Pipeline Orchestrator** — built for enterprise reliability, observability, and security.

## Features

### 🚀 LLM Gateway

- **Reliability Layer**: Circuit breakers, exponential backoff retries, and multi-provider fallback chains.
- **Security Middleware**: Automatic PII redaction and prompt injection detection.
- **Governance**: Token-bucket rate limiting and comprehensive audit logging.
- **Provider Adapters**: OpenAI, Anthropic, and local/mock support.

### ⛓️ Pipeline Orchestrator

- **Pythonic DSL**: Define complex ML workflows using simple decorators.
- **Execution Engine**: Support for sequential, parallel, and conditional execution with checkpointing.
- **Validation Gates**: Pydantic-based data validation between pipeline stages.
- **Tracking**: Integrated experiment tracking and model registry.

### 📊 Observability

- **Structured Logging**: JSON logs ready for ELK/Splunk.
- **Metrics**: Prometheus instrumentation for latency, costs, and health.
- **Tracing**: OpenTelemetry support for end-to-end request tracing.

## Quickstart

```python
from aicp.gateway import LLMGateway
from aicp.gateway.providers import OpenAIProvider

gateway = LLMGateway(
    primary_provider=OpenAIProvider(api_key="..."),
    enable_reliability=True
)

response = await gateway.complete("Explain quantum computing in production terms.")
```

## Structure

```text
src/aicp/
├── gateway/       # LLM Gateway, reliability, middleware
├── pipeline/      # ML Pipeline DSL and execution engine
├── observability/ # Logging, metrics, and tracing
└── cli.py         # Command-line interface
```
