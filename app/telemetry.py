"""Telemetry middleware for tracking per-endpoint request metrics."""

import time
from collections import defaultdict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

metrics_store: dict = {
    "endpoints": defaultdict(lambda: {
        "request_count": 0,
        "total_response_time": 0.0,
        "error_count": 0,
        "status_codes": defaultdict(int),
    })
}


class TelemetryMiddleware(BaseHTTPMiddleware):
    """Middleware that intercepts every request to collect timing and error metrics."""

    async def dispatch(self, request: Request, call_next) -> Response:
        endpoint = f"{request.method} {request.url.path}"
        start_time = time.time()

        try:
            response: Response = await call_next(request)
        except Exception as exc:
            duration = time.time() - start_time
            metrics = metrics_store["endpoints"][endpoint]
            metrics["request_count"] += 1
            metrics["total_response_time"] += duration
            metrics["error_count"] += 1
            metrics["status_codes"]["500"] += 1
            raise exc

        duration = time.time() - start_time
        metrics = metrics_store["endpoints"][endpoint]
        metrics["request_count"] += 1
        metrics["total_response_time"] += duration
        metrics["status_codes"][str(response.status_code)] += 1
        if response.status_code >= 400:
            metrics["error_count"] += 1

        return response


def get_metrics() -> dict:
    """Compute aggregated metrics from the in-memory store."""
    result: dict = {}
    for endpoint, data in metrics_store["endpoints"].items():
        count: int = data["request_count"]
        result[endpoint] = {
            "request_count": count,
            "average_response_time": round(data["total_response_time"] / count, 4) if count > 0 else 0,
            "error_count": data["error_count"],
            "error_rate": round(data["error_count"] / count, 4) if count > 0 else 0,
            "status_codes": dict(data["status_codes"]),
        }
    return result
