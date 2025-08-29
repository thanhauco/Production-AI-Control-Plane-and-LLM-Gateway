import typer
import asyncio
from rich.console import Console
from rich.table import Table
from .gateway.gateway import LLMGateway
from .gateway.providers.mock import MockProvider
from .gateway.providers.base import CompletionRequest, Message, Role
from .gateway.middleware import PIIRedactor, PromptGuard
from .pipeline.engine import stage, Pipeline
from .observability.logging import setup_logging

app = typer.Typer(help="Production AI Control Plane CLI")
console = Console()

@app.command()
def chat(
    message: str = typer.Argument(..., help="Message to send to the LLM"),
    redact: bool = typer.Option(True, help="Enable PII redaction"),
    mock_error: bool = typer.Option(False, help="Simulate a provider error")
):
    """Chat with the LLM Gateway."""
    setup_logging()
    
    async def _chat():
        providers = [
            MockProvider(name="primary", response_content="Hello! My email is test@example.com.")
        ]
        
        middlewares = [PromptGuard()]
        if redact:
            middlewares.append(PIIRedactor())
            
        gateway = LLMGateway(providers=providers, middlewares=middlewares)
        
        request = CompletionRequest(
            model="gpt-4",
            messages=[Message(role=Role.USER, content=message)]
        )
        
        try:
            response = await gateway.complete(request)
            console.print(f"\n[bold green]Response:[/bold green] {response.content}")
            console.print(f"[dim]Usage: {response.usage.total_tokens} tokens[/dim]")
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")

    asyncio.run(_chat())

@app.command()
def run_eval(prompt: str = typer.Argument("Explain production AI.", help="Prompt to evaluate")):
    """Run a sample model evaluation pipeline."""
    setup_logging()
    
    async def _run():
        @stage(name="generate_response")
        async def generate_response(prompt: str):
            gateway = LLMGateway([MockProvider(name="eval-model")])
            req = CompletionRequest(model="eval-model", messages=[Message(role=Role.USER, content=prompt)])
            res = await gateway.complete(req)
            return res.content

        @stage(name="validate_output", depends_on=["generate_response"])
        def validate_output(generate_response: str):
            if len(generate_response) < 10:
                raise ValueError("Response too short")
            return {"valid": True, "length": len(generate_response)}

        p = Pipeline("eval-pipeline")
        p.add_stage(generate_response)
        p.add_stage(validate_output)
        
        run_record = await p.run({"prompt": prompt})
        
        table = Table(title=f"Pipeline Run: {run_record.pipeline_name}")
        table.add_column("Stage")
        table.add_column("Status")
        table.add_column("Output/Error")
        
        for name, res in run_record.results.items():
            status_color = "green" if res.status == "completed" else "red"
            table.add_row(name, f"[{status_color}]{res.status}[/{status_color}]", str(res.output or res.error))
            
        console.print(table)

    asyncio.run(_run())

if __name__ == "__main__":
    app()
