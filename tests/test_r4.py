import itertools
import math
import random

import pytest

from src.r4_tsp import (costo_recorrido, fuerza_bruta, held_karp, itinerario_dia,
                        memoria_held_karp_bytes, vecino_mas_cercano)

# Caso resuelto a mano (asimétrico). Inicio = 0, lugares = [1, 2, 3].
# Óptimo: 0->1->2->3->0 = 1 + 1 + 1 + 1 = 4.
MANO = [
    [0, 1, 9, 9],
    [9, 0, 1, 9],
    [9, 9, 0, 1],
    [1, 9, 9, 0],
]


def matriz_aleatoria(n, semilla):
    rng = random.Random(semilla)
    return [[0 if i == j else rng.randint(1, 100) for j in range(n)] for i in range(n)]


def test_caso_a_mano():
    for algoritmo in (fuerza_bruta, held_karp):
        r = algoritmo(MANO, 0, [1, 2, 3])
        assert r.costo_s == 4
        assert r.orden == [0, 1, 2, 3, 0]


def test_asimetria_importa():
    # El recorrido inverso cuesta 9*4 = 36, no 4.
    assert costo_recorrido(MANO, [0, 3, 2, 1, 0]) == 36


@pytest.mark.parametrize("k", [1, 2, 3, 4, 5, 6, 7])
@pytest.mark.parametrize("semilla", range(5))
def test_held_karp_igual_a_fuerza_bruta(k, semilla):
    d = matriz_aleatoria(k + 1, 100 * k + semilla)
    fb = fuerza_bruta(d, 0, list(range(1, k + 1)))
    hk = held_karp(d, 0, list(range(1, k + 1)))
    assert hk.costo_s == fb.costo_s


@pytest.mark.parametrize("semilla", range(10))
def test_held_karp_devuelve_recorrido_valido_y_consistente(semilla):
    d = matriz_aleatoria(8, semilla)
    lugares = [1, 2, 4, 5, 7]
    r = held_karp(d, 3, lugares)
    assert r.orden[0] == r.orden[-1] == 3
    assert sorted(r.orden[1:-1]) == sorted(lugares)
    assert costo_recorrido(d, r.orden) == r.costo_s


def test_held_karp_es_optimo_frente_a_todas_las_permutaciones():
    d = matriz_aleatoria(7, 7)
    lugares = [1, 2, 3, 4, 5, 6]
    mejor = min(costo_recorrido(d, [0, *p, 0]) for p in itertools.permutations(lugares))
    assert held_karp(d, 0, lugares).costo_s == mejor


def test_casos_pequenos():
    d = matriz_aleatoria(3, 1)
    assert held_karp(d, 0, []).orden == [0, 0]
    assert fuerza_bruta(d, 0, []).costo_s == 0
    r = held_karp(d, 0, [2])
    assert r.orden == [0, 2, 0] and r.costo_s == d[0][2] + d[2][0]


def test_voraz_valido_y_no_mejor_que_el_optimo():
    for semilla in range(20):
        d = matriz_aleatoria(9, semilla)
        lugares = [1, 2, 3, 4, 5, 6, 7, 8]
        v = vecino_mas_cercano(d, 0, lugares)
        o = held_karp(d, 0, lugares)
        assert v.orden[0] == v.orden[-1] == 0
        assert sorted(v.orden[1:-1]) == lugares
        assert costo_recorrido(d, v.orden) == pytest.approx(v.costo_s)
        assert v.costo_s >= o.costo_s


def test_voraz_no_siempre_es_optimo():
    # Desde 0 el voraz va a 1 (cuesta 1) y luego a 3 (cuesta 3), pero desde 3
    # solo queda 2 por 50 y de 2 al inicio otros 50 (total 104). El óptimo
    # 0->1->2->3->0 cuesta 1+50+1+1 = 53.
    d = [
        [0, 1, 2, 50],
        [50, 0, 50, 3],
        [50, 50, 0, 1],
        [1, 50, 50, 0],
    ]
    v = vecino_mas_cercano(d, 0, [1, 2, 3])
    o = held_karp(d, 0, [1, 2, 3])
    assert v.orden == [0, 1, 3, 2, 0]
    assert v.costo_s == 1 + 3 + 50 + 50
    assert o.orden == [0, 1, 2, 3, 0]
    assert o.costo_s == 1 + 50 + 1 + 1
    assert o.costo_s < v.costo_s


def test_memoria_held_karp():
    assert memoria_held_karp_bytes(12) == (1 << 12) * 12 * 9


def test_itinerario_quita_atractivos_hasta_caber():
    # 4 atractivos (120, 120, 120 y 300 min), viajes de 10 min (600 s) entre cualquier par.
    n = 5
    d = [[0 if i == j else 600 for j in range(n)] for i in range(n)]
    dur = {1: 120, 2: 120, 3: 120, 4: 300}
    r = itinerario_dia(d, 0, [1, 2, 3, 4], dur, jornada_min=400)
    assert r["inicial"]["total_min"] == pytest.approx(660 + 50)
    assert r["quitados"][0]["atractivo"] == 4   # el que más tiempo libera
    assert r["final"]["cabe"]
    assert r["final"]["total_min"] <= 400
    assert r["final"]["orden"][0] == r["final"]["orden"][-1] == 0


def test_itinerario_que_ya_cabe_no_quita_nada():
    d = [[0 if i == j else 60 for j in range(4)] for i in range(4)]
    r = itinerario_dia(d, 0, [1, 2, 3], {1: 30, 2: 30, 3: 30}, jornada_min=660)
    assert r["quitados"] == []
    assert r["final"]["cabe"]