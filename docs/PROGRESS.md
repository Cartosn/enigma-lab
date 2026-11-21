# Progreso

Última actualización: 20-11-2026 · fase 2 cerrada.

| Fase | Estado | Semana |
| --- | --- | --- |
| 0 · Andamiaje | Cerrada (20-11-2026) | 1 |
| 1 · Núcleo Enigma | Cerrada (20-11-2026) | 1 |
| 2 · Estadística y cribs | Cerrada (20-11-2026) | 1–2 (reunión con el profe) |
| 3 · Bombe | Siguiente | 2 |
| 4 · Banburismus | Pendiente | 3 |
| 5 · Extensiones P2 | Pendiente | 3 |
| 6 · Pulido y entrega | Pendiente | Fin de la 3 |

## Fase 2 · Estadística y cribs

**Criterios de aceptación:** se cumplen.

| Criterio | Resultado |
| --- | --- |
| Cifras de 5.2 exactas | Todas (desde la fase 0; E2 las reúne) |
| E4 coincide con (25/26)^L dentro del IC | Texto aleatorio: dentro del IC 95 % en 10 de 10 longitudes |

Además, los casos de 6.5 (diapositivas 10 y 11 y caso de respaldo) pasan exactos.
`make test` da 189 pruebas que pasan y 3 cifras pendientes (fases 3 a 5), en unos 40 s.
`make lint` pasa sin errores. `make reproduce` completo (corpus y E1 a E4) tarda 39 s en
este equipo.

**Qué quedó:**
- **Corpus:**
  - alemán: Fontane y Kafka, 578.365 letras;
  - español: Cervantes, 1.620.450 letras;
  - se descarga de un espejo de Gutenberg con SHA-256 verificado;
  - el repo trae muestras de unos 200 KB por idioma.
- **`stats/`:** normalización según el spec, frecuencias, IC, χ², la antifrecuencia del
  cifrado y su potencia teórica, matriz plano × cifrado, cuadrigramas e intervalos.
- **`cribs/`:** arrastre del crib, escalar y vectorizado, y menú con lazos, aristas en
  lazos y letra de prueba.
- **Experimentos:** E2, E3 y E4, con figuras para el informe. El resumen agrega la
  diapositiva 15 y `r2_cribs.csv`.
- **App:**
  - páginas Espacio de claves, Estadística del cifrado, Cribs y menús, y Experimentos;
  - dos componentes nuevos, el arrastre del crib y el grafo del menú, que solo dibujan
    datos de Python;
  - todo revisado en el navegador.
- **Documentos:** guía de estudio (tema 3), VALIDACION (6.5), DECISIONES (D-024 a
  D-030), FUENTES (corpus) y ARQUITECTURA.

**Cifras obtenidas** (modo completo, semilla 2026, commit `6bd632e`):
- **E3:**
  - El IC del corpus alemán es 0,0757 (Pommerening: 0,0758) y el del español, 0,0750.
  - Con 1.000 letras, el IC del alemán baja de 0,0760 en el plano a 0,0385 en el
    cifrado.
  - La χ² rechaza la uniformidad del 100 % de los planos y del 10,0 % de los cifrados.
    La antifrecuencia (1 − f_c)/25 predice 8,0 %: el cifrado no es del todo uniforme.
  - No hubo ningún punto fijo en 3.850.000 letras.
- **E4, texto aleatorio:**
  - L = 13: sobrevive el 60,1 % de las alineaciones falsas (IC 59,9 %–60,3 %; teoría
    60,1 %).
  - L = 50: el 14,1 % (teoría 14,1 %).
- **E4, alemán real:**
  - L = 13: el 61,6 % (61,4 %–61,8 %); L = 50: el 15,4 %.
  - (25/26)^L queda fuera del IC en las 10 longitudes. La teoría corregida
    (1 − (1 − κ)/25)^L, con κ = 0,0802, queda dentro en las 10.
- **Cifras de la presentación:** 36 de 36 coinciden; 3 llegan en las fases 3 a 5.

**Qué falta (fase 3):**
- la Bombe: aleatorizador precalculado, versión en Numba y versión de referencia;
- el verificador;
- la página La Bombe;
- E5, con la tabla de Turing;
- `make bench-demo` para la demo 2;
- CyberChef para la Bombe.

**Pendiente del autor:**
- confirmar el equipo de la demo 2 (P-001);
- crear el repositorio remoto;
- encender Docker Desktop si quiere la validación automática con CyberChef (P-003).

## Fase 1 · Núcleo Enigma

**Criterios de aceptación:** se cumplen todos.

| Criterio | Resultado |
| --- | --- |
| Vectores de 6.1 | 9 de 9, con un mensaje real del U-264 (1942) |
| 100 % frente a py-enigma en 10.000 claves | 10.000 de 10.000 (IC 95 % de Wilson 99,96 %–100 %) |
| Propiedades | Involución, sin puntos fijos y lotes = escalar, con hypothesis |
| Periodo 16.900 y 676 fuera del ciclo | Un solo ciclo de 16.900; 676 fuera |
| La animación reproduce la traza | Lo comprueba una prueba (el JSON es la traza) y se vio en el navegador |

`make test` da 150 pruebas que pasan y 5 cifras pendientes, en unos 35 s en este equipo.
`make lint` (ruff y mypy) pasa sin errores.

**Qué quedó:**
- **Núcleo (`core/`):**
  - `wiring.py`: cableados I–VIII, Beta, Gamma y los reflectores A, B, C, B delgado y C
    delgado, tomados de Wikipedia.
  - `stepping.py`: paso con doble paso y estructura de ciclos.
  - `machine.py`:
    - `EnigmaConfig` inmutable, que lee hojas de claves;
    - `Enigma` con `encrypt` y `trace`, para Enigma I, M3 y M4.
  - `batch.py`: cifrado por lotes con tablas precalculadas.
  - `random_keys.py`: claves aleatorias con semilla.
  - `vectors.py`: los vectores de 6.1.
- **Validación:**
  - py-enigma en 10.000 claves (E1 y `tests/test_pyenigma.py`);
  - CyberChef a mano en 6 casos, todos iguales;
  - hypothesis.

  Detalle en `docs/VALIDACION.md`.
- **Experimentos:** marco común, E1 y `make reproduce`, `make rapido`,
  `make experimento` y `make resumen`. El registro único de cifras está en `cifras.py`.
- **App:**
  - Página Máquina, con:
    - los preajustes «Vector BDZGO», «Portada» y «Ejemplo histórico»;
    - los botones «Clave aleatoria» y «Reiniciar posición»;
    - salida en grupos de 5;
    - comprobaciones en vivo: cifrar la salida devuelve la entrada y no hay puntos fijos;
    - la animación SVG de la traza.
  - En Inicio, el estado de la validación en vivo.
- **Documentos:** VALIDACION, la guía de estudio (tema 2), DECISIONES (D-015 a D-023),
  FUENTES y ARQUITECTURA.

**Cifras obtenidas** (E1 en modo completo, semilla 2026, 19 s):
- **py-enigma:** 10.000 de 10.000 casos con 1.007.710 letras: Enigma I 4.945 de 4.945,
  M3 2.568 de 2.568 y M4 2.487 de 2.487.
- **Propiedades:** 2.000 claves de Enigma I con 200.000 letras dan 0 puntos fijos,
  involución en las 2.000 claves y lotes iguales al escalar en las 2.000.
- **CyberChef:** 6 de 6, incluido el U-264 (232 letras) y una clave M3 con el rotor VI y
  el reflector C.
- **Cifras de la presentación:** 29 de 29 coinciden; 5 llegan en las fases 2 a 5.
- **Demo 1:** el cálculo de la traza de «Vector BDZGO» y de «Portada» tarda menos de
  1 ms en este equipo.

**Qué falta (fase 2):**
- `keyspace` completo y la página «Espacio de claves» (E2);
- el corpus alemán y español, y `stats/` (E3);
- `cribs/` con los casos de 6.5 (E4);
- las páginas 3 a 5 y la página Experimentos.

**Pendiente del autor:**
- confirmar en qué equipo se hará la demo 2 (P-001);
- crear el repositorio remoto, para la CI y el enlace de la diapositiva 21;
- encender Docker Desktop cuando quiera la validación automática con CyberChef (P-003).

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
