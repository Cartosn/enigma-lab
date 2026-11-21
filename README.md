# Enigma Lab

Proyecto final de Criptografía, Universidad Nacional de Colombia (2026).

**¿Por qué se rompió un cifrado con unas 1,6 × 10²⁰ claves, y cuánta información
necesita cada ataque?** Enigma Lab es una app que simula la máquina Enigma, la Bombe de
Turing-Welchman y experimentos estadísticos sobre los ataques. Sirve para la demo en
vivo de la presentación y produce las cifras de sus diapositivas.

> **Estado:** fase 3 de 6 cerrada.
> - **Núcleo:** Enigma I, M3 y M4 validadas contra los vectores publicados, py-enigma
>   (10.000 claves) y CyberChef.
> - **Estadística:** del idioma, con un corpus de Gutenberg.
> - **Cribs y menús:** arrastre del crib y menú de la Bombe.
> - **Bombe:** union-find en Numba, con diagonal board, modos Bletchley y robusto, y un
>   verificador que recupera la clave; validada contra CyberChef y la tabla de Turing.
> - **Experimentos:** E1 a E5.
> - **App:** páginas Máquina, Espacio de claves, Estadística, Cribs y menús, La Bombe y
>   Experimentos.
>
> El detalle está en [`docs/PROGRESS.md`](docs/PROGRESS.md).

## Inicio rápido (local)

1. Instala el entorno: uv, Python 3.12 y las dependencias de `uv.lock`.
   - Windows (PowerShell): `powershell -ExecutionPolicy Bypass -File scripts\install.ps1`
   - Linux o macOS: `sh scripts/install.sh`
2. Abre la app: `make app`, y luego http://localhost:8501.
3. Corre las pruebas: `make test`.

Sin make: `uv run streamlit run app/Inicio.py` y `uv run pytest`. `make help` lista
todos los objetivos.

## Reproducir los resultados

`make reproduce` hace tres cosas:
1. descarga el corpus completo (`make corpus`, con SHA-256 verificado);
2. corre los experimentos E1 a E5 en modo completo, con semilla 2026;
3. arma `results/presentacion/`.

`make resumen` rehace el resumen sin volver a correr nada. Sin internet, `make rapido`
corre todo con las muestras del corpus que trae el repositorio. `make bench-demo` mide la
demo 2 de la Bombe en el equipo donde se corre (éxito y tiempos).

## Estructura

| Carpeta | Contenido |
| --- | --- |
| `src/enigma_lab/` | Toda la lógica: máquina, estadística, cribs, Bombe, Banburismus, experimentos, tema |
| `app/` | La interfaz Streamlit: `Inicio.py` (entrada), `pages/`, `ui/` y `static/fonts/` |
| `tests/` | pytest + hypothesis; `test_presentacion.py` comprueba cada cifra de las diapositivas |
| `docs/` | Spec, progreso, decisiones, arquitectura, validación, guía de estudio y fuentes |
| `scripts/` | Instalación, ayuda del Makefile, banco de la demo 2, URL de CyberChef y el piloto original |
