# Utilidades multiplataforma. En Windows PowerShell usar los comandos
# equivalentes documentados en README.md (los targets *-win los ejecutan).

PY ?= python
VENV := .venv
PYBIN := $(VENV)/Scripts/python.exe

.PHONY: help setup lint test test-ml test-backend build-web data-audit clean

help:
	@echo "targets: setup, lint, test, test-ml, test-backend, build-web, data-audit, clean"

setup:
	$(PY) -m venv $(VENV)
	$(PYBIN) -m pip install --upgrade pip
	$(PYBIN) -m pip install -r ml/requirements.txt -r backend/requirements.txt
	cd frontend && npm ci

lint:
	$(PYBIN) -m ruff check .
	cd frontend && npm run lint

test: test-ml test-backend

test-ml:
	$(PYBIN) -m pytest ml/tests

test-backend:
	$(PYBIN) -m pytest backend/tests

build-web:
	cd frontend && npm run build

data-audit:
	$(PYBIN) scripts/audit_data.py

clean:
	rm -rf $(VENV) frontend/node_modules frontend/dist
