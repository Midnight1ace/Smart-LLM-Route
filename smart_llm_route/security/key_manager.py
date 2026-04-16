import os
from typing import Optional, Dict
from pathlib import Path
import json

class KeyManager:
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or ".llm_keys.json"
        self._keys: Dict[str, str] = {}
        self._load_keys()

    def _load_keys(self):
        path = Path(self.storage_path)
        if path.exists():
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    self._keys = data.get('keys', {})
            except:
                self._keys = {}

    def _save_keys(self):
        with open(self.storage_path, 'w') as f:
            json.dump({'keys': self._keys}, f)

    def get_key(self, provider: str) -> Optional[str]:
        key = os.getenv(f"{provider.upper()}_API_KEY")
        if key:
            return key
        
        return self._keys.get(provider)

    def set_key(self, provider: str, key: str):
        self._keys[provider] = key
        self._save_keys()

    def has_key(self, provider: str) -> bool:
        if os.getenv(f"{provider.upper()}_API_KEY"):
            return True
        return provider in self._keys

    def remove_key(self, provider: str):
        if provider in self._keys:
            del self._keys[provider]
            self._save_keys()

    def list_providers(self) -> list:
        providers = set()
        for key in os.environ:
            if key.endswith('_API_KEY') and os.environ[key]:
                providers.add(key.replace('_API_KEY', '').lower())
        providers.update(self._keys.keys())
        return list(providers)