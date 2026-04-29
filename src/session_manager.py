import json
from pathlib import Path
from typing import Dict, List, Optional

class SessionManager:
    SESSION_DIR = Path("config/sessions")

    def __init__(self):
        self.SESSION_DIR.mkdir(parents=True, exist_ok=True)
        self._sessions: Dict[str, List[dict]] = {}

    def load(self, plugin_name: str) -> Optional[List[dict]]:
        path = self.SESSION_DIR / f"{plugin_name}.json"
        if not path.exists():
            return None
        with open(path) as f:
            cookies = json.load(f)
        self._sessions[plugin_name] = cookies
        return cookies

    def get_cookies(self, plugin_name: str) -> Optional[List[dict]]:
        if plugin_name not in self._sessions:
            return self.load(plugin_name)
        return self._sessions[plugin_name]

    def store_credentials(self, plugin_name: str, username: str, password: str) -> None:
        path = self.SESSION_DIR / f"{plugin_name}_creds.json"
        with open(path, 'w') as f:
            json.dump({"username": username, "password": password}, f)

    def get_credentials(self, plugin_name: str) -> Optional[dict]:
        path = self.SESSION_DIR / f"{plugin_name}_creds.json"
        if not path.exists():
            return None
        with open(path) as f:
            return json.load(f)

    def credentials_set(self, plugin_name: str) -> bool:
        return (self.SESSION_DIR / f"{plugin_name}_creds.json").exists()

    def is_authenticated(self, plugin_name: str) -> bool:
        return self.get_cookies(plugin_name) is not None or self.credentials_set(plugin_name)
