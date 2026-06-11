# /mnt/i/workspaces/llm/retrieval/model_client.py

from pathlib import Path
import yaml
import httpx
from typing import NamedTuple, Optional
from schemas import TOPIC_FORMAT_SCHEMA

def load_config(path: Path | str) -> dict:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file {path} does not exist")
    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    resolved = {}
    for role, model_name in raw["roles"].items():
        if model_name not in raw["models"]:
            raise KeyError(f"Role '{role}' references undefined model '{model_name}'")
        resolved[role] = raw["models"][model_name]
    return resolved


class ChatResult(NamedTuple):
    content: str
    model: str
    prompt_tokens: int
    eval_count: int


class ModelClient:
    def __init__(self, config: dict):
        self.config = config

    def embed_dim(self, role: str) -> int:
        try:
            return self.config[role]["embed_dim"]
        except KeyError as e:
            raise KeyError(f"Role '{role}' not found in config") from e

    def _post_embed_request(self, url: str, payload: dict) -> httpx.Response:
        return httpx.post(url, json=payload, timeout=120.0)

    def embed_texts(self, texts: list[str], role: str) -> list[list[float]]:
        role_config = self.config[role]
        url = f"{role_config['address']}/api/embed"
        payload = {"model": role_config["model"], "input": texts}
        
        try:
            response = self._post_embed_request(url, payload)
            response.raise_for_status()
        except httpx.ConnectError as e:
            raise e
        
        embeddings = response.json().get("embeddings")
        if not isinstance(embeddings, list):
            raise ValueError("Invalid response format: 'embeddings' key missing or not a list")
        
        embed_dim = self.embed_dim(role)
        for vector in embeddings:
            if len(vector) != embed_dim:
                raise ValueError(f"Vector length {len(vector)} does not match expected dimension {embed_dim}")
        
        return embeddings

    def _chat(self, prompt: str, model_config: dict, schema: Optional[dict] = None, timeout: Optional[float] = None) -> ChatResult:
        payload = {
            "model": model_config["model"],
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": model_config.get("options", {})
        }
        
        if schema is not None:
            payload["format"] = schema
        
        if "think" in model_config:
            payload["think"] = model_config["think"]
        
        effective_timeout = timeout if timeout is not None else model_config.get("timeout_s", 120)
        url = f'{model_config["address"]}/api/chat'
        
        resp = httpx.post(url, json=payload, timeout=effective_timeout)
        resp.raise_for_status()
        
        return ChatResult(
            content=resp.json()["message"]["content"],
            model=resp.json().get("model", model_config["model"]),
            prompt_tokens=resp.json().get("prompt_eval_count", 0),
            eval_count=resp.json().get("eval_count", 0)
        )

    def call(self, prompt: str, model_config: dict, schema: Optional[dict] = None, timeout: Optional[float] = None) -> ChatResult:
        return self._chat(prompt, model_config, schema=schema, timeout=timeout)

    def extract_prose(self, prompt: str) -> ChatResult:
        return self._chat(prompt, self.config["extraction_prose"], schema=TOPIC_FORMAT_SCHEMA)

    def extract_code(self, prompt: str) -> ChatResult:
        return self._chat(prompt, self.config["extraction_code"], schema=TOPIC_FORMAT_SCHEMA)
