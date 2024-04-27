# Makefile for Python project to handle testing
.PHONY: install test clean all

# Install dependencies
install:
	pip install -r requirements.txt

# Run tests with PYTHONPATH set
test:
	PYTHONPATH=$(PWD) pytest

# Command to clean up test cache or other temporary files
clean:
	rm -rf .pytest_cache
	rm -rf __pycache__

# Command to run all steps
all: install test clean
