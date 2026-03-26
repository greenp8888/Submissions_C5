PYTHON ?= python
VENV_DIR ?= .venv

ifeq ($(OS),Windows_NT)
VENV_PY := $(VENV_DIR)/Scripts/python.exe
else
VENV_PY := $(VENV_DIR)/bin/python
endif

.PHONY: help venv install setup run check clean clean-pyc clean-cache reset-chats

help:
	@echo "Available targets:"
	@echo "  make setup        - Create virtualenv and install dependencies"
	@echo "  make venv         - Create virtualenv in $(VENV_DIR)"
	@echo "  make install      - Install project dependencies into virtualenv"
	@echo "  make run          - Run Streamlit app"
	@echo "  make check        - Run Python syntax checks"
	@echo "  make clean-pyc    - Remove Python bytecode files"
	@echo "  make clean-cache  - Remove __pycache__ and .cache"
	@echo "  make clean        - Run all clean targets"
	@echo "  make reset-chats  - Remove all saved chat session JSON files"

setup: venv install

venv:
	$(PYTHON) -m venv $(VENV_DIR)

install: venv
	$(VENV_PY) -m pip install --upgrade pip
	$(VENV_PY) -m pip install -r requirements.txt

run:
	$(VENV_PY) -m streamlit run main.py

check:
	$(VENV_PY) -m py_compile main.py openrouter_client.py summaries.py storage.py

clean-pyc:
	$(PYTHON) -c "import pathlib; [p.unlink() for p in pathlib.Path('.').rglob('*.pyc')]"
	$(PYTHON) -c "import pathlib; [p.unlink() for p in pathlib.Path('.').rglob('*.pyo')]"

clean-cache:
	$(PYTHON) -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]"
	$(PYTHON) -c "import shutil, pathlib; p=pathlib.Path('.cache'); shutil.rmtree(p, ignore_errors=True) if p.exists() else None"

clean: clean-pyc clean-cache

reset-chats:
	$(PYTHON) -c "import pathlib; d=pathlib.Path('chat_sessions'); [p.unlink() for p in d.glob('*.json')] if d.exists() else None"
