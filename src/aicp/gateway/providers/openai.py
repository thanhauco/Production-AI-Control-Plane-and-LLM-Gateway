import os
import httpx
import uuid
import structlog
from typing import Optional
from .base import LLMProvider, CompletionRequest, CompletionResponse, Usage, Role

logger = structlog.get_logger()

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url

    @property
    def provider_name(self) -> str:
        return "openai"

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": request.model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": request.stream
        }
        
        if request.stop:
            payload["stop"] = request.stop
        
        payload.update(request.extra_params)

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                logger.error("openai_api_error", status_code=response.status_code, body=response.text)
                response.raise_for_status()

            data = response.json()
            choice = data["choices"][0]
            usage_data = data["usage"]

            return CompletionResponse(
                id=data["id"],
                model=data["model"],
                content=choice["message"]["content"],
                role=Role(choice["message"]["role"]),
                usage=Usage(
                    prompt_tokens=usage_data["prompt_tokens"],
                    completion_tokens=usage_data["completion_tokens"],
                    total_tokens=usage_data["total_tokens"]
                ),
                finish_reason=choice.get("finish_reason"),
                provider_metadata={"system_fingerprint": data.get("system_fingerprint")}
            )
