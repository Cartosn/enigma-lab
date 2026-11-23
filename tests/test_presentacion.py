"""Cada cifra de la presentación, comprobada contra el código.

El registro de cifras está en ``enigma_lab/cifras.py``: la misma lista alimenta la tabla
«Cifras de la presentación» de ``RESUMEN.md``. Las cifras de módulos que aún no
existen quedan como pendientes, con la fase en que llegan (``pytest -ra`` las lista).
Las medidas se comprueban contra la corrida completa guardada en ``results/``; sin ella
(un clon sin resultados) esas pruebas se saltan (D-073).
"""

from __future__ import annotations

import pytest

from enigma_lab.cifras import CIFRAS, Cifra, SinCorrida

READY = [c for c in CIFRAS if not c.is_pending]
PENDING = [c for c in CIFRAS if c.is_pending]


@pytest.mark.parametrize("cifra", READY, ids=[f"diap {c.slides}: {c.description}" for c in READY])
def test_cifra(cifra: Cifra) -> None:
    assert cifra.compute is not None
    try:
        obtained = cifra.compute()
    except SinCorrida as missing:
        pytest.skip(str(missing))
    assert obtained == cifra.expected, f"diapositivas {cifra.slides}"


if PENDING:  # desde la fase 5 no queda ninguna

    @pytest.mark.parametrize(
        "cifra",
        [pytest.param(c, marks=pytest.mark.skip(reason=c.pending)) for c in PENDING],
        ids=[f"diap {c.slides}" for c in PENDING],
    )
    def test_cifra_pendiente(cifra: Cifra) -> None:  # pragma: no cover
        raise AssertionError("pendiente")
