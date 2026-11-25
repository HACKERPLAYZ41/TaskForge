.PHONY: help install analyze generate validate evaluate report rebuild demo clean

help:
	@echo "TaskForge: Coding Task Factory for Harbor Framework"
	@echo "Commands:"
	@echo "  make install    - Install Python virtual environment and dependencies"
	@echo "  make analyze    - Analyze target codebase (AST, LOC, dependencies)"
	@echo "  make generate   - Generate feature tasks in Harbor format"
	@echo "  make validate   - Execute validation gates (G1 - G7)"
	@echo "  make evaluate   - Evaluate tasks across model tiers"
	@echo "  make report     - Build static HTML report and CLI summary"
	@echo "  make rebuild    - Verify reproducibility and hash identity"
	@echo "  make demo       - Run complete end-to-end demo"

install:
	uv python install 3.12
	uv venv .venv --python 3.12
	uv pip install --python .venv/bin/python harbor pytest pyyaml anthropic toml

analyze:
	./bin/taskforge analyze

generate:
	./bin/taskforge generate --n 10 --seed 42

validate:
	./bin/taskforge validate

evaluate:
	./bin/taskforge evaluate

report:
	./bin/taskforge report

rebuild:
	./bin/taskforge rebuild

demo:
	./bin/taskforge demo

clean:
	rm -rf tasks/generated/* tasks/rebuild_test/*
