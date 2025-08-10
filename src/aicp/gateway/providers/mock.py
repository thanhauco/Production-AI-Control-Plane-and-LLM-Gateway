import uuid
from .base import LLMProvider, CompletionRequest, CompletionResponse, Usage, Role
import structlog

logger = structlog.get_logger()

class MockProvider(LLMProvider):
    def __init__(self, name: str = "mock-provider", response_content: str = "This is a mock response."):
        self.name = name
        self.response_content = response_content

    @property
    def provider_name(self) -> str:
        return self.name

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        # Log the received messages to verify middleware redaction
        for msg in request.messages:
            logger.info("mock_provider_received", role=msg.role, content=msg.content)

        # Simulate local latency if needed
        content = f"{self.response_content}"
        
        # Calculate mock usage
        prompt_len = sum(len(m.content) for m in request.messages)
        completion_len = len(content)
        
        return CompletionResponse(
            id=f"mock-{uuid.uuid4()}",
            model=request.model,
            content=content,
            role=Role.ASSISTANT,
            usage=Usage(
                prompt_tokens=prompt_len // 4,  # Rough token estimate
                completion_tokens=completion_len // 4,
                total_tokens=(prompt_len + completion_len) // 4
            ),
            provider_metadata={"mock": True}
        )
