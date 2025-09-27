from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from typing import Optional, Dict, Any
import functools

def setup_tracing(service_name: str = "aicp-control-plane"):
    """Initialize OpenTelemetry tracing with a console exporter."""
    resource = Resource.create({
        "service.name": service_name,
        "service.version": "0.1.0"
    })
    
    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)
    
    trace.set_tracer_provider(provider)

def get_tracer(name: str = "aicp"):
    return trace.get_tracer(name)

def traced(name: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None):
    """Decorator to trace a function execution."""
    def decorator(func):
        span_name = name or func.__name__
        tracer = get_tracer()

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with tracer.start_as_current_span(span_name) as span:
                if attributes:
                    for k, v in attributes.items():
                        span.set_attribute(k, v)
                return func(*args, **kwargs)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            with tracer.start_as_current_span(span_name) as span:
                if attributes:
                    for k, v in attributes.items():
                        span.set_attribute(k, v)
                return await func(*args, **kwargs)

        import asyncio
        return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper
    return decorator
