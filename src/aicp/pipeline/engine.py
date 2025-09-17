import asyncio
import functools
import inspect
from typing import Any, Callable, Dict, List, Optional, Type
from .models import PipelineRun, StageResult, StageStatus
from .validation import ValidationGate
from datetime import datetime
import structlog

logger = structlog.get_logger()

class Stage:
    def __init__(
        self, 
        func: Callable, 
        name: Optional[str] = None, 
        depends_on: Optional[List[str]] = None,
        gate: Optional[ValidationGate] = None,
        retries: int = 0
    ):
        self.func = func
        self.name = name or func.__name__
        self.depends_on = depends_on or []
        self.gate = gate
        self.retries = retries

    async def run(self, context: Dict[str, Any]) -> StageResult:
        result = StageResult(stage_id=self.name, status=StageStatus.RUNNING)
        last_error = None
        
        for attempt in range(self.retries + 1):
            try:
                if attempt > 0:
                    logger.info("retrying_stage", stage=self.name, attempt=attempt)
                
                # Inject context variables as arguments if they match
                sig = inspect.signature(self.func)
                kwargs = {k: context[k] for k in sig.parameters if k in context}
                
                if asyncio.iscoroutinefunction(self.func):
                    output = await self.func(**kwargs)
                else:
                    output = self.func(**kwargs)
                
                # Run validation gate if present
                if self.gate and not self.gate.validate(output):
                    raise ValueError(f"Validation failed at gate: {self.gate.name}")

                result.output = output
                result.status = StageStatus.COMPLETED
                result.end_time = datetime.now()
                return result
            except Exception as e:
                logger.error("stage_failed", stage=self.name, error=str(e), attempt=attempt)
                last_error = e
                if attempt < self.retries:
                    await asyncio.sleep(1.0 * (2 ** attempt)) # Backoff

        result.error = str(last_error)
        result.status = StageStatus.FAILED
        result.end_time = datetime.now()
        return result

class Pipeline:
    def __init__(self, name: str):
        self.name = name
        self.stages: Dict[str, Stage] = {}

    def add_stage(self, stage: Stage):
        self.stages[stage.name] = stage

    async def run(self, initial_context: Optional[Dict[str, Any]] = None) -> PipelineRun:
        run = PipelineRun(pipeline_name=self.name)
        context = (initial_context or {}).copy()
        
        logger.info("pipeline_started", pipeline=self.name, run_id=run.run_id)
        run.status = StageStatus.RUNNING
        
        # Simple topological sort/sequential execution for MVP
        # In a real system, we'd use a graph to determine parallel execution
        executed = set()
        
        while len(executed) < len(self.stages):
            ready = [
                s for name, s in self.stages.items() 
                if name not in executed and all(dep in executed for dep in s.depends_on)
            ]
            
            if not ready:
                if len(executed) < len(self.stages):
                    run.status = StageStatus.FAILED
                    logger.error("pipeline_deadlock", executed=list(executed))
                    break
                break

            # Execute ready stages (sequential for now)
            for stage in ready:
                stage_result = await stage.run(context)
                run.results[stage.name] = stage_result
                executed.add(stage.name)
                
                if stage_result.status == StageStatus.FAILED:
                    run.status = StageStatus.FAILED
                    logger.error("pipeline_aborted", stage=stage.name)
                    run.end_time = datetime.now()
                    return run
                
                # Update context with output
                if stage_result.output is not None:
                    context[stage.name] = stage_result.output

        run.status = StageStatus.COMPLETED
        run.end_time = datetime.now()
        logger.info("pipeline_completed", pipeline=self.name, run_id=run.run_id)
        return run

# Decorators
def stage(
    name: Optional[str] = None, 
    depends_on: Optional[List[str]] = None,
    gate: Optional[ValidationGate] = None,
    retries: int = 0
):
    def decorator(func):
        return Stage(func, name=name, depends_on=depends_on, gate=gate, retries=retries)
    return decorator

def pipeline(name: str):
    def decorator(func):
        # This is a bit of a trick: the function being decorated 
        # defines the stages, and return a Pipeline object.
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            p = Pipeline(name)
            # Find all stages in the local scope of the function? 
            # Better to let the user explicitely add them or use a registry.
            # For this MVP, we'll assume the function returns a list of stages.
            stages = func(*args, **kwargs)
            for s in stages:
                p.add_stage(s)
            return p
        return wrapper
    return decorator
