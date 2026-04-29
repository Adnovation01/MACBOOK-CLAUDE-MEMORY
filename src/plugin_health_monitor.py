import json
import os
import concurrent.futures
from datetime import datetime, timezone
from typing import Dict, List

from src.plugins.base_plugin import BasePlugin

CACHE_TTL_SECONDS = 300


class PluginHealthMonitor:
    def __init__(self, plugins: List[BasePlugin], cache_path: str = "data/plugin_health.json"):
        self._plugins: Dict[str, BasePlugin] = {p.name: p for p in plugins}
        self._cache_path = cache_path
        self._cache: Dict[str, dict] = self._load_cache()

    def _load_cache(self) -> Dict[str, dict]:
        if os.path.exists(self._cache_path):
            try:
                with open(self._cache_path) as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_cache(self):
        os.makedirs(os.path.dirname(self._cache_path) or ".", exist_ok=True)
        with open(self._cache_path, "w") as f:
            json.dump(self._cache, f, indent=2)

    def _is_fresh(self, entry: dict) -> bool:
        checked_at = entry.get("checked_at")
        if not checked_at:
            return False
        try:
            checked = datetime.fromisoformat(checked_at)
            if checked.tzinfo is None:
                checked = checked.replace(tzinfo=timezone.utc)
            age = (datetime.now(timezone.utc) - checked).total_seconds()
            return age < CACHE_TTL_SECONDS
        except Exception:
            return False

    def _record(self, name: str, result: dict):
        self._cache[name] = {
            "status": result["status"],
            "error": result.get("error"),
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    def run_lightweight_check(self) -> Dict[str, dict]:
        for name, plugin in self._plugins.items():
            if name in self._cache and self._is_fresh(self._cache[name]):
                continue
            try:
                result = plugin.health_check()
            except Exception as e:
                result = {"status": "failed", "error": str(e)[:120]}
            self._record(name, result)
        self._save_cache()
        return self._cache

    def run_full_probe(self) -> Dict[str, dict]:
        def probe(name: str, plugin: BasePlugin):
            try:
                leads = plugin.search("dentist", "New York", 1)
                if leads:
                    return name, {"status": "healthy", "error": None}
                return name, {"status": "failed", "error": "returned 0 results"}
            except Exception as e:
                return name, {"status": "failed", "error": str(e)[:120]}

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self._plugins)) as ex:
            futures = {ex.submit(probe, n, p): n for n, p in self._plugins.items()}
            for future in concurrent.futures.as_completed(futures, timeout=35):
                try:
                    name, result = future.result()
                    self._record(name, result)
                except Exception:
                    pass
        self._save_cache()
        return self._cache

    def get_status(self) -> Dict[str, dict]:
        return dict(self._cache)

    def get_healthy_plugin_names(self) -> List[str]:
        return [
            name for name, entry in self._cache.items()
            if entry.get("status") == "healthy"
        ]

    def get_summary(self) -> Dict[str, int]:
        counts: Dict[str, int] = {"healthy": 0, "degraded": 0, "failed": 0, "unknown": 0}
        for name in self._plugins:
            entry = self._cache.get(name)
            status = entry["status"] if entry else "unknown"
            counts[status] = counts.get(status, 0) + 1
        return counts
