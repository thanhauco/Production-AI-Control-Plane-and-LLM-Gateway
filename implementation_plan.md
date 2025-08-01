# Production AI Control Plane

A unified platform for managing AI workloads from experimentation to production, combining an **intelligent LLM Gateway** with an **ML Pipeline Orchestrator** — built for enterprise reliability, observability, and security.

---

## User Review Required

> [!IMPORTANT] > **Scope Decision**: This plan covers a comprehensive system. We can:
>
> - **Full Build**: All 5 phases (~300-400 lines of core code + tests)
> - **MVP First**: Phases 1-2 only (Gateway with reliability patterns), then iterate

> [!NOTE] > **Tech Stack**: Python 3.11+, `httpx` for async HTTP, `pydantic` for validation, `structlog` for logging, `prometheus-client` for metrics. No heavy frameworks — designed for portability.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONTROL PLANE CLI / API                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────┐    ┌──────────────────────────────┐  │
│  │    LLM GATEWAY       │    │    PIPELINE ORCHESTRATOR     │  │
│  │  ┌────────────────┐  │    │  ┌────────────────────────┐  │  │
│  │  │ Middleware     │  │    │  │ Pipeline DSL           │  │  │
│  │  │ • PII Redact   │  │    │  │ • YAML + Decorators    │  │  │
│  │  │ • Rate Limit   │  │    │  └────────────────────────┘  │  │
│  │  │ • Audit Log    │  │    │  ┌────────────────────────┐  │  │
│  │  └────────────────┘  │    │  │ Execution Engine       │  │  │
│  │  ┌────────────────┐  │    │  │ • DAG Scheduling       │  │  │
│  │  │ Reliability    │  │    │  │ • Checkpointing        │  │  │
│  │  │ • Circuit Brk  │  │    │  └────────────────────────┘  │  │
│  │  │ • Retry/Back   │  │    │  ┌────────────────────────┐  │  │
│  │  │ • Fallback     │  │    │  │ Integrations           │  │  │
│  │  └────────────────┘  │    │  │ • MLflow / W&B         │  │  │
│  │  ┌────────────────┐  │    │  │ • Model Registry       │  │  │
│  │  │ Providers      │  │    │  └────────────────────────┘  │  │
│  │  │ • OpenAI       │  │    └──────────────────────────────┘  │
│  │  │ • Anthropic    │  │                                      │
│  │  │ • Local/Mock   │  │                                      │
│  │  └────────────────┘  │                                      │
│  └──────────────────────┘                                      │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                    OBSERVABILITY LAYER                          │
│   Structured Logs │ Metrics (Prometheus) │ Traces (OpenTel)    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Proposed Changes

### Core Package Structure

#### [NEW] [pyproject.toml](file:///Users/jordan_mbp/.gemini/antigravity/playground/gravitic-magnetar/pyproject.toml)

Package definition with dependencies: `httpx`, `pydantic`, `structlog`, `prometheus-client`, `pyyaml`, `typer`

#### [NEW] [src/aicp/\_\_init\_\_.py](file:///Users/jordan_mbp/.gemini/antigravity/playground/gravitic-magnetar/src/aicp/__init__.py)

Package root exposing main public APIs

---

### Gateway Module (`src/aicp/gateway/`)

#### [NEW] [providers/base.py](file:///Users/jordan_mbp/.gemini/antigravity/playground/gravitic-magnetar/src/aicp/gateway/providers/base.py)

Abstract `LLMProvider` protocol + `CompletionRequest`/`CompletionResponse` models

#### [NEW] [providers/openai.py](file:///Users/jordan_mbp/.gemini/antigravity/playground/gravitic-magnetar/src/aicp/gateway/providers/openai.py)

OpenAI adapter with async completion, streaming support

#### [NEW] [providers/anthropic.py](file:///Users/jordan_mbp/.gemini/antigravity/playground/gravitic-magnetar/src/aicp/gateway/providers/anthropic.py)

Anthropic Claude adapter

#### [NEW] [providers/mock.py](file:///Users/jordan_mbp/.gemini/antigravity/playground/gravitic-magnetar/src/aicp/gateway/providers/mock.py)

Deterministic mock provider for testing

#### [NEW] [reliability.py](file:///Users/jordan_mbp/.gemini/antigravity/playground/gravitic-magnetar/src/aicp/gateway/reliability.py)

- `CircuitBreaker`: Tracks failures, trips open after threshold, half-open recovery
- `RetryPolicy`: Exponential backoff with jitter, configurable max attempts
- `FallbackChain`: Ordered list of providers, failover on error

#### [NEW] [middleware.py](file:///Users/jordan_mbp/.gemini/antigravity/playground/gravitic-magnetar/src/aicp/gateway/middleware.py)

- `PIIRedactor`: Regex + spaCy NER-based PII detection/masking
- `PromptGuard`: Injection pattern detection, blocklist enforcement
- `RateLimiter`: Token bucket algorithm per-client
- `AuditLogger`: Structured request/response logging

#### [NEW] [gateway.py](file:///Users/jordan_mbp/.gemini/antigravity/playground/gravitic-magnetar/src/aicp/gateway/gateway.py)

Main `LLMGateway` class orchestrating middleware → reliability → provider

---

### Pipeline Module (`src/aicp/pipeline/`)

#### [NEW] [models.py](file:///Users/jordan_mbp/.gemini/antigravity/playground/gravitic-magnetar/src/aicp/pipeline/models.py)

`Pipeline`, `Stage`, `StageResult`, `PipelineRun` Pydantic models

#### [NEW] [decorators.py](file:///Users/jordan_mbp/.gemini/antigravity/playground/gravitic-magnetar/src/aicp/pipeline/decorators.py)

`@stage`, `@pipeline` decorators for Pythonic pipeline definition

#### [NEW] [engine.py](file:///Users/jordan_mbp/.gemini/antigravity/playground/gravitic-magnetar/src/aicp/pipeline/engine.py)

Execution engine: DAG resolution, parallel execution, checkpointing

#### [NEW] [tracking.py](file:///Users/jordan_mbp/.gemini/antigravity/playground/gravitic-magnetar/src/aicp/pipeline/tracking.py)

Experiment tracking adapter (MLflow integration)

#### [NEW] [registry.py](file:///Users/jordan_mbp/.gemini/antigravity/playground/gravitic-magnetar/src/aicp/pipeline/registry.py)

Model versioning: register, promote (staging → production), rollback

#### [NEW] [validation.py](file:///Users/jordan_mbp/.gemini/antigravity/playground/gravitic-magnetar/src/aicp/pipeline/validation.py)

Data validation gates using Pydantic + custom validators

---

### Observability Module (`src/aicp/observability/`)

#### [NEW] [logging.py](file:///Users/jordan_mbp/.gemini/antigravity/playground/gravitic-magnetar/src/aicp/observability/logging.py)

Structured logging setup with `structlog`, JSON output for prod

#### [NEW] [metrics.py](file:///Users/jordan_mbp/.gemini/antigravity/playground/gravitic-magnetar/src/aicp/observability/metrics.py)

Prometheus metrics: request latency, token counts, error rates, circuit breaker state

#### [NEW] [tracing.py](file:///Users/jordan_mbp/.gemini/antigravity/playground/gravitic-magnetar/src/aicp/observability/tracing.py)

OpenTelemetry trace context propagation hooks

---

### CLI & API

#### [NEW] [cli.py](file:///Users/jordan_mbp/.gemini/antigravity/playground/gravitic-magnetar/src/aicp/cli.py)

Typer-based CLI: `aicp gateway chat`, `aicp pipeline run`, `aicp registry list`

#### [NEW] [api.py](file:///Users/jordan_mbp/.gemini/antigravity/playground/gravitic-magnetar/src/aicp/api.py)

Optional FastAPI server exposing gateway + pipeline operations

---

### Examples & Documentation

#### [NEW] [examples/](file:///Users/jordan_mbp/.gemini/antigravity/playground/gravitic-magnetar/examples/)

- `simple_chat.py` — Basic gateway usage
- `rag_pipeline.py` — RAG pipeline with validation gates
- `ab_test_pipeline.py` — A/B model comparison with tracking

#### [NEW] [README.md](file:///Users/jordan_mbp/.gemini/antigravity/playground/gravitic-magnetar/README.md)

Project overview, quickstart, architecture diagram, configuration reference

---

## Verification Plan

### Automated Tests

```bash
# Unit tests for all modules
pytest tests/ -v --cov=aicp --cov-report=term-missing

# Integration test: gateway with mock provider
pytest tests/integration/test_gateway_e2e.py

# Pipeline execution test
pytest tests/integration/test_pipeline_execution.py
```

### Manual Verification

- Run example scripts and verify expected output
- Trigger circuit breaker by simulating provider failures
- Confirm metrics exposed at `/metrics` endpoint
- Review structured logs for completeness
