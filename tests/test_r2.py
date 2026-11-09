import math

import networkx as nx
import pytest

from src.r2_caminos import Dijkstra


def crear_grafo():
    g = nx.MultiDiGraph()
    g.add_edge("A", "B", tiempo_s=8)
    g.add_edge("A", "B", tiempo_s=3)  # arista paralela: debe elegir 3
    g.add_edge("A", "C", tiempo_s=2)
    g.add_edge("C", "B", tiempo_s=2)
    g.add_edge("B", "D", tiempo_s=1)
    g.add_edge("C", "D", tiempo_s=10)
    g.add_node("Z")
    return g


def test_lineal_y_heap_encuentran_mismo_camino_minimo():
    d = Dijkstra(crear_grafo())
    lineal = d.lineal("A", "D")
    heap = d.heap("A", "D")
    assert lineal.tiempo_s == pytest.approx(4)
    assert heap.tiempo_s == pytest.approx(4)
    assert lineal.ruta == ["A", "B", "D"]
    assert heap.ruta == ["A", "B", "D"]


def test_origen_igual_destino():
    d = Dijkstra(crear_grafo())
    for resultado in (d.lineal("A", "A"), d.heap("A", "A")):
        assert resultado.tiempo_s == 0
        assert resultado.ruta == ["A"]
        assert resultado.nodos_explorados == 1


def test_destino_inalcanzable():
    d = Dijkstra(crear_grafo())
    for resultado in (d.lineal("A", "Z"), d.heap("A", "Z")):
        assert math.isinf(resultado.tiempo_s)
        assert resultado.ruta == []


def test_rechaza_pesos_negativos():
    g = nx.DiGraph()
    g.add_edge("A", "B", tiempo_s=-1)
    with pytest.raises(ValueError, match="no negativo"):
        Dijkstra(g)


def test_rechaza_nodo_inexistente():
    d = Dijkstra(crear_grafo())
    with pytest.raises(ValueError, match="no existe"):
        d.heap("NO", "A")
