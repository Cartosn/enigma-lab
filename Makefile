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

SEMILLA ?= 2026
MODO ?= completo
E ?= todos
# Casos por configuración en make bench-demo
N ?= 30

.PHONY: help install test test-rapido lint format app requirements corpus experimento reproduce rapido resumen bench-demo

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

corpus: ## Descarga el corpus completo de Project Gutenberg (verifica SHA-256)
	$(UV) run python scripts/fetch_corpora.py

experimento: ## Corre un experimento: make experimento E=e1 MODO=rapido
	$(UV) run python -m enigma_lab.experiments $(E) --mode $(MODO) --seed $(SEMILLA)

reproduce: corpus ## Corre todos los experimentos en modo completo y arma el resumen
	$(UV) run python -m enigma_lab.experiments todos --mode completo --seed $(SEMILLA)
	$(UV) run python -m enigma_lab.resumen

rapido: ## Corre todos los experimentos en modo rápido (para la app)
	$(UV) run python -m enigma_lab.experiments todos --mode rapido --seed $(SEMILLA)

resumen: ## Arma results/presentacion/ (RESUMEN.md, cifras.json, CSV) sin correr nada
	$(UV) run python -m enigma_lab.resumen

bench-demo: ## Mide la demo 2 en este equipo: éxito y tiempos (make bench-demo N=30)
	$(UV) run python scripts/bench_demo2.py --n $(N)

requirements: ## Regenera requirements.txt a partir de uv.lock
	$(UV) export --format requirements-txt --no-hashes --all-groups --output-file requirements.txt
