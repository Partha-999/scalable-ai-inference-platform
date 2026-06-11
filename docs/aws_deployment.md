# AWS Deployment

## Reference Architecture

- **Ingress**: Application Load Balancer or API Gateway.
- **Compute**: Amazon EKS for FastAPI + Ray Serve pods, or ECS/Fargate for smaller footprints.
- **Cache**: ElastiCache Redis for request caching and rate limiting.
- **Artifacts**: ECR for container images and S3 for model artifacts.
- **Secrets**: AWS Secrets Manager or Parameter Store.
- **Observability**: CloudWatch logs, Prometheus, Grafana, and optional OpenTelemetry export.

## Rollout Notes

- Keep model loading lazy and tenant-scoped.
- Use HPA against CPU, memory, and custom Ray / request metrics.
- Store JWT secrets and API keys outside the container image.
- Pin image tags and use blue/green or canary deployments for model updates.
