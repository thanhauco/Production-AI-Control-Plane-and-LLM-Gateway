from typing import Any, Dict, List, Optional, Callable, Union
from pydantic import BaseModel, Field
from enum import Enum
import uuid
from datetime import datetime

class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class StageResult(BaseModel):
    stage_id: str
    status: StageStatus
    output: Any = None
    error: Optional[str] = None
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class PipelineRun(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pipeline_name: str
    status: StageStatus = StageStatus.PENDING
    results: Dict[str, StageResult] = Field(default_factory=dict)
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
