import re
from typing import List, Optional
import structlog
from .providers.base import CompletionRequest, CompletionResponse

logger = structlog.get_logger()

class Middleware:
    async def pre_process(self, request: CompletionRequest) -> CompletionRequest:
        return request

    async def post_process(self, response: CompletionResponse) -> CompletionResponse:
        return response

class PIIRedactor(Middleware):
    # Simplified regex-based PII detection for the MVP
    PII_PATTERNS = {
        "EMAIL": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
        "PHONE": r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
        "SSN": r"\d{3}-\d{2}-\d{4}",
        "CREDIT_CARD": r"\b(?:\d[ -]*?){13,16}\b"
    }

    def __init__(self, entities: Optional[List[str]] = None):
        self.entities = entities or list(self.PII_PATTERNS.keys())

    async def pre_process(self, request: CompletionRequest) -> CompletionRequest:
        new_messages = []
        for msg in request.messages:
            content = msg.content
            for entity in self.entities:
                pattern = self.PII_PATTERNS.get(entity)
                if pattern:
                    content = re.sub(pattern, f"[{entity}_REDACTED]", content)
            new_messages.append(msg.model_copy(update={"content": content}))
        
        return request.model_copy(update={"messages": new_messages})

    async def post_process(self, response: CompletionResponse) -> CompletionResponse:
        content = response.content
        for entity in self.entities:
            pattern = self.PII_PATTERNS.get(entity)
            if pattern:
                content = re.sub(pattern, f"[{entity}_REDACTED]", content)
        
        return response.model_copy(update={"content": content})

class PromptGuard(Middleware):
    INJECTION_PATTERNS = [
        r"ignore all previous instructions",
        r"system prompt:",
        r"you are now a",
        r"bypass",
        r"do not mention"
    ]

    async def pre_process(self, request: CompletionRequest) -> CompletionRequest:
        for msg in request.messages:
            for pattern in self.INJECTION_PATTERNS:
                if re.search(pattern, msg.content, re.IGNORECASE):
                    logger.warn("potential_prompt_injection_detected", pattern=pattern)
                    # We could raise an error here or just log it
                    # For now, we'll just log
        return request

class MiddlewarePipeline:
    def __init__(self, middlewares: List[Middleware]):
        self.middlewares = middlewares

    async def run_pre(self, request: CompletionRequest) -> CompletionRequest:
        for mw in self.middlewares:
            request = await mw.pre_process(request)
        return request

    async def run_post(self, response: CompletionResponse) -> CompletionResponse:
        for mw in reversed(self.middlewares):
            response = await mw.post_process(response)
        return response
