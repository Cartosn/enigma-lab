#!/usr/bin/env sh
# Instala el entorno de Enigma Lab en Linux o macOS.
#
# Uso, desde la raíz del repositorio:  sh scripts/install.sh
#
# Instala uv si falta (https://docs.astral.sh/uv/); uv descarga Python 3.12 y las
# dependencias fijadas en uv.lock.
set -eu
cd "$(dirname "$0")/.."

if ! command -v uv >/dev/null 2>&1; then
    echo "Instalando uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    PATH="$HOME/.local/bin:$PATH"
    export PATH
fi

if ! command -v make >/dev/null 2>&1; then
    echo "Aviso: falta GNU Make. Instálalo con tu gestor de paquetes (por ejemplo, sudo apt install make)." >&2
fi

uv python install 3.12
uv sync

echo ""
echo "Listo. Abre la app con:  make app"
