import asyncio
import time
from typing import List, Optional, Callable, Dict, Any
import structlog
from .providers.base import LLMProvider, CompletionRequest, CompletionResponse

logger = structlog.get_logger()

class CircuitBreakerOpenError(Exception):
    """Raised when the circuit breaker is open."""
    pass

class CircuitBreaker:
    def __init__(
        self, 
        name: str, 
        failure_threshold: int = 5, 
        recovery_timeout: float = 30.0
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time: Optional[float] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def record_success(self):
        if self.state == "HALF_OPEN":
            logger.info("circuit_breaker_recovered", breaker=self.name)
        self.failures = 0
        self.state = "CLOSED"
        self.last_failure_time = None

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
            logger.warn("circuit_breaker_opened", breaker=self.name, failures=self.failures)

    def can_execute(self) -> bool:
        if self.state == "CLOSED":
            return True
        
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.info("circuit_breaker_half_open", breaker=self.name)
                return True
            return False
        
        return True # HALF_OPEN allows testing

class ReliabilityLayer:
    def __init__(
        self,
        providers: List[LLMProvider],
        max_retries: int = 3,
        base_delay: float = 1.0
    ):
        self.providers = providers
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.breakers = {p.provider_name: CircuitBreaker(p.provider_name) for p in providers}

    async def execute_with_fallback(self, request: CompletionRequest) -> CompletionResponse:
        last_error = None
        
        for provider in self.providers:
            breaker = self.breakers[provider.provider_name]
            
            if not breaker.can_execute():
                logger.debug("skipping_provider_breaker_open", provider=provider.provider_name)
                continue

            for attempt in range(self.max_retries):
                try:
                    logger.info("attempting_request", provider=provider.provider_name, attempt=attempt+1)
                    response = await provider.complete(request)
                    breaker.record_success()
                    return response
                except Exception as e:
                    logger.error("request_failed", provider=provider.provider_name, error=str(e), attempt=attempt+1)
                    breaker.record_failure()
                    last_error = e
                    
                    if attempt < self.max_retries - 1:
                        delay = self.base_delay * (2 ** attempt) # Exponential backoff
                        await asyncio.sleep(delay)
                    else:
                        break # Try next provider

        raise last_error or Exception("All providers failed or breakers are open")
