.PHONY: help check check-fix test lint coverage clean install

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

check:  ## Run all quality checks (linting, tests, coverage, complexity)
	@echo "Activating virtual environment and installing dependencies..."
	@source .venv/bin/activate && make install
	python scripts/quality_check.py --all

check-fix:  ## Auto-fix issues then run quality checks
	@echo "Activating virtual environment and installing dependencies..."
	@source .venv/bin/activate && make install
	python scripts/quality_check.py --all --fix

test:  ## Run tests with coverage
	@echo "Activating virtual environment and installing dependencies..."
	@source .venv/bin/activate && make install
	python -m pytest tests/ --cov=scripts --cov=tests --cov-report=term-missing -v

lint:  ## Run linting checks only
	@echo "Activating virtual environment and installing dependencies..."
	@source .venv/bin/activate && make install
	ruff check scripts/ tests/
	ruff format --check scripts/ tests/

lint-fix:  ## Auto-fix linting issues
	@echo "Activating virtual environment and installing dependencies..."
	@source .venv/bin/activate && make install
	ruff check --fix scripts/ tests/
	ruff format scripts/ tests/

coverage:  ## Generate coverage report
	@echo "Activating virtual environment and installing dependencies..."
	@source .venv/bin/activate && make install
	python -m pytest tests/ --cov=scripts --cov=tests --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

complexity:  ## Check code complexity
	@echo "Activating virtual environment and installing dependencies..."
	@source .venv/bin/activate && make install
	radon cc scripts/ tests/ -a -nb

clean:  ## Clean up generated files
	rm -rf .coverage htmlcov/ .pytest_cache/ .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete

install:  ## Install dependencies
	@source .venv/bin/activate && pip install -r requirements.txt