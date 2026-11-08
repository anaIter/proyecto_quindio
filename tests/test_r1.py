import networkx as nx
import pandas as pd
import pytest

pytest.importorskip("osmnx")
import osmnx as ox
from src.r1_red import estimar_memoria, ubicar_lugares


def test_memoria():
    r = estimar_memoria(1000, 3000)
    assert r["matriz_MB"] == pytest.approx(8.0)
    assert r["listas_MB"] == pytest.approx(0.08)


def _grafo():
    G = nx.MultiDiGraph(crs="EPSG:4326")
    for n, (x, y) in {1: (-75.68, 4.53), 2: (-75.67, 4.53), 3: (-75.67, 4.54), 4: (-75.60, 4.60)}.items():
        G.add_node(n, x=x, y=y)
    for u, v in [(1, 2), (2, 3), (3, 1), (3, 4)]:  # el nodo 4 no regresa
        G.add_edge(u, v, length=100.0)
    return G


def test_componente_fuerte():
    Gc = ox.truncate.largest_component(_grafo(), strongly=True)
    assert set(Gc.nodes) == {1, 2, 3}
    assert nx.is_strongly_connected(Gc)


def test_ubicar_exacto_y_lejano():
    G = ox.truncate.largest_component(_grafo(), strongly=True)
    cat = pd.DataFrame({"id": ["a", "b"], "nombre": ["a", "b"],
                        "lat": [4.53, 4.55], "lon": [-75.68, -75.68]})
    r = ubicar_lugares(G, cat)
    assert r.loc[0, "dist_nodo_m"] < 1 and not r.loc[0, "lejano"]
    assert r.loc[1, "lejano"]
