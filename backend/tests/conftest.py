import httpx
import functools

# Monkey-patch httpx.Client.__init__ to fix compatibility with older starlette.testclient
original_init = httpx.Client.__init__

@functools.wraps(original_init)
def patched_init(self, *args, **kwargs):
    if 'app' in kwargs:
        # httpx >= 0.28 removed the 'app' keyword argument in favor of 'transport'
        app = kwargs.pop('app')
        if 'transport' not in kwargs:
            kwargs['transport'] = httpx.ASGITransport(app=app)
    original_init(self, *args, **kwargs)

httpx.Client.__init__ = patched_init

import pytest
from backend.app.api.middleware import copilot_limiter, demo_limiter

@pytest.fixture(autouse=True)
def reset_rate_limiters():
    copilot_limiter._counts.clear()
    demo_limiter._counts.clear()
    yield
