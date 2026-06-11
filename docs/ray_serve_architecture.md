# Ray Serve Production Architecture Guide

This document outlines the architecture, data flow, scaling mechanics, and model lifecycles of the **AI Inference Platform** migrated to Ray Serve.

---

## 1. Request Flow

When an inference client makes a request to the platform:

```mermaid
sequenceDiagram
    participant Client as Inference Client
    participant Proxy as Ray Serve HTTP Proxy
    participant Actor as Serve Ingress Actor (FastAPI)
    participant Loader as Model Loader Singleton
    participant Cache as Redis Cache
    participant HF as HuggingFace Cache / Local Disk

    Client->>Proxy: POST /api/v1/inference/text (headers & payload)
    Proxy->>Actor: Route HTTP Request
    Actor->>Cache: Check Redis cache key (tenant_id:hash)
    alt Cache HIT
        Cache-->>Actor: Return cached JSON result
        Actor-->>Proxy: HTTP 200 (cached: true)
        Proxy-->>Client: Return predictions
    else Cache MISS
        Actor->>Loader: get_pipeline(model_record)
        alt Pipeline NOT loaded
            Loader->>HF: Fetch model files & weights from cache/disk
            HF-->>Loader: Instantiate Model & Processor
        end
        Loader-->>Actor: Perform PyTorch/TensorFlow Inference
        Actor->>Cache: Save predictions with TTL expiry
        Actor-->>Proxy: HTTP 200 (cached: false)
        Proxy-->>Client: Return predictions
    end
```

1. **HTTP Proxy Router**: Ray Serve runs a lightweight HTTP proxy on port 8000. It receives external requests and routes them to the replica actors of the target deployment.
2. **FastAPI Ingress**: The FastAPI app is mounted inside the `InferencePlatformDeployment` class via `@serve.ingress`. The proxy routes all matching API request paths directly to this deployment class.
3. **In-Flight Queue Management**: Ray Serve buffers incoming requests and balances them across the available replica actors.

---

## 2. Replica Scaling & Load-Based Autoscaling

Autoscaling is configured in [serve_app.py](file:///c:/Users/ASUS/OneDrive/Gitam/Projects/AI%20Inference%20Platform/app/deployments/serve_app.py):

- **Parameters**:
  - `min_replicas = 1`: The cluster maintains at least 1 active actor, avoiding cold-starts for baseline traffic.
  - `max_replicas = 10`: The cluster can scale up to 10 concurrent actor replicas to absorb sudden spikes.
  - `target_ongoing_requests = 5`: The scaling trigger metric.

- **Scaling Trigger**:
  Ray Serve continuously tracks the average number of ongoing requests (processed + queued in-flight queries) across all active replicas.
  - If the average ongoing requests exceed `5.0`, the autoscaler calculates the necessary replicas and provisions new actors.
  - If the traffic drops and the ongoing queue average falls below the threshold, replicas are gradually de-provisioned down to `min_replicas`.

---

## 3. Model Loading Lifecycle

- **Lazy Loading**: Rather than loading all 22 massive deep learning models on startup, model loader keeps them unloaded. The pipelines are initialized *on-demand* during the first client inference request (`get_pipeline`).
* **Cache Eviction**: To prevent cumulative out-of-memory crashes on GPU or RAM, the platform supports resource reclamation. In memory-constrained flows, the validation suite invokes `clear_cache()`, which clears model references, runs `gc.collect()`, and empties PyTorch VRAM.

---

## 4. Cache Strategy

- **Tenant Isolation**: Multi-tenancy cache separation is achieved by generating cache keys that prepend the tenant ID: `inference:{tenant_id}:{modality}:{model_id}:{payload_hash}`.
- **Deduplication**: When duplicate inference requests hit the API within a tenant boundary, the endpoint retrieves the serialized PredictionResponse directly from Redis cache, completely bypassing model loading and execution. This keeps latencies sub-millisecond and prevents CPU spikes under duplicate load patterns.
