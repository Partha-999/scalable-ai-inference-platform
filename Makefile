.PHONY: install run test lint docker-up docker-down

install:
	pip install -r requirements.txt

run:
	python -m scripts.start_ray_serve

test:
	pytest -q

lint:
	python -m compileall app

docker-up:
	docker compose up --build

docker-down:
	docker compose down -v
