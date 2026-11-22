# Enigma Lab · imagen de la app (spec, secciones 3 y 10)
#
#   docker compose up          y luego abrir  http://localhost:8501
#
# Python 3.12 con uv; las dependencias salen de uv.lock (uv sync --frozen --no-dev). La
# imagen trae las muestras del corpus (data/corpora/muestras) y los resultados guardados
# (results/): la app funciona sin internet. Los núcleos de Numba se compilan al construir
# la imagen, así que la primera apertura no espera al compilador.

FROM python:3.12-slim

# uv, la misma versión con que se generó uv.lock.
COPY --from=ghcr.io/astral-sh/uv:0.13.9 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONUTF8=1 \
    PYTHONUNBUFFERED=1 \
    ENIGMA_LAB_ROOT=/app \
    NUMBA_CACHE_DIR=/var/cache/enigma-lab/numba \
    MPLCONFIGDIR=/var/cache/enigma-lab/matplotlib

WORKDIR /app

# 1. Las dependencias, en su propia capa: se reutiliza mientras uv.lock no cambie.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# 2. El proyecto (lo que no excluye .dockerignore) y su instalación.
COPY . .
RUN uv sync --frozen --no-dev

# 3. Un usuario sin privilegios, con escritura en las cachés de Numba y Matplotlib.
RUN useradd --create-home --uid 1000 enigma \
 && mkdir -p "$NUMBA_CACHE_DIR" "$MPLCONFIGDIR" \
 && chown -R enigma:enigma /var/cache/enigma-lab
USER enigma

# 4. Precalienta Numba dentro de la imagen (la caché queda en NUMBA_CACHE_DIR).
RUN python -c "from enigma_lab.bombe.sweep import warm_up; print(f'Numba listo en {warm_up():.1f} s')"

EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health', timeout=4)"]

# Streamlit sin abrir navegador (headless), escuchando fuera del contenedor y sin vigilar
# archivos (en la imagen el código no cambia; en WSL la vigilancia sería por sondeo).
CMD ["streamlit", "run", "app/Inicio.py", \
     "--server.headless=true", "--server.address=0.0.0.0", "--server.port=8501", \
     "--server.fileWatcherType=none", "--browser.gatherUsageStats=false"]
