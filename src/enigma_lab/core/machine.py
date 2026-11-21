"""La máquina Enigma: clave inmutable, cifrado y traza letra por letra (spec 5.1).

El camino de una letra, con el plugboard P, los rotores derecho R, central M e
izquierdo L, y el reflector U:

    lámpara = P⁻¹ · R⁻¹ · M⁻¹ · L⁻¹ · U · L · M · R · P (tecla)

Cada rotor actúa desplazado. Si su ventana está en ``p`` y su anillo en ``r``, el
cableado queda corrido s = p − r lugares, y la salida para la entrada x es

    rotor_s(x) = W[(x + s) mod 26] − s  (mod 26).

Como U es una involución sin puntos fijos, la permutación completa también lo es.
Cifrar dos veces devuelve el original, y ninguna letra se cifra a sí misma.

Toda la lógica está en :meth:`Enigma._signal`: ``encrypt`` y ``trace`` la comparten,
de modo que la animación muestra exactamente lo que calcula el cifrado.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass, field, replace
from typing import Any

from enigma_lab.core.stepping import StepResult, notch_sets, step
from enigma_lab.core.wiring import (
    ALPHABET,
    MODELS,
    REFLECTORS,
    ROTORS,
    inverse,
    permutation,
    to_index,
    to_letter,
)

MAX_CABLES = 13


def parse_settings(text: str | tuple[int, ...] | list[int], count: int) -> tuple[int, ...]:
    """Anillos o posiciones en notación de hoja de claves a números 0–25.

    Acepta letras juntas ("BUL") o separadas ("B U L"), números de 1 a 26 como en
    las hojas de claves ("02 21 12"), o una secuencia de enteros 0–25.
    """
    if isinstance(text, (tuple, list)):
        values = tuple(int(v) for v in text)
    else:
        tokens = text.split()
        if len(tokens) == 1 and tokens[0].isalpha():
            tokens = list(tokens[0])
        values = tuple(int(t) - 1 if t.isdigit() else to_index(t) for t in tokens)
    if len(values) != count or not all(0 <= v < 26 for v in values):
        raise ValueError(f"se esperaban {count} valores entre A y Z (o 01 y 26): {text!r}")
    return values


def parse_plugboard(text: str) -> tuple[tuple[str, str], ...]:
    """Cables del plugboard en notación de hoja de claves ("AV BS CG") a parejas ordenadas.

    Cada pareja se guarda en orden alfabético (AV, no VA) y las parejas también, para
    que dos escrituras de la misma conexión den la misma clave.
    """
    tokens = [t for t in re.split(r"[\s,;]+", text.strip().upper()) if t]
    pairs = []
    for token in tokens:
        if not re.fullmatch(r"[A-Z]{2}", token):
            raise ValueError(f"plugboard ilegible; usa parejas como «AV BS CG»: {token!r}")
        a, b = sorted(token)
        pairs.append((a, b))
    return tuple(sorted(pairs))


@dataclass(frozen=True)
class EnigmaConfig:
    """Una clave completa de Enigma, inmutable.

    Attributes:
        rotors: nombres de izquierda a derecha, p. ej. ("II", "IV", "V"); en la M4,
            ("Beta", "II", "IV", "I").
        reflector: "A", "B" o "C" (Enigma I), "B" o "C" (M3), "B-Thin" o "C-Thin" (M4).
        rings: anillos (Ringstellung) 0–25 de cada rotor; A = 0 = «01».
        positions: letras de ventana al empezar a cifrar, 0–25.
        plugboard: parejas de letras intercambiadas, ordenadas.
        model: "I", "M3" o "M4".
    """

    rotors: tuple[str, ...] = ("I", "II", "III")
    reflector: str = "B"
    rings: tuple[int, ...] = (0, 0, 0)
    positions: tuple[int, ...] = (0, 0, 0)
    plugboard: tuple[tuple[str, str], ...] = ()
    model: str = "I"

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        if self.model not in MODELS:
            raise ValueError(f"modelo desconocido: {self.model!r}")
        spec = MODELS[self.model]
        if len(self.rotors) != spec.n_rotors:
            raise ValueError(f"{spec.name} lleva {spec.n_rotors} rotores")
        *greek, a, b, c = self.rotors
        if greek and greek[0] not in spec.greek:
            raise ValueError(f"el rotor de la izquierda de la M4 es Beta o Gamma, no {greek[0]}")
        for name in (a, b, c):
            if name not in spec.rotors:
                raise ValueError(f"{spec.name} no tiene el rotor {name!r}")
        if len({a, b, c}) != 3:
            raise ValueError("los tres rotores deben ser distintos")
        if self.reflector not in spec.reflectors:
            raise ValueError(f"{spec.name} no usa el reflector {self.reflector!r}")
        for values, what in ((self.rings, "anillos"), (self.positions, "posiciones")):
            if len(values) != spec.n_rotors or not all(0 <= v < 26 for v in values):
                raise ValueError(f"{what}: se esperaban {spec.n_rotors} valores entre 0 y 25")
        letters = [x for pair in self.plugboard for x in pair]
        if len(self.plugboard) > MAX_CABLES or len(set(letters)) != len(letters):
            raise ValueError("plugboard inválido: cada letra va en un solo cable (13 como máximo)")
        if any(x not in ALPHABET for x in letters):
            raise ValueError("el plugboard solo admite letras de la A a la Z")

    @classmethod
    def from_strings(
        cls,
        rotors: str,
        reflector: str = "B",
        rings: str = "",
        positions: str = "",
        plugboard: str = "",
        model: str = "I",
    ) -> EnigmaConfig:
        """Desde la notación de una hoja de claves.

        Ejemplo: ``EnigmaConfig.from_strings("II IV V", "B", "02 21 12", "WXC",
        "AV BS CG DL FU HZ IN KM OW RX")``. Anillos y posiciones vacíos valen A.
        """
        names = tuple(rotors.split())
        n = len(names)
        return cls(
            rotors=names,
            reflector=reflector,
            rings=parse_settings(rings or "A" * n, n),
            positions=parse_settings(positions or "A" * n, n),
            plugboard=parse_plugboard(plugboard),
            model=model,
        )

    def with_positions(self, positions: str | tuple[int, ...]) -> EnigmaConfig:
        """La misma clave con otras posiciones iniciales (p. ej. la clave de mensaje)."""
        return replace(self, positions=parse_settings(positions, len(self.rotors)))

    @property
    def ring_letters(self) -> str:
        return "".join(to_letter(v) for v in self.rings)

    @property
    def position_letters(self) -> str:
        return "".join(to_letter(v) for v in self.positions)

    @property
    def plugboard_string(self) -> str:
        return " ".join(a + b for a, b in self.plugboard)

    def describe(self) -> str:
        """Resumen legible: «Enigma I · II-IV-V · reflector B · anillos BUL · …»."""
        cables = self.plugboard_string or "sin cables"
        return (
            f"{MODELS[self.model].name} · {'-'.join(self.rotors)} · reflector {self.reflector}"
            f" · anillos {self.ring_letters} · posición {self.position_letters} · {cables}"
        )

    def to_dict(self) -> dict[str, str]:
        """Clave en texto, como en ``data/reference/test_vectors.json``."""
        return {
            "model": self.model,
            "rotors": " ".join(self.rotors),
            "reflector": self.reflector,
            "rings": self.ring_letters,
            "positions": self.position_letters,
            "plugboard": self.plugboard_string,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> EnigmaConfig:
        return cls.from_strings(
            data["rotors"],
            data.get("reflector", "B"),
            data.get("rings", ""),
            data.get("positions", ""),
            data.get("plugboard", ""),
            data.get("model", "I"),
        )


@dataclass(frozen=True)
class Stage:
    """Una etapa del camino de la corriente y la letra que sale de ella."""

    component: str  # "keyboard", "plugboard", "rotor", "reflector" o "lamp"
    label: str  # «Rotor III», «Reflector B»…
    letter: str
    direction: str  # "in", "forward", "turn", "back" u "out"
    slot: int | None = None  # rotor 0 = el de más a la izquierda


@dataclass(frozen=True)
class LetterTrace:
    """Lo que pasa al pulsar una tecla: el paso de los rotores y el camino de la letra."""

    index: int
    key: str
    lamp: str
    positions_before: str
    positions: str
    stepped: tuple[bool, ...]
    double_step: bool
    stages: tuple[Stage, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def path(self) -> str:
        """El camino en una línea: «A → A → C → D → F → S → S → E → B → B → B»."""
        return " → ".join(stage.letter for stage in self.stages)


class Enigma:
    """Una máquina Enigma con estado: las posiciones de los rotores cambian al cifrar."""

    def __init__(self, config: EnigmaConfig) -> None:
        self.config = config
        specs = [ROTORS[name] for name in config.rotors]
        self._forward = [permutation(s.wiring) for s in specs]
        self._backward = [inverse(p) for p in self._forward]
        self._notches = notch_sets([s.notches for s in specs])
        self._reflector = permutation(REFLECTORS[config.reflector])
        self._plug = list(range(26))
        for a, b in config.plugboard:
            self._plug[to_index(a)], self._plug[to_index(b)] = to_index(b), to_index(a)
        self.positions: tuple[int, ...] = config.positions

    # ------------------------------------------------------------------ estado

    def reset(self) -> None:
        """Vuelve a las posiciones iniciales de la clave."""
        self.positions = self.config.positions

    @property
    def window(self) -> str:
        """Letras que se ven en las ventanas, de izquierda a derecha."""
        return "".join(to_letter(p) for p in self.positions)

    def step(self) -> StepResult:
        """Avanza los rotores un paso (lo que ocurre al pulsar una tecla)."""
        result = step(self.positions, self._notches)
        self.positions = result.positions
        return result

    # ------------------------------------------------------------------ cifrado

    def _rotor(self, x: int, slot: int, table: list[int] | tuple[int, ...]) -> int:
        """Salida del rotor ``slot`` desplazado s = ventana − anillo: W[x + s] − s."""
        shift = self.positions[slot] - self.config.rings[slot]
        return (table[(x + shift) % 26] - shift) % 26

    def _signal(self, x: int, record: list[Stage] | None = None) -> int:
        """Camino de la corriente para la tecla x, con los rotores ya avanzados.

        Si ``record`` es una lista, anota la letra que sale de cada etapa.
        """
        names = self.config.rotors
        last = len(names) - 1

        def note(component: str, label: str, value: int, direction: str, slot: int | None) -> None:
            if record is not None:
                record.append(Stage(component, label, to_letter(value), direction, slot))

        note("keyboard", "Tecla", x, "in", None)
        x = self._plug[x]
        note("plugboard", "Plugboard", x, "forward", None)
        for slot in range(last, -1, -1):
            x = self._rotor(x, slot, self._forward[slot])
            note("rotor", f"Rotor {names[slot]}", x, "forward", slot)
        x = self._reflector[x]
        note("reflector", f"Reflector {self.config.reflector}", x, "turn", None)
        for slot in range(last + 1):
            x = self._rotor(x, slot, self._backward[slot])
            note("rotor", f"Rotor {names[slot]}", x, "back", slot)
        x = self._plug[x]
        note("plugboard", "Plugboard", x, "back", None)
        note("lamp", "Lámpara", x, "out", None)
        return x

    def press(self, key: int) -> int:
        """Pulsa una tecla (0–25): avanza los rotores y devuelve la lámpara que se enciende."""
        self.step()
        return self._signal(key)

    def encrypt(self, text: str) -> str:
        """Cifra (o descifra: es la misma operación) un texto de letras A–Z."""
        return "".join(to_letter(self.press(to_index(c))) for c in clean(text, strict=True))

    def trace(self, text: str) -> list[LetterTrace]:
        """Cifra el texto y devuelve, por letra, el paso de los rotores y cada etapa."""
        traces = []
        for index, letter in enumerate(clean(text, strict=True)):
            before = self.window
            stepped = self.step()
            stages: list[Stage] = []
            lamp = self._signal(to_index(letter), stages)
            traces.append(
                LetterTrace(
                    index=index,
                    key=letter,
                    lamp=to_letter(lamp),
                    positions_before=before,
                    positions=self.window,
                    stepped=stepped.stepped,
                    double_step=stepped.double_step,
                    stages=tuple(stages),
                )
            )
        return traces


def clean(text: str, strict: bool = False) -> str:
    """Deja solo las letras A–Z, en mayúsculas.

    Con ``strict=True`` acepta espacios (los grupos de 5 letras) pero rechaza cualquier
    otro carácter, para no cifrar en silencio algo distinto de lo que se escribió.
    """
    upper = text.upper()
    if strict and re.search(r"[^A-Z\s]", upper):
        raise ValueError("Enigma solo tiene las teclas A–Z (los espacios se ignoran)")
    return re.sub(r"[^A-Z]", "", upper)


def to_machine_letters(text: str) -> str:
    """Lo que se puede teclear en Enigma: A–Z, sin nada más.

    Quita las tildes y diéresis (Á → A, Ü → U), cambia Ñ → N y ß → SS, y descarta
    espacios, números y signos. La normalización del corpus (fase 2) es otra: en
    alemán escribe Ü → UE, como hacían los operadores.
    """
    text = text.replace("ß", "SS").replace("ẞ", "SS")
    decomposed = unicodedata.normalize("NFD", text.upper())
    letters = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    return re.sub(r"[^A-Z]", "", letters)


def groups_of_five(text: str) -> str:
    """Texto en grupos de 5 letras, como se transmitía: «BDZGO EWTYX…»."""
    return " ".join(text[i : i + 5] for i in range(0, len(text), 5))


def encrypt(config: EnigmaConfig, text: str) -> str:
    """Atajo: cifra un texto con una máquina nueva en la clave dada."""
    return Enigma(config).encrypt(text)
