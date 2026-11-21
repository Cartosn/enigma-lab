"""Números con formato español: punto de miles, coma decimal y signo menos tipográfico.

Toda cifra que lea una persona (app, figuras, resumen, informe) pasa por aquí, para
que la app y las diapositivas escriban los números igual: 1.054.560 · 67,11 ·
1,6 × 10²⁰ · 70,2 % · −0,093.
"""

from __future__ import annotations

MINUS = "−"
"""Signo menos tipográfico (−), el que usan las diapositivas."""

NBSP = " "
"""Espacio no separable, entre la cifra y su unidad («70,2 %», «5.037 años»)."""

_SUPERSCRIPTS = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")


def _swap_separators(text: str) -> str:
    """Pasa del formato inglés (1,234.5) al español (1.234,5)."""
    return text.replace(",", "\0").replace(".", ",").replace("\0", ".")


def _sign(value: float) -> str:
    return MINUS if value < 0 else ""


def fmt_int(value: int) -> str:
    """Entero con punto de miles: 1054560 → «1.054.560»."""
    return _sign(value) + f"{abs(value):,}".replace(",", ".")


def fmt_dec(value: float, decimals: int = 2) -> str:
    """Decimal con coma y punto de miles: 67.107 → «67,11»; −0.093 → «−0,093»."""
    text = _swap_separators(f"{abs(value):,.{decimals}f}")
    is_zero = float(text.replace(".", "").replace(",", ".")) == 0
    return ("" if is_zero else _sign(value)) + text


def fmt_pct(fraction: float, decimals: int = 1) -> str:
    """Fracción como porcentaje: 0.7018 → «70,2 %»."""
    return f"{fmt_dec(100 * fraction, decimals)}{NBSP}%"


def fmt_sci(value: float, digits: int = 2) -> str:
    """Notación científica con ``digits`` cifras significativas: 1,5896e20 → «1,6 × 10²⁰»."""
    if value == 0:
        return "0"
    mantissa, exponent = f"{abs(value):.{digits - 1}e}".split("e")
    power = str(int(exponent)).translate(_SUPERSCRIPTS)
    return f"{_sign(value)}{mantissa.replace('.', ',')} × 10{power}"
