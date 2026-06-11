# Scalable AI Inference Platform

Production-grade multi-tenant AI inference platform for serving Vision and NLP models at scale using FastAPI, Ray Serve, Redis, Docker, Kubernetes, and AWS-ready deployment architecture.

Built to demonstrate distributed model serving, intelligent request routing, observability, caching, autoscaling, and cloud-native deployment patterns commonly used in modern AI systems.

---

## Overview

This platform provides a unified API layer for deploying and serving multiple NLP and Computer Vision models through a scalable inference infrastructure.

The system supports:

* Multi-tenant inference workloads
* Dynamic model routing
* Distributed model serving with Ray Serve
* Redis-backed response caching
* JWT and API-Key authentication
* Request rate limiting
* Real-time monitoring and observability
* Kubernetes deployment support
* AWS-ready cloud architecture

---

## Key Features

### AI Model Serving

* 20+ Vision and NLP models
* Lazy model loading
* Dynamic model selection
* Batch inference support
* Text and image inference APIs
* Object detection support
* OCR support

### Scalability

* Ray Serve distributed deployment
* Horizontal autoscaling architecture
* Multi-tenant request isolation
* Redis caching layer
* Stateless API services
* Containerized deployment

### Security

* JWT authentication
* API-Key authentication
* Tenant-aware request handling
* Rate limiting middleware
* Request validation

### Observability

* Prometheus metrics collection
* Grafana dashboards
* Health and readiness probes
* Request latency tracking
* System monitoring

---

## Supported Models

### NLP Models

| Category                 | Capability                               |
| ------------------------ | ---------------------------------------- |
| Sentiment Analysis       | Positive / Negative Classification       |
| Topic Classification     | Topic Detection                          |
| Intent Classification    | User Intent Recognition                  |
| Question Answering       | Context-Aware Answer Extraction          |
| Named Entity Recognition | Person, Organization, Location Detection |
| Text Classification      | General Purpose Classification           |

### Vision Models

| Category                 | Capability                  |
| ------------------------ | --------------------------- |
| Vision Transformer (ViT) | Image Classification        |
| CLIP                     | Image-Text Similarity       |
| Swin Transformer         | Image Classification        |
| OCR                      | Text Extraction from Images |
| DETR                     | Object Detection            |

---

## High-Level Architecture

```text
                    Client Applications
                             │
                             ▼
                    FastAPI Gateway
                             │
            ┌────────────────┴────────────────┐
            │                                 │
            ▼                                 ▼
    Authentication                  Rate Limiting
            │                                 │
            └──────────────┬──────────────────┘
                           ▼
                    Ray Serve Cluster
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
   NLP Models        Vision Models       OCR Models
        │                  │                  │
        └──────────────────┴──────────────────┘
                           │
                           ▼
                      Redis Cache

Monitoring Stack:

Prometheus → Grafana
```

---

## Repository Structure

```text
.
├── app/
│   ├── api/
│   ├── deployments/
│   ├── middleware/
│   ├── monitoring/
│   ├── services/
│   ├── validation/
│   └── tests/
│
├── configs/
│   ├── kubernetes/
│   ├── prometheus.yml
│   └── grafana_dashboard.json
│
├── docs/
│   ├── aws_deployment.md
│   └── ray_serve_architecture.md
│
├── frontend/
│
├── scripts/
│
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## API Endpoints

### Health

```http
GET /api/v1/health/live
GET /api/v1/health/ready
GET /api/v1/health/metrics
```

### Authentication

```http
POST /api/v1/auth/token
```

### Inference

```http
POST /api/v1/inference/text
POST /api/v1/inference/vision
POST /api/v1/inference/vision/upload
POST /api/v1/inference/batch
GET  /api/v1/inference/models
```

---

## Technology Stack

### Backend

* Python
* FastAPI
* Ray Serve
* TensorFlow
* Hugging Face Transformers

### Infrastructure

* Redis
* Docker
* Kubernetes
* AWS

### Monitoring

* Prometheus
* Grafana

### Frontend

* React
* TypeScript
* Vite

---

## Documentation

Detailed architecture and deployment documentation:

* `docs/ray_serve_architecture.md`
* `docs/aws_deployment.md`

---

## Local Development

### Clone Repository

```bash
git clone https://github.com/Partha-999/scalable-ai-inference-platform.git
cd scalable-ai-inference-platform
```

### Setup Environment

```bash
cp .env.example .env
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run API

```bash
uvicorn app.main:app --reload
```

---

## Docker Deployment

```bash
docker-compose up --build
```

---

## Future Enhancements

* GPU-aware autoscaling
* Multi-region deployment
* Model versioning
* Canary model rollouts
* A/B testing framework
* Advanced tracing with OpenTelemetry
* Distributed feature store integration

---

## Author

**Partha Sarathi**

Focused on building scalable systems, distributed infrastructure, search technologies, and AI-powered platforms.
