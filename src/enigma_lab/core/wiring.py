"""Cableados de rotores y reflectores, muescas y modelos de Enigma.

Fuente: Wikipedia, «Enigma rotor details», revisión 1275803743 (15-02-2025),
consultada el 20-11-2026. Los cableados coinciden con los del piloto (rotores I–V y
reflector B) y con los de py-enigma 1.0.2, que no trae el reflector A; lo comprueba
``tests/test_wiring.py``.

**Cómo leer un cableado.** Es la imagen de A…Z con el rotor en la posición A y el
anillo en A: el rotor I lleva A→E, B→K, C→M…

**Cómo leer una muesca.** Se nombra por la letra que se ve en la ventana cuando el
rotor arrastra al de su izquierda. Con el rotor I en Q, la siguiente pulsación lo lleva
a R y hace avanzar también al rotor de su izquierda. Los rotores navales VI–VIII
tienen dos muescas (Z y M). Los rotores griegos de la M4 (Beta y Gamma) nunca giran.
"""

from __future__ import annotations

from dataclasses import dataclass

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


@dataclass(frozen=True)
class RotorSpec:
    """Un rotor: su cableado y las letras de ventana en las que arrastra al siguiente."""

    name: str
    wiring: str
    notches: str = ""


ROTORS: dict[str, RotorSpec] = {
    spec.name: spec
    for spec in (
        RotorSpec("I", "EKMFLGDQVZNTOWYHXUSPAIBRCJ", "Q"),
        RotorSpec("II", "AJDKSIRUXBLHWTMCQGZNPYFVOE", "E"),
        RotorSpec("III", "BDFHJLCPRTXVZNYEIWGAKMUSQO", "V"),
        RotorSpec("IV", "ESOVPZJAYQUIRHXLNFTGKDCMWB", "J"),
        RotorSpec("V", "VZBRGITYUPSDNHLXAWMJQOFECK", "Z"),
        RotorSpec("VI", "JPGVOUMFYQBENHZRDKASXLICTW", "ZM"),
        RotorSpec("VII", "NZJHGRCXMYSWBOUFAIVLPEKQDT", "ZM"),
        RotorSpec("VIII", "FKQHTLXOCBJSPDZRAMEWNIUYGV", "ZM"),
        RotorSpec("Beta", "LEYJVCNIXWPBQMDRTAKZGFUHOS"),
        RotorSpec("Gamma", "FSOKANUERHMBTIYCWLQPZXVGJD"),
    )
}
"""Rotores por nombre. Beta y Gamma (M4) no tienen muesca: nunca giran."""

REFLECTORS: dict[str, str] = {
    "A": "EJMZALYXVBWFCRQUONTSPIKHGD",
    "B": "YRUHQSLDPXNGOKMIEBFZCWVJAT",
    "C": "FVPJIAOYEDRZXWGCTKUQSBNMHL",
    "B-Thin": "ENKQAUYWJICOPBLMDXZVFTHRGS",
    "C-Thin": "RDOBJNTKVEHMLFCWZAXGYIPSUQ",
}
"""Reflectores (Umkehrwalze) por nombre; los «Thin» son los delgados de la M4."""


@dataclass(frozen=True)
class MachineModel:
    """Un modelo de Enigma: qué rotores y reflectores admite.

    ``rotors`` son los rotores que giran, de entre los que se eligen tres distintos.
    ``greek`` son los rotores fijos que la M4 pone a la izquierda de esos tres.
    """

    key: str
    name: str
    rotors: tuple[str, ...]
    reflectors: tuple[str, ...]
    greek: tuple[str, ...] = ()

    @property
    def n_rotors(self) -> int:
        """Rotores en la máquina: 3, o 4 con el griego de la M4."""
        return 4 if self.greek else 3


MODELS: dict[str, MachineModel] = {
    "I": MachineModel("I", "Enigma I", ("I", "II", "III", "IV", "V"), ("A", "B", "C")),
    "M3": MachineModel(
        "M3", "Enigma M3 (naval)", ("I", "II", "III", "IV", "V", "VI", "VII", "VIII"), ("B", "C")
    ),
    "M4": MachineModel(
        "M4",
        "Enigma M4 (naval)",
        ("I", "II", "III", "IV", "V", "VI", "VII", "VIII"),
        ("B-Thin", "C-Thin"),
        greek=("Beta", "Gamma"),
    ),
}
"""Modelos por clave: "I" (Wehrmacht), "M3" y "M4" (Kriegsmarine)."""


def to_index(letter: str) -> int:
    """Letra A–Z a número 0–25."""
    index = ALPHABET.find(letter.upper())
    if len(letter) != 1 or index < 0:
        raise ValueError(f"no es una letra de la A a la Z: {letter!r}")
    return index


def to_letter(index: int) -> str:
    """Número 0–25 a letra A–Z."""
    return ALPHABET[index % 26]


def permutation(wiring: str) -> tuple[int, ...]:
    """Cableado en letras a permutación de 0–25: p[x] es la salida para la entrada x."""
    perm = tuple(to_index(c) for c in wiring)
    if sorted(perm) != list(range(26)):
        raise ValueError(f"el cableado no es una permutación de A–Z: {wiring}")
    return perm


def inverse(perm: tuple[int, ...]) -> tuple[int, ...]:
    """Permutación inversa: el camino de vuelta por un rotor."""
    inv = [0] * len(perm)
    for x, y in enumerate(perm):
        inv[y] = x
    return tuple(inv)


def is_reflector(perm: tuple[int, ...]) -> bool:
    """¿Es una involución sin puntos fijos? Así debe ser todo reflector.

    Que el reflector sea su propia inversa hace que cifrar y descifrar sean la misma
    operación. Que no tenga puntos fijos hace que ninguna letra se cifre a sí misma.
    """
    return all(perm[perm[x]] == x and perm[x] != x for x in range(len(perm)))
