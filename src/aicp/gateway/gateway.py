from typing import List, Optional
from .providers.base import LLMProvider, CompletionRequest, CompletionResponse
from .reliability import ReliabilityLayer
from .middleware import Middleware, MiddlewarePipeline
from ..observability.tracing import traced

class LLMGateway:
    def __init__(
        self,
        providers: List[LLMProvider],
        middlewares: Optional[List[Middleware]] = None,
        max_retries: int = 3
    ):
        self.reliability = ReliabilityLayer(providers, max_retries=max_retries)
        self.pipeline = MiddlewarePipeline(middlewares or [])

    @traced(name="llm_gateway_completion")
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        # 1. Run pre-processing middleware (Security, PII, etc.)
        processed_request = await self.pipeline.run_pre(request)
        
        # 2. Execute with reliability patterns (Retries, Circuit Breakers, Fallbacks)
        response = await self.reliability.execute_with_fallback(processed_request)
        
        # 3. Calculate estimated cost
        response.cost = self._calculate_cost(response.model, response.usage)
        
        # 4. Run post-processing middleware
        final_response = await self.pipeline.run_post(response)
        
        return final_response

    def _calculate_cost(self, model: str, usage: Any) -> float:
        # Simplified internal pricing table (price per 1k tokens)
        pricing = {
            "gpt-4": {"prompt": 0.03, "completion": 0.06},
            "gpt-3.5-turbo": {"prompt": 0.0015, "completion": 0.002},
            "gemini-pro": {"prompt": 0.000125, "completion": 0.000375}
        }
        
        base_model = next((k for k in pricing if k in model), "gpt-3.5-turbo")
        rates = pricing[base_model]
        
        cost = (usage.prompt_tokens / 1000 * rates["prompt"]) + \
               (usage.completion_tokens / 1000 * rates["completion"])
        return round(cost, 6)
