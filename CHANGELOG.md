# Changelog

All notable changes to the Production AI Control Plane will be documented in this file.

## [1.2.0] - 2025-10-16

### Added

- **Security Middleware**: Implemented automatic secret masking in structured logs. The `mask_secrets` processor now automatically redacts API keys, bearer tokens, and sensitive headers (Address #4).

### Fixed

- **Gateway Resilience**: Safely handle missing `usage` fields in upstream OpenAI API responses to prevent application crashes (#2).

## [1.1.0] - 2025-10-13

### Added

- **Cost Governance**: Integrated a real-time cost calculation engine into the `LLMGateway`. Users can now track estimated spending based on model-specific token pricing (Address #3).

### Fixed

- **Pipeline Scaling**: Resolved a race condition in the Pipeline Engine when multiple stages attempted to update the shared execution context during parallel runs. Added `asyncio.Lock` for thread-safe state management (#1).

## [1.0.0] - 2025-09-30

### Added

- **Real LLM Providers**: Integrated OpenAI and Google Gemini API adapters.
- **Model Registry**: Implemented versioning and status management (staging/production) for local model deployments.
- **Distributed Tracing**: End-to-end OpenTelemetry integration across gateway and pipeline modules.
- **Validation Gates**: Pydantic-based data quality enforcement for ML workflows.

## [0.5.0] - 2025-09-15

### Added

- **Observability Stack**: Prometheus metrics and structured JSON logging.
- **CLI Interface**: Unified command-line interface for chat and pipeline evaluation.

## [0.2.0] - 2025-08-25

### Added

- **Core Orchestrator**: Initial implementation of the `@stage` and `@pipeline` decorators and execution loop.
- **LLM Gateway Foundation**: Reliability layer with Circuit Breakers and Fallback chains.

## [0.1.0] - 2025-08-01

### Added

- Initial project scaffolding and core abstractions.
