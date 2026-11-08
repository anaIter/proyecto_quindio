import numpy as np
import pytest

from src.r3_hull import mismos_vertices, puntos_cuadrado, quickhull, hull_scipy


def P(lista):
    return np.unique(np.array(lista, dtype=np.int64), axis=0)


def test_cuadrado_con_interiores_y_alineados():
    # cuadrado 0..10; puntos interiores y puntos sobre los lados (no son vértices)
    pts = P([(0, 0), (10, 0), (10, 10), (0, 10), (5, 5), (3, 7), (5, 0), (0, 5), (10, 5), (5, 10)])
    h = quickhull(pts)
    assert {tuple(v) for v in h.tolist()} == {(0, 0), (10, 0), (10, 10), (0, 10)}


def test_antihorario_empieza_en_extremo_izquierdo():
    h = quickhull(P([(0, 0), (4, 0), (4, 4), (0, 4), (2, 2)]))
    assert tuple(h[0]) == (0, 0)
    area2 = sum(h[i][0] * h[(i + 1) % len(h)][1] - h[(i + 1) % len(h)][0] * h[i][1] for i in range(len(h)))
    assert area2 > 0  # área con signo positivo = antihorario


def test_casos_degenerados():
    assert len(quickhull(P([(3, 3)]))) == 1
    assert len(quickhull(P([(0, 0), (5, 5)]))) == 2
    # todos alineados: solo los dos extremos
    h = quickhull(P([(0, 0), (1, 1), (2, 2), (3, 3), (9, 9)]))
    assert {tuple(v) for v in h.tolist()} == {(0, 0), (9, 9)}


def test_triangulo_a_mano():
    h = quickhull(P([(0, 0), (6, 0), (3, 5), (3, 1), (2, 1)]))
    assert {tuple(v) for v in h.tolist()} == {(0, 0), (6, 0), (3, 5)}


def test_empate_en_distancia_maxima():
    # (3,5) y (6,5) a la misma distancia de AB: ambos son vértices
    h = quickhull(P([(0, 0), (10, 0), (3, 5), (6, 5)]))
    assert {tuple(v) for v in h.tolist()} == {(0, 0), (10, 0), (3, 5), (6, 5)}


def test_coordenadas_grandes_no_desbordan():
    base = 9_000_000
    pts = P([(base, base), (base + 80_000, base), (base + 80_000, base + 80_000),
             (base, base + 80_000), (base + 40_000, base + 40_000)])
    assert len(quickhull(pts)) == 4


@pytest.mark.parametrize("semilla", range(8))
def test_contra_scipy_aleatorio(semilla):
    pts = puntos_cuadrado(2000, semilla=semilla, lado=5000)
    assert mismos_vertices(quickhull(pts), hull_scipy(pts))


def test_contra_scipy_malla_muchos_alineados():
    xs, ys = np.meshgrid(np.arange(0, 30), np.arange(0, 20))
    pts = P(np.column_stack([xs.ravel(), ys.ravel()]))
    h = quickhull(pts)
    assert {tuple(v) for v in h.tolist()} == {(0, 0), (29, 0), (29, 19), (0, 19)}
    assert mismos_vertices(h, hull_scipy(pts))


def test_contra_scipy_circulo_muchos_vertices():
    t = np.linspace(0, 2 * np.pi, 400, endpoint=False)
    pts = P(np.column_stack([np.rint(10_000 * np.cos(t)), np.rint(10_000 * np.sin(t))]))
    assert mismos_vertices(quickhull(pts), hull_scipy(pts))
