import time
from ray import serve

from app.deployments.serve_app import entrypoint

if __name__ == "__main__":
    serve.start(http_options={"host": "0.0.0.0", "port": 8000})
    serve.run(entrypoint)
    print("Ray Serve started successfully. Streaming logs...", flush=True)
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print("Shutting down Ray Serve...")
        serve.shutdown()
