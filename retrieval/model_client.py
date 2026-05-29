# /mnt/i/workspaces/llm/retrieval/model_client.py

from pathlib import Path
import yaml
import httpx

def load_config(path: Path | str) -> dict:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file {path} does not exist")
    
    with path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    if "roles" not in config:
        raise ValueError("Config must contain a top-level 'roles' key")
    
    return config["roles"]


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
