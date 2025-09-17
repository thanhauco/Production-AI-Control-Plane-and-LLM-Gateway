from typing import Any, Callable, Dict, Optional, Type
from pydantic import BaseModel, ValidationError
import structlog

logger = structlog.get_logger()

class ValidationGate:
    def __init__(
        self, 
        name: str, 
        model: Optional[Type[BaseModel]] = None,
        validator: Optional[Callable[[Any], bool]] = None
    ):
        self.name = name
        self.model = model
        self.validator = validator

    def validate(self, data: Any) -> bool:
        """Validate data against the gate's rules."""
        logger.info("executing_validation_gate", gate=self.name)
        
        # 1. Type validation if model is provided
        if self.model:
            try:
                if isinstance(data, dict):
                    self.model(**data)
                else:
                    self.model.model_validate(data)
            except (ValidationError, TypeError) as e:
                logger.error("validation_gate_failed", gate=self.name, error=str(e))
                return False

        # 2. Functional validation if validator is provided
        if self.validator:
            try:
                if not self.validator(data):
                    logger.error("validation_gate_function_failed", gate=self.name)
                    return False
            except Exception as e:
                logger.error("validation_gate_exception", gate=self.name, error=str(e))
                return False

        logger.info("validation_gate_passed", gate=self.name)
        return True
