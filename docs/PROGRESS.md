# Progreso

Última actualización: 20-11-2026 · fase 0 cerrada.

| Fase | Estado | Semana |
| --- | --- | --- |
| 0 · Andamiaje | Cerrada (20-11-2026) | 1 |
| 1 · Núcleo Enigma | Siguiente | 1 |
| 2 · Estadística y cribs | Pendiente | 1–2 (reunión con el profe) |
| 3 · Bombe | Pendiente | 2 |
| 4 · Banburismus | Pendiente | 3 |
| 5 · Extensiones P2 | Pendiente | 3 |
| 6 · Pulido y entrega | Pendiente | Fin de la 3 |

## Fase 0 · Andamiaje

**Criterio de aceptación:** `make test` y `make app` funcionan. Se cumple. `make test`
da 59 pruebas que pasan y 8 pendientes en unos 11 s en este equipo. `make app` sirve la
app en http://localhost:8501; se revisó en el navegador integrado, con las fuentes
cargadas desde la app y sin peticiones externas.

**Qué quedó:**
- Entorno: uv 0.13.9, CPython 3.12.16, `pyproject.toml`, `uv.lock` y `requirements.txt`.
  Versiones principales: NumPy 2.5.5, Numba 0.68.1, pandas 3.1.1, SciPy 1.18.1,
  statsmodels 0.15.0, Streamlit 1.67.0, Plotly 7.1.0, Matplotlib 3.11.2, networkx 3.7,
  py-enigma 1.0.2.
- Calidad: ruff, mypy (modo básico), pytest + hypothesis (determinista) y CI en Ubuntu y
  Windows (aún sin ejecutar: falta el remoto).
- `Makefile`: `help`, `install`, `test`, `test-rapido`, `lint`, `format`, `app` y
  `requirements`. Scripts de instalación `install.ps1` e `install.sh`.
- Tema «Bletchley nocturno»:
  - colores del spec, en `.streamlit/config.toml` y en `viz/theme.py`;
  - paleta Okabe-Ito en un orden validado;
  - rampa ámbar;
  - plantillas Plotly `enigma_dark` y `enigma_dark_demo`, y estilos Matplotlib
    `enigma_print` y `enigma_slides`;
  - fuentes Inter y JetBrains Mono en el repo.
- App: punto de entrada con navegación, interruptor de modo demo (20 px) y página Inicio,
  con la pregunta, «67 → 20 bits», la barra de bits, las tarjetas de los módulos, el
  estado de la validación y las fuentes.
- `core/keyspace.py`, adelantado a esta fase (D-005), y `viz/numfmt.py`.
- `docs/`: PROGRESS, DECISIONES, FUENTES, ARQUITECTURA, VALIDACION y
  GUIA_DE_ESTUDIO (tema 1).

**Cifras obtenidas** (todas del código y comprobadas en `tests/test_keyspace.py` y
`tests/test_presentacion.py`):
- Total sin anillos: 158.962.555.217.826.360.000 claves (67,11 bits). Con anillos:
  1,0746 × 10²³ claves (76,51 bits).
- Bits por componente: orden 5,91 · posiciones 14,10 · anillos 9,40 · plugboard 47,10. El
  plugboard es el 70,2 % de los 67,11 bits.
- Plugboard: N(6) = 100.391.791.500; N(10) = 150.738.274.937.250; el máximo es con 11
  cables, N(11) = 205.552.193.096.250.
- Barrido de la Bombe: 1.054.560 configuraciones (20,01 bits).
- Fuerza bruta a 10⁹ claves por segundo: 5.037 años.

**Exploración previa al plan** (no es un resultado del proyecto; la fase 3 la repite
con `enigma_lab`). `scripts/exploracion_demo2.py` usa el piloto con 5.000 claves y
semilla 2026:
- Con WETTERBERICHT, el rotor central se mueve dentro de las 13 letras en el 46,7 % de
  las claves.
- El menú tiene 0 lazos en el 39,8 % de las claves, 1 en el 46,1 %, 2 en el 11,9 % y 3 o
  más en el 2,2 %, con 15,41 letras en promedio.
- Por eso la demo 2 necesitará el modo robusto y un verificador automático de todas las
  paradas.

**Qué falta (fase 1):** `core/` con Enigma I y M3, el doble paso, la traza y la versión
por lotes; los vectores de 6.1 y un mensaje histórico; py-enigma en 10.000 claves;
hypothesis; CyberChef (P-003); la página Máquina con la animación y los preajustes
«Vector BDZGO» y «Portada»; `make resumen`.

**Pendiente del autor:** confirmar en qué equipo se hará la demo 2 (P-001) y crear el
repositorio remoto, para que corra la CI y para el enlace de la diapositiva 21.
