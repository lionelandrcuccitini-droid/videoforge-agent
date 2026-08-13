.PHONY: install lint test check docker

install:
	python -m pip install -e ".[dev]"

lint:
	ruff check .
	ruff format --check .
	mypy src

test:
	pytest --cov=videoforge_agent --cov-report=term-missing

check: lint test

docker:
	docker build -t videoforge-agent:local .

