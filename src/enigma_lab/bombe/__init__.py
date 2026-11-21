"""La Bombe de Turing-Welchman y su verificador (spec 5.5).

- ``scrambler``: el aleatorizador (Enigma sin plugboard) precalculado por orden de
  rotores para las 17.576 posiciones del núcleo.
- ``wiring``: el menú convertido en el cableado de la Bombe (cables, aristas, diagonal).
- ``bombe_numba``: el barrido rápido en Numba, con union-find.
- ``bombe_reference``: la misma Bombe en Python puro, solo para las pruebas.
- ``sweep``: la Bombe completa: ajustes, barrido por órdenes y lista de paradas.
- ``checker``: el verificador, en dos etapas (máquina de verificación y descifrado).
"""
