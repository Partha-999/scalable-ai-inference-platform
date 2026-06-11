# Scalable AI Inference Platform

FastAPI + Ray Serve platform for multi-tenant vision and text inference with Redis caching, JWT/API-key auth, rate limiting, Prometheus metrics, Grafana dashboards, and AWS-ready deployment assets.

## Local Run

1. Copy `.env.example` to `.env`.
2. Install dependencies with `pip install -r requirements.txt`.
3. Start the API with `uvicorn app.main:app --reload`.

## Key Endpoints

- `GET /api/v1/health/live`
- `GET /api/v1/health/ready`
- `GET /api/v1/health/metrics`
- `POST /api/v1/auth/token`
- `POST /api/v1/inference/text`
- `POST /api/v1/inference/vision`
- `POST /api/v1/inference/vision/upload`
- `POST /api/v1/inference/batch`
- `GET /api/v1/inference/models`

## Notes

- Models are loaded lazily with TensorFlow/Transformers and fallback heuristics keep the service usable in lightweight environments.
- Ray Serve deployment entrypoint is under `app/deployments/serve_app.py`.
- Monitoring config lives in `configs/` and Kubernetes manifests in `configs/kubernetes/`.

Text Models
Model Type	What it does
Sentiment	Positive/negative sentiment
Topic	Topic classification
Intent	Intent classification
QA (SQuAD)	Extract answers from a provided context
NER	Find people, locations, organizations in text
Text Classification	Generic classification labels

Vision Models
Model Type	What it does
ViT	Image classification
CLIP	Image/text similarity classification
Swin	Image classification
DETR	Object detection