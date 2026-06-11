from __future__ import annotations

from ray import serve

from app.main import create_app

fastapi_app = create_app()


@serve.deployment(
    name="ai-inference-platform",
    num_replicas="auto",
    autoscaling_config={
        "min_replicas": 1,
        "initial_replicas": 1,
        "max_replicas": 10,
        "target_ongoing_requests": 5,
    },
    max_ongoing_requests=256,
    ray_actor_options={"num_cpus": 1},
)
@serve.ingress(fastapi_app)
class InferencePlatformDeployment:
    pass


entrypoint = InferencePlatformDeployment.bind()
