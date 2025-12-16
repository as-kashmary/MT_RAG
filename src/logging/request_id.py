# middleware/request_id.py
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

from src.logging.logging import set_request_id


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Try to read incoming request id
        incoming_request_id = request.headers.get("X-Request-ID")

        # Always ensure a valid request id exists
        request_id = set_request_id(incoming_request_id)

        response = await call_next(request)

        # Headers MUST be strings
        response.headers["X-Request-ID"] = request_id
        return response
