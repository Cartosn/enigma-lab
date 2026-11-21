#!/usr/bin/env python3
"""Piloto para la propuesta: simulador mínimo de Enigma I y verificaciones.

Comprueba con código las cifras que cita la propuesta:
  1. Vectores de prueba conocidos (AAAAA -> BDZGO; doble paso ADU->ADV->AEW->BFX).
  2. Propiedades: ninguna letra se cifra a sí misma; cifrar = descifrar.
  3. Periodo del odómetro de rotores (doble paso).
  4. Espacio de claves exacto y combinaciones del plugboard.
  5. Monte Carlo: fracción de alineaciones falsas de un crib que sobreviven
     al filtro "ninguna letra se cifra a sí misma", contra (25/26)^L.
"""
import csv
import math
import random
from math import factorial, log2

import numpy as np

A = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
ROTORS = {
    'I':   ('EKMFLGDQVZNTOWYHXUSPAIBRCJ', 'Q'),
    'II':  ('AJDKSIRUXBLHWTMCQGZNPYFVOE', 'E'),
    'III': ('BDFHJLCPRTXVZNYEIWGAKMUSQO', 'V'),
    'IV':  ('ESOVPZJAYQUIRHXLNFTGKDCMWB', 'J'),
    'V':   ('VZBRGITYUPSDNHLXAWMJQOFECK', 'Z'),
}
REFLECTORS = {'B': 'YRUHQSLDPXNGOKMIEBFZCWVJAT',
              'C': 'FVPJIAOYEDRZXWGCTKUQSBNMHL'}


class Enigma:
    """Enigma I: 3 rotores (izq, centro, der), reflector fijo, plugboard."""

    def __init__(self, rotors=('I', 'II', 'III'), reflector='B',
                 rings='AAA', start='AAA', plugs=''):
        self.fw = [[A.index(c) for c in ROTORS[r][0]] for r in rotors]
        self.bw = []
        for w in self.fw:
            inv = [0] * 26
            for i, o in enumerate(w):
                inv[o] = i
            self.bw.append(inv)
        self.notch = [A.index(ROTORS[r][1]) for r in rotors]
        self.refl = [A.index(c) for c in REFLECTORS[reflector]]
        self.ring = [A.index(c) for c in rings]
        self.pos = [A.index(c) for c in start]
        self.plug = list(range(26))
        for pair in plugs.split():
            a, b = A.index(pair[0]), A.index(pair[1])
            self.plug[a], self.plug[b] = b, a

    def step(self):
        # 0 = izquierdo, 1 = central, 2 = derecho
        if self.pos[1] == self.notch[1]:          # doble paso del central
            self.pos[1] = (self.pos[1] + 1) % 26
            self.pos[0] = (self.pos[0] + 1) % 26
        elif self.pos[2] == self.notch[2]:
            self.pos[1] = (self.pos[1] + 1) % 26
        self.pos[2] = (self.pos[2] + 1) % 26

    def _through(self, x, i, table):
        s = self.pos[i] - self.ring[i]
        return (table[(x + s) % 26] - s) % 26

    def press(self, c):
        self.step()
        x = self.plug[c]
        for i in (2, 1, 0):
            x = self._through(x, i, self.fw[i])
        x = self.refl[x]
        for i in (0, 1, 2):
            x = self._through(x, i, self.bw[i])
        return self.plug[x]

    def encrypt(self, text):
        return ''.join(A[self.press(A.index(ch))] for ch in text)

    def window(self):
        return ''.join(A[p] for p in self.pos)


def random_key(rng, n_plugs=10):
    rotors = tuple(rng.sample(list(ROTORS), 3))
    rings = ''.join(rng.choice(A) for _ in range(3))
    start = ''.join(rng.choice(A) for _ in range(3))
    letters = rng.sample(A, 2 * n_plugs)
    plugs = ' '.join(letters[2 * i] + letters[2 * i + 1] for i in range(n_plugs))
    return dict(rotors=rotors, reflector='B', rings=rings, start=start, plugs=plugs)


def plugboard(k, n=26):
    """Formas de conectar k cables en un plugboard de n letras."""
    return factorial(n) // (factorial(n - 2 * k) * factorial(k) * 2 ** k)


def main():
    rng = random.Random(20261120)

    print('== 1. Vectores de prueba ==')
    out = Enigma().encrypt('AAAAA')
    print('I-II-III, UKW-B, anillos AAA, inicio AAA: AAAAA ->', out, '| esperado BDZGO |', out == 'BDZGO')
    e = Enigma(start='ADU')
    seq = [e.window()]
    for _ in range(4):
        e.press(0)
        seq.append(e.window())
    print('Doble paso desde ADU:', ' -> '.join(seq), '| esperado ADU -> ADV -> AEW -> BFX -> BFY |',
          seq == ['ADU', 'ADV', 'AEW', 'BFX', 'BFY'])

    print('\n== 2. Propiedades estructurales ==')
    fixed_points = 0
    reciprocity_ok = True
    n_letters = 0
    for _ in range(2000):
        k = random_key(rng)
        msg = ''.join(rng.choice(A) for _ in range(100))
        ct = Enigma(**k).encrypt(msg)
        back = Enigma(**k).encrypt(ct)
        fixed_points += sum(p == c for p, c in zip(msg, ct))
        reciprocity_ok &= (back == msg)
        n_letters += len(msg)
    print(f'{n_letters:,} letras cifradas con 2000 claves aleatorias: letras cifradas a sí mismas = {fixed_points}')
    print('Cifrar dos veces devuelve el original (involución):', reciprocity_ok)

    print('\n== 3. Periodo del odómetro ==')
    e = Enigma(start='AAA')
    for _ in range(20000):          # entrar al ciclo
        e.step()
    s0 = tuple(e.pos)
    period = 0
    states = set()
    while True:
        states.add(tuple(e.pos))
        e.step()
        period += 1
        if tuple(e.pos) == s0:
            break
    print('Periodo =', period, '| 26*25*26 =', 26 * 25 * 26, '| 26^3 =', 26 ** 3,
          '| estados fuera del ciclo =', 26 ** 3 - len(states))

    print('\n== 4. Espacio de claves (Enigma I, 3 de 5 rotores, 10 cables) ==')
    orders = 5 * 4 * 3
    positions = 26 ** 3
    rings_eff = 26 ** 2
    p10 = plugboard(10)
    no_rings = orders * positions * p10
    with_rings = no_rings * rings_eff
    print('Orden de rotores:', orders)
    print('Posiciones iniciales:', positions)
    print('Anillos que importan (central y derecho):', rings_eff)
    print('Plugboard con 10 cables:', f'{p10:,}')
    print('Total sin anillos:', f'{no_rings:,}', f'= {no_rings:.4e} = 2^{log2(no_rings):.2f}')
    print('Total con anillos:', f'{with_rings:,}', f'= {with_rings:.4e} = 2^{log2(with_rings):.2f}')
    print('Lo que barre la Bombe (orden x posiciones):', f'{orders * positions:,}', f'= 2^{log2(orders * positions):.2f}')
    print('Naval M3, 3 de 8 rotores:', 8 * 7 * 6, 'órdenes')
    print('Plugboard por número de cables:')
    for k in range(14):
        print(f'  {k:2d} cables: {plugboard(k):>22,}')
    best = max(range(14), key=plugboard)
    print('Máximo en', best, 'cables')

    print('\n== 5. Monte Carlo de cribs ==')
    lengths = [5, 10, 13, 16, 20, 25, 30, 40, 50]
    trials = 1000
    N = 250
    rows = []
    true_alignment_always_survives = True
    for L in lengths:
        fracs = []
        for _ in range(trials):
            k = random_key(rng)
            pt = [rng.choice(A) for _ in range(N)]
            crib = [rng.choice(A) for _ in range(L)]
            t = rng.randrange(N - L + 1)
            pt[t:t + L] = crib
            ct = Enigma(**k).encrypt(''.join(pt))
            ct_arr = np.frombuffer(ct.encode(), dtype=np.uint8)
            crib_arr = np.frombuffer(''.join(crib).encode(), dtype=np.uint8)
            win = np.lib.stride_tricks.sliding_window_view(ct_arr, L)
            survives = ~(win == crib_arr).any(axis=1)
            true_alignment_always_survives &= bool(survives[t])
            wrong = np.delete(survives, t)
            fracs.append(wrong.mean())
        mean = float(np.mean(fracs))
        half = 1.96 * float(np.std(fracs, ddof=1)) / math.sqrt(trials)
        theory = (25 / 26) ** L
        rows.append(dict(L=L, simulado=round(mean, 4), ic_bajo=round(mean - half, 4),
                         ic_alto=round(mean + half, 4), teorico=round(theory, 4)))
        print(f'L={L:2d}: simulado {mean:.4f} (IC95 ±{half:.4f}) | teórico (25/26)^L = {theory:.4f}')
    print('La alineación correcta sobrevive siempre:', true_alignment_always_survives)
    with open('crib_montecarlo.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    print('\n== 6. Distinguidor por puntos fijos ==')
    for L in (26, 50, 100):
        print(f'P(permutaciones aleatorias sin ningún punto fijo en {L} letras) = (25/26)^{L} = {(25 / 26) ** L:.4f}')


if __name__ == '__main__':
    main()
