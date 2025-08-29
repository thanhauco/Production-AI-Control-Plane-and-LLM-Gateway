import pytest
import asyncio
from aicp.gateway.reliability import CircuitBreaker, ReliabilityLayer
from aicp.gateway.providers.base import LLMProvider, CompletionRequest, CompletionResponse, Usage, Role

class FailingProvider(LLMProvider):
    def __init__(self, name="failing"):
        self.name = name
        self.calls = 0

    @property
    def provider_name(self):
        return self.name

    async def complete(self, request):
        self.calls += 1
        raise Exception("Service Unavailable")

class SuccessProvider(LLMProvider):
    def __init__(self, name="success"):
        self.name = name

    @property
    def provider_name(self):
        return self.name

    async def complete(self, request):
        return CompletionResponse(
            id="ok", model="test", content="success",
            usage=Usage(prompt_tokens=1, completion_tokens=1, total_tokens=2)
        )

@pytest.mark.asyncio
async def test_circuit_breaker_trips():
    breaker = CircuitBreaker("test", failure_threshold=2, recovery_timeout=0.1)
    assert breaker.can_execute() is True
    
    breaker.record_failure()
    assert breaker.can_execute() is True
    
    breaker.record_failure()
    assert breaker.can_execute() is False
    assert breaker.state == "OPEN"

@pytest.mark.asyncio
async def test_reliability_layer_fallback():
    failing = FailingProvider("primary")
    success = SuccessProvider("secondary")
    
    layer = ReliabilityLayer(providers=[failing, success], max_retries=1)
    
    req = CompletionRequest(model="test", messages=[])
    resp = await layer.execute_with_fallback(req)
    
    assert resp.content == "success"
    assert failing.calls == 1
    # On second call, the primary breaker should be OPEN (if threshold reached)
    # Actually, in ReliabilityLayer, it records failure on every attempt.
