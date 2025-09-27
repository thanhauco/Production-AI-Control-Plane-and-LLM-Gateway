import asyncio
from aicp.gateway.gateway import LLMGateway
from aicp.gateway.providers.mock import MockProvider
from aicp.pipeline.engine import stage, Pipeline
from aicp.pipeline.validation import ValidationGate
from aicp.observability.logging import setup_logging
from aicp.observability.tracing import setup_tracing
from pydantic import BaseModel

class SummaryModel(BaseModel):
    summary: str
    word_count: int

def validate_length(data: SummaryModel):
    return data.word_count > 2

async def main():
    setup_logging()
    setup_tracing("example-service")
    
    # 1. Define a validation gate
    gate = ValidationGate(
        name="summary_quality",
        model=SummaryModel,
        validator=validate_length
    )

    # 2. Define stages with gates and retries
    @stage(name="summarize", gate=gate, retries=1)
    async def summarize(text: str):
        # Simulating a model that returns a structured dict
        return {
            "summary": "This is a summary of production AI constraints.",
            "word_count": 8
        }

    @stage(name="finalize", depends_on=["summarize"])
    def finalize(summarize: dict):
        return f"Final Report: {summarize['summary']}"

    # 3. Assemble and run
    p = Pipeline("production_report")
    p.add_stage(summarize)
    p.add_stage(finalize)
    
    print("--- Running Pipeline with Tracing & Validation ---")
    result = await p.run({"text": "Production AI is hard."})
    
    for name, res in result.results.items():
        print(f"Stage: {name}, Status: {res.status}, Output: {res.output}")

if __name__ == "__main__":
    asyncio.run(main())
