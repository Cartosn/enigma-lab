"""Enigma Lab: simulación y criptoanálisis estadístico de Enigma.

Paquete del proyecto final de Criptografía (Universidad Nacional de Colombia).
La lógica de la máquina existe una sola vez, aquí, en Python; la interfaz
(``app/``) y los componentes JavaScript solo muestran lo que este paquete calcula.

Subpaquetes (se completan por fases; ver ``docs/PROGRESS.md``):

- ``core``: la máquina Enigma y el espacio de claves.
- ``stats``: estadística del idioma (frecuencias, IC, n-gramas).
- ``cribs``: arrastre de cribs y menús.
- ``bombe``: la Bombe de Turing-Welchman y su verificador.
- ``banburismus``: puntuación en decibanes y prueba secuencial de Wald.
- ``rejewski``: características y catálogo de Rejewski.
- ``attacks``: ataques modernos solo con texto cifrado.
- ``experiments``: experimentos E1 a E8.
- ``viz``: tema visual, figuras y formato de números.
"""

__version__ = "0.1.0"

#: Semilla global del proyecto.
SEED = 2026
