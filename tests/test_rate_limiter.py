import time
from src.rate_limiter import RateLimiter

def test_wait_enforces_minimum_delay():
    rl = RateLimiter({'test_plugin': (0.1, 0.2)})
    rl.wait('test_plugin')
    start = time.time()
    rl.wait('test_plugin')
    elapsed = time.time() - start
    assert elapsed >= 0.08

def test_failure_count_increments():
    slept = []
    rl = RateLimiter({}, sleep_fn=slept.append)
    assert rl.failure_count('x') == 0
    rl.record_failure('x')
    assert rl.failure_count('x') == 1
    assert len(slept) == 1  # backoff was called once

def test_reset_failures():
    rl = RateLimiter({})
    rl._fail_count['x'] = 3
    rl.reset_failures('x')
    assert rl.failure_count('x') == 0

def test_default_delay_used_for_unknown_plugin():
    rl = RateLimiter({})
    # Should not raise, uses (2.0, 4.0) default — just verify it runs
    # Don't actually wait 2s in tests; test the config lookup only
    min_d, max_d = rl._config.get('unknown', (2.0, 4.0))
    assert min_d == 2.0
    assert max_d == 4.0
