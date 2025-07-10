# TrackLab Development Makefile

.PHONY: help install install-dev test test-unit test-integration test-functional test-system lint format mypy clean build serve docs

help:  ## Show this help message
	@echo "TrackLab Development Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install tracklab in development mode
	pip install -e .

install-dev:  ## Install development dependencies
	pip install -e ".[dev]"
	pip install -r requirements_dev.txt
	pip install -r requirements_test.txt

test:  ## Run all tests
	nox -s tests

test-unit:  ## Run unit tests
	nox -s unit_tests

test-integration:  ## Run integration tests
	nox -s integration_tests

test-functional:  ## Run functional tests
	nox -s functional_tests

test-system:  ## Run system tests
	nox -s system_tests

lint:  ## Run linting
	nox -s lint

format:  ## Format code
	nox -s format

mypy:  ## Run type checking
	nox -s mypy

clean:  ## Clean build artifacts
	nox -s clean

build:  ## Build the package
	nox -s build

serve:  ## Start development server
	nox -s serve

coverage:  ## Generate coverage report
	nox -s coverage

# Direct pytest commands for faster iteration
pytest-unit:  ## Run unit tests with pytest (faster)
	pytest tests/unit_tests/ -v

pytest-integration:  ## Run integration tests with pytest (faster)
	pytest tests/integration_tests/ -v

pytest-functional:  ## Run functional tests with pytest (faster)
	pytest tests/functional_tests/ -v

pytest-system:  ## Run system tests with pytest (faster)
	pytest tests/system_tests/ -v

pytest-all:  ## Run all tests with pytest (faster)
	pytest tests/ -v

# Development shortcuts
dev-setup:  ## Complete development setup
	$(MAKE) install-dev
	$(MAKE) format
	$(MAKE) test-unit

quick-test:  ## Run quick tests for development
	pytest tests/unit_tests/ -x -q

# Frontend
frontend:  ## Build frontend assets
	cd frontend && npm install && npm run build
	cp -r frontend/dist/* tracklab/backend/server/static/

# Documentation
docs:  ## Generate documentation
	@echo "Documentation generation not yet implemented"

# Release
release-check:  ## Check if ready for release
	$(MAKE) clean
	$(MAKE) lint
	$(MAKE) mypy
	$(MAKE) test
	$(MAKE) build

upload:  ## Upload package to PyPI
	python -m twine upload dist/*

# Docker commands (future)
docker-build:  ## Build Docker image
	@echo "Docker build not yet implemented"

docker-run:  ## Run Docker container
	@echo "Docker run not yet implemented"