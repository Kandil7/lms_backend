from __future__ import annotations

import json

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class ResponseEnvelopeMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        success_message: str = "Success",
        excluded_paths: list[str] | None = None,
    ) -> None:
        super().__init__(app)
        self.success_message = success_message
        self.excluded_paths = excluded_paths or []

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        if self._is_excluded(request.url.path):
            return response
        if response.status_code >= 400 or response.status_code == 204:
            return response
        if request.method.upper() == "HEAD":
            return response

        content_type = response.headers.get("content-type", "").lower()
        if "application/json" not in content_type:
            return response

        payload = await self._extract_json_payload(response)
        if payload is None:
            return response
        if self._already_enveloped(payload):
            return response

        wrapped = {
            "success": True,
            "data": payload,
            "message": self.success_message,
        }
        new_response = JSONResponse(status_code=response.status_code, content=wrapped)
        for key, value in response.headers.items():
            normalized = key.lower()
            if normalized in {"content-length", "content-type"}:
                continue
            new_response.headers[key] = value
        new_response.background = response.background
        return new_response

    def _is_excluded(self, path: str) -> bool:
        return any(path == excluded or path.startswith(f"{excluded}/") for excluded in self.excluded_paths)

    @staticmethod
    async def _extract_json_payload(response: Response):
        body = getattr(response, "body", None)
        if body is None:
            chunks = []
            async for chunk in response.body_iterator:
                chunks.append(chunk)
            body = b"".join(chunks)
        if not body:
            return None

        try:
            return json.loads(body.decode("utf-8"))
        except Exception:
            return None

    @staticmethod
    def _already_enveloped(payload) -> bool:
        if not isinstance(payload, dict):
            return False
        return {"success", "data", "message"}.issubset(payload.keys())

