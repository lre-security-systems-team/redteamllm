import json
from typing import Optional
from pathlib import Path
class Config:
    def __init__(self):
        # locate config.json *next to* this file
        config_path = Path(__file__).parent / "config.json"
        if not config_path.exists():
            raise FileNotFoundError(f"Could not find config.json at {config_path!r}")
        with config_path.open(encoding="utf-8") as f:
            self.data:dict = json.load(f)

        self.base_prompt : Optional[str] = self.data.get("base_system_prompt")
        self.act_system_prompt : Optional[str] = self.data.get("act_system_prompt")
        self.reason_system_prompt : Optional[str] = self.data.get("reason_system_prompt")
        self.summarizer_system_prompt : Optional[str] = self.data.get("summarizer_system_prompt")
        self.planner_system_prompt : Optional[str] = self.data.get("planner_system_prompt")
        self.reason_time : int = self.data.get("reason_time")
        self.activate_summary : bool  = self.data.get("activate_summary")
        self.model_name: str = self.data.get("model_name")
        self.api_key:str = self.data.get("api_key")

        if self.base_prompt is None or self.act_system_prompt is None or self.reason_system_prompt is None or self.summarizer_system_prompt is None or self.planner_system_prompt is None or self.reason_time is None or self.activate_summary is None or self.model_name is None or self.api_key is None:
            raise Exception("Configuration needs to include all fields")
        

configuration = Config()