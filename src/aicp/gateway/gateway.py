from typing import List, Optional
from .providers.base import LLMProvider, CompletionRequest, CompletionResponse
from .reliability import ReliabilityLayer
from .middleware import Middleware, MiddlewarePipeline

class LLMGateway:
    def __init__(
        self,
        providers: List[LLMProvider],
        middlewares: Optional[List[Middleware]] = None,
        max_retries: int = 3
    ):
        self.reliability = ReliabilityLayer(providers, max_retries=max_retries)
        self.pipeline = MiddlewarePipeline(middlewares or [])

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        # 1. Run pre-processing middleware (Security, PII, etc.)
        processed_request = await self.pipeline.run_pre(request)
        
        # 2. Execute with reliability patterns (Retries, Circuit Breakers, Fallbacks)
        response = await self.reliability.execute_with_fallback(processed_request)
        
        # 3. Run post-processing middleware
        final_response = await self.pipeline.run_post(response)
        
        return final_response
