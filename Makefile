# Enigma Lab · Makefile
#
# Funciona con GNU Make en Linux, macOS y Windows. En Windows las recetas pueden
# correr en cmd.exe o en sh, así que solo usan comandos de uv y de python.
# Lista de objetivos:  make help

.DEFAULT_GOAL := help

# La consola de Windows usa cp1252: sin esto, imprimir tildes puede fallar.
export PYTHONUTF8 := 1

UV ?= uv
PORT ?= 8501
# Opciones extra de Streamlit, p. ej.  make app STREAMLIT_FLAGS=--server.headless=true
STREAMLIT_FLAGS ?=

.PHONY: help install test test-rapido lint format app requirements

help: ## Muestra esta lista
	@$(UV) run --no-project python scripts/make_help.py Makefile

install: ## Crea el entorno: Python 3.12 y las dependencias fijadas en uv.lock
	$(UV) sync

test: ## Corre todas las pruebas
	$(UV) run pytest

test-rapido: ## Corre las pruebas sin las marcadas como lentas
	$(UV) run pytest -m "not lento"

lint: ## Revisa el estilo (ruff) y los tipos (mypy)
	$(UV) run ruff check .
	$(UV) run ruff format --check .
	$(UV) run mypy

format: ## Formatea el código con ruff
	$(UV) run ruff format .
	$(UV) run ruff check --fix .

app: ## Abre Enigma Lab en el navegador (http://localhost:8501)
	$(UV) run streamlit run app/Inicio.py --server.port $(PORT) $(STREAMLIT_FLAGS)

requirements: ## Regenera requirements.txt a partir de uv.lock
	$(UV) export --format requirements-txt --no-hashes --all-groups --output-file requirements.txt
