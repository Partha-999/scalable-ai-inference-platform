from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

REQUEST_COUNT = Counter("ai_platform_requests_total", "Total requests", ["route", "method", "status"])
REQUEST_LATENCY = Histogram("ai_platform_request_latency_seconds", "Request latency", ["route", "method"])
INFERENCE_LATENCY = Histogram("ai_platform_inference_latency_seconds", "Inference latency", ["model_id", "task"])
CACHE_HIT_RATE = Counter("ai_platform_cache_hits_total", "Cache hits", ["cache_name"])
RATE_LIMIT_REJECTIONS = Counter("ai_platform_rate_limit_rejections_total", "Rate limited requests", ["tenant_id"])
ACTIVE_REQUESTS = Gauge("ai_platform_active_requests", "Active in-flight requests")
MODEL_LOAD_STATUS = Gauge("ai_platform_model_load_status", "Model load status", ["model_id", "status"])
