import typer
import asyncio
from rich.console import Console
from rich.table import Table
from .gateway.gateway import LLMGateway
from .gateway.providers.mock import MockProvider
from .gateway.providers.openai import OpenAIProvider
from .gateway.providers.gemini import GeminiProvider
from .gateway.providers.base import CompletionRequest, Message, Role
from .gateway.middleware import PIIRedactor, PromptGuard
from .pipeline.engine import stage, Pipeline
from .pipeline.registry import ModelRegistry
from .observability.logging import setup_logging

app = typer.Typer(help="Production AI Control Plane CLI")
console = Console()

@app.command()
def chat(
    message: str = typer.Argument(..., help="Message to send to the LLM"),
    provider: str = typer.Option("mock", help="Provider to use: mock, openai, gemini"),
    model: str = typer.Option("gpt-4", help="Model name to use"),
    redact: bool = typer.Option(True, help="Enable PII redaction")
):
    """Chat with the LLM Gateway."""
    setup_logging()
    
    async def _chat():
        if provider == "openai":
            providers = [OpenAIProvider()]
        elif provider == "gemini":
            providers = [GeminiProvider()]
        else:
            providers = [MockProvider(name="mock", response_content="Hello! My email is test@example.com.")]
        
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

# Registry Commands
registry_app = typer.Typer(help="Manage the Model Registry")
app.add_typer(registry_app, name="registry")

@registry_app.command("list")
def list_models():
    """List all models in the registry."""
    registry = ModelRegistry()
    models = registry.list_models()
    
    table = Table(title="Model Registry")
    table.add_column("Name")
    table.add_column("Version")
    table.add_column("Provider")
    table.add_column("Model Name")
    table.add_column("Status")
    
    for name, versions in models.items():
        for v in versions:
            status_style = "bold green" if v.status == "production" else "dim blue"
            table.add_row(name, v.version, v.provider, v.model_name, f"[{status_style}]{v.status}[/{status_style}]")
    
    console.print(table)

@registry_app.command("register")
def register_model(
    name: str = typer.Argument(..., help="Friendly name of the model"),
    version: str = typer.Argument(..., help="Version string (e.g. 1.0.0)"),
    provider: str = typer.Argument(..., help="Provider name (openai, gemini, mock)"),
    model_name: str = typer.Argument(..., help="Actual model ID (e.g. gpt-4o)"),
    description: str = typer.Option(None, help="Optional description")
):
    """Register a new model version."""
    registry = ModelRegistry()
    v = registry.register(name, version, provider, model_name, description)
    console.print(f"[green]Registered {name} version {v.version}[/green]")

@registry_app.command("promote")
def promote_model(
    name: str = typer.Argument(..., help="Friendly name of the model"),
    version: str = typer.Argument(..., help="Version to promote to production")
):
    """Promote a model version to production."""
    registry = ModelRegistry()
    try:
        v = registry.promote(name, version)
        console.print(f"[bold green]Promoted {name} v{v.version} to production![/bold green]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")

if __name__ == "__main__":
    app()
