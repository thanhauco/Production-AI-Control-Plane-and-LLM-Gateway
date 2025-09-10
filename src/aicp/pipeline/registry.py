import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class ModelVersion(BaseModel):
    version: str
    provider: str
    model_name: str
    status: str = "staging"  # staging, production, archived
    created_at: datetime = Field(default_factory=datetime.now)
    description: Optional[str] = None
    metadata: Dict[str, str] = Field(default_factory=dict)

class ModelRegistry:
    def __init__(self, storage_path: str = "model_registry.json"):
        self.storage_path = storage_path
        self.models: Dict[str, List[ModelVersion]] = {}
        self._load()

    def _load(self):
        if os.path.exists(self.storage_path):
            with open(self.storage_path, "r") as f:
                data = json.load(f)
                for name, versions in data.items():
                    self.models[name] = [ModelVersion(**v) for v in versions]

    def _save(self):
        data = {name: [v.dict() for v in versions] for name, versions in self.models.items()}
        # Handle datetime serialization
        data_json = json.loads(json.dumps(data, default=str))
        with open(self.storage_path, "w") as f:
            json.dump(data_json, f, indent=2)

    def register(self, name: str, version: str, provider: str, model_name: str, description: Optional[str] = None):
        if name not in self.models:
            self.models[name] = []
        
        new_version = ModelVersion(
            version=version,
            provider=provider,
            model_name=model_name,
            description=description
        )
        self.models[name].append(new_version)
        self._save()
        return new_version

    def promote(self, name: str, version: str):
        if name not in self.models:
            raise KeyError(f"Model {name} not found")
        
        for v in self.models[name]:
            if v.version == version:
                # Demote existing production models
                for other_v in self.models[name]:
                    if other_v.status == "production":
                        other_v.status = "archived"
                v.status = "production"
                self._save()
                return v
        raise ValueError(f"Version {version} not found for model {name}")

    def get_production(self, name: str) -> Optional[ModelVersion]:
        if name not in self.models:
            return None
        for v in self.models[name]:
            if v.status == "production":
                return v
        return None

    def list_models(self) -> Dict[str, List[ModelVersion]]:
        return self.models
