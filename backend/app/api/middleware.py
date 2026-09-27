import os
import time
import uuid
import re
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Cache control for API endpoints
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"

        # HSTS - only emit if served over HTTPS or explicitly configured
        proto = request.headers.get("x-forwarded-proto", "")
        if proto == "https" or os.environ.get("REQUIRE_HTTPS", "").lower() == "true":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # We omit CSP here as the backend serves only JSON API responses,
        # so broad CSP headers are unnecessary for API routes.

        return response

class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-ID")
        # Sanitize and bound length
        if not req_id or not re.match(r'^[\w\-]{1,64}$', req_id):
            req_id = str(uuid.uuid4())

        request.state.request_id = req_id

        from backend.app.core.logging import request_id_ctx_var
        token = request_id_ctx_var.set(req_id)

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = req_id
            return response
        finally:
            request_id_ctx_var.reset(token)

class RequestSizeMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_upload_size: int = 102400): # Default 100KB is plenty for signals (2000 chars), copilot (1000 chars), demo (50)
        super().__init__(app)
        self.max_upload_size = int(os.environ.get("REQUEST_SIZE_LIMIT_BYTES", str(max_upload_size)))

    async def dispatch(self, request: Request, call_next):
        if request.method == "POST":
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.max_upload_size:
                return JSONResponse(status_code=413, content={"detail": "Payload Too Large"})
        return await call_next(request)

class RateLimiter:
    """
    In-process, bounded-memory rate limiter.
    Not distributed. State resets on restart.
    """
    def __init__(self, limit: int, window: int):
        self.limit = limit
        self.window = window
        self._counts = {}

    def __call__(self, request: Request):
        try:
            now = time.time()

            # Simple bounded memory
            if len(self._counts) > 5000:
                to_delete = []
                for ip, times in list(self._counts.items()):
                    valid_times = [t for t in times if now - t < self.window]
                    if not valid_times:
                        to_delete.append(ip)
                    else:
                        self._counts[ip] = valid_times
                for ip in to_delete:
                    del self._counts[ip]
                # Fallback to prevent exhaustion
                if len(self._counts) > 10000:
                    self._counts.clear()

            ip = request.client.host if request.client else "127.0.0.1"
            ip = request.headers.get("x-forwarded-for", ip).split(",")[0].strip()

            times = self._counts.get(ip, [])
            valid_times = [t for t in times if now - t < self.window]

            if len(valid_times) >= self.limit:
                oldest = valid_times[0]
                retry_after = int(self.window - (now - oldest))
                if retry_after < 0: retry_after = 0
                raise HTTPException(
                    status_code=429,
                    detail="Too Many Requests",
                    headers={"Retry-After": str(retry_after)}
                )

            valid_times.append(now)
            self._counts[ip] = valid_times

        except HTTPException:
            raise
        except Exception:
            # Fail closed on internal problem
            raise HTTPException(status_code=500, detail="Rate limiter internal error")

COPILOT_LIMIT = int(os.environ.get("RATE_LIMIT_COPILOT", "5"))
COPILOT_WINDOW = int(os.environ.get("RATE_LIMIT_WINDOW_COPILOT", "60"))

DEMO_LIMIT = int(os.environ.get("RATE_LIMIT_DEMO", "2"))
DEMO_WINDOW = int(os.environ.get("RATE_LIMIT_WINDOW_DEMO", "60"))

# Increase limits significantly during testing to avoid order-dependent failures
# (Removed, tests now clear limiters globally in conftest.py)

copilot_limiter = RateLimiter(limit=COPILOT_LIMIT, window=COPILOT_WINDOW)
demo_limiter = RateLimiter(limit=DEMO_LIMIT, window=DEMO_WINDOW)
