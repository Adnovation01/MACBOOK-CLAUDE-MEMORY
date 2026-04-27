import time
import random
from typing import Callable, Dict, Tuple

class RateLimiter:
    def __init__(self, config: Dict[str, Tuple[float, float]], sleep_fn: Callable[[float], None] = time.sleep):
        self._config = config
        self._last_call: Dict[str, float] = {}
        self._fail_count: Dict[str, int] = {}
        self._sleep = sleep_fn

    def wait(self, plugin_name: str):
        min_d, max_d = self._config.get(plugin_name, (2.0, 4.0))
        delay = random.uniform(min_d, max_d)
        last = self._last_call.get(plugin_name, 0)
        elapsed = time.time() - last
        if elapsed < delay:
            self._sleep(delay - elapsed)
        self._last_call[plugin_name] = time.time()

    def record_failure(self, plugin_name: str):
        self._fail_count[plugin_name] = self._fail_count.get(plugin_name, 0) + 1
        backoff = min(2 ** self._fail_count[plugin_name], 60)
        self._sleep(backoff)

    def failure_count(self, plugin_name: str) -> int:
        return self._fail_count.get(plugin_name, 0)

    def reset_failures(self, plugin_name: str):
        self._fail_count[plugin_name] = 0
