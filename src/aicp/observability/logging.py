import structlog
import sys
import logging

def mask_secrets(logger, method_name, event_dict):
    """Mask potential secrets in logs."""
    secret_keys = ["api_key", "token", "password", "authorization"]
    for key in secret_keys:
        if key in event_dict:
            event_dict[key] = "********"
    # Mask obvious bearer tokens
    if "content" in event_dict and "Bearer " in str(event_dict["content"]):
        event_dict["content"] = "[SECURE_TOKEN_MASKED]"
    return event_dict

def setup_logging(level: str = "INFO"):
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            mask_secrets,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer() if not sys.stderr.isatty() else structlog.dev.ConsoleRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level)),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

logger = structlog.get_logger()
