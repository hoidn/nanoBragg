.PHONY: setup format lint test clean

# Python executable
PYTHON := python
VENV_DIR := .venv
PIP := $(VENV_DIR)/bin/pip
PYTHON_VENV := $(VENV_DIR)/bin/python

setup:
	$(PYTHON) -m venv $(VENV_DIR)
	$(PIP) install -r requirements.txt

format:
	$(PYTHON_VENV) -m black src/ tests/
	$(PYTHON_VENV) -m isort src/ tests/

lint: format
	@echo "Code formatting complete"

test:
	$(PYTHON_VENV) -m pytest -q --durations=10

test-verbose:
	$(PYTHON_VENV) -m pytest -v

clean:
	rm -rf $(VENV_DIR)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# C code compilation targets
nanoBragg:
	gcc -O3 -o nanoBragg nanoBragg.c -lm -fopenmp

nonBragg:
	gcc -O3 -o nonBragg nonBragg.c -lm

noisify:
	gcc -O3 -o noisify noisify.c -lm

c-all: nanoBragg nonBragg noisify

# Golden suite generation
golden-suite:
	$(MAKE) -C golden_suite_generator/ all

# Help target
help:
	@echo "Available targets:"
	@echo "  setup         - Create virtual environment and install dependencies"
	@echo "  format        - Format code with black and isort"
	@echo "  lint          - Run code formatting (alias for format)"
	@echo "  test          - Run test suite with pytest"
	@echo "  test-verbose  - Run test suite with verbose output"
	@echo "  clean         - Remove virtual environment and Python cache files"
	@echo "  nanoBragg     - Compile original C nanoBragg simulator"
	@echo "  nonBragg      - Compile nonBragg simulator"
	@echo "  noisify       - Compile noisify utility"
	@echo "  c-all         - Compile all C programs"
	@echo "  golden-suite  - Generate golden test data from C code"