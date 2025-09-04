import os
import httpx
import uuid
import structlog
from typing import Optional, Dict, Any
from .base import LLMProvider, CompletionRequest, CompletionResponse, Usage, Role

logger = structlog.get_logger()

class GeminiProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    @property
    def provider_name(self) -> str:
        return "gemini"

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        if not self.api_key:
            raise ValueError("Gemini API key not found. Set GEMINI_API_KEY environment variable.")

        # Map messages to Gemini format
        contents = []
        for m in request.messages:
            role = "user" if m.role == Role.USER or m.role == Role.SYSTEM else "model"
            contents.append({
                "role": role,
                "parts": [{"text": m.content}]
            })

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
                "stopSequences": [request.stop] if isinstance(request.stop, str) else request.stop
            }
        }

        # Gemini uses the model name in the URL
        model_id = request.model if "/" in request.model else f"{request.model}"
        url = f"{self.base_url}/{model_id}:generateContent?key={self.api_key}"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
            
            if response.status_code != 200:
                logger.error("gemini_api_error", status_code=response.status_code, body=response.text)
                response.raise_for_status()

            data = response.json()
            
            # Simple result extraction
            candidate = data["candidates"][0]
            text_result = candidate["content"]["parts"][0]["text"]
            
            # Gemini v1beta doesn't always return usage in this specific way, 
            # but let's assume standard response for now or estimate.
            usage_info = data.get("usageMetadata", {})
            
            return CompletionResponse(
                id=f"gemini-{uuid.uuid4()}",
                model=request.model,
                content=text_result,
                role=Role.ASSISTANT,
                usage=Usage(
                    prompt_tokens=usage_info.get("promptTokenCount", 0),
                    completion_tokens=usage_info.get("candidatesTokenCount", 0),
                    total_tokens=usage_info.get("totalTokenCount", 0)
                ),
                finish_reason=candidate.get("finishReason"),
                provider_metadata={"safety_ratings": candidate.get("safetyRatings")}
            )
