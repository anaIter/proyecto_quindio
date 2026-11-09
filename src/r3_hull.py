"""Requerimiento 3: envolvente convexa de la red vial.

Algoritmo propio: QuickHull (divide y vencerás).
  - Divide: el segmento AB (extremos izquierdo y derecho) separa los puntos en
    "debajo" y "encima"; el punto más lejano C de cada lado parte el problema
    en dos subproblemas (los puntos fuera de AC y fuera de CB).
  - Vence: los puntos dentro del triángulo ACB se descartan.
  - Combina: concatenar A, hull(A,C), C, hull(C,B), B, ...
  Tiempo esperado O(n log n) con h pequeño (O(n h) en general), peor caso O(n^2).
  Memoria O(n). CITAR FUENTE en el informe (p. ej. Barber, Dobkin & Huhdanpaa 1996,
  "The Quickhull algorithm for convex hulls"; CLRS cap. 33 para geometría).

Coordenadas: UTM 18N (EPSG:32618), redondeadas a entero, sin repetidos, int64.
Los puntos alineados sobre un lado NO se cuentan como vértices (solo se
consideran puntos con producto cruz estrictamente distinto de cero).

Uso:  python -m src.r3_hull experimento
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.spatial import ConvexHull

from src.bench import info_maquina, medir

RESULTS = Path("results")
RED_PROCESADA = Path("data/grafo_procesado.graphml")
SEMILLA = 42
LADO_CUADRADO_M = 100_000
TAMANOS = [1_000, 10_000, 50_000]

_A_UTM = Transformer.from_crs("EPSG:4326", "EPSG:32618", always_xy=True)
_A_GEO = Transformer.from_crs("EPSG:32618", "EPSG:4326", always_xy=True)


# ------------------------------------------------------------ preparación (NO se mide)
def a_enteros_utm(lons, lats) -> np.ndarray:
    """(lon, lat) -> array (m, 2) int64 en metros UTM 18N, redondeado y sin repetidos."""
    x, y = _A_UTM.transform(np.asarray(lons, float), np.asarray(lats, float))
    pts = np.rint(np.column_stack([x, y])).astype(np.int64)
    return np.unique(pts, axis=0)


def puntos_de_red(G) -> np.ndarray:
    lons = [d["x"] for _, d in G.nodes(data=True)]
    lats = [d["y"] for _, d in G.nodes(data=True)]
    return a_enteros_utm(lons, lats)


def puntos_cuadrado(n: int, semilla: int = SEMILLA, lado: int = LADO_CUADRADO_M) -> np.ndarray:
    rng = np.random.default_rng(semilla)
    pts = np.rint(rng.uniform(0, lado, size=(n, 2))).astype(np.int64)
    return np.unique(pts, axis=0)


# ------------------------------------------------------------ algoritmo propio
def _cruz(p, q, pts):
    """Producto cruz (q-p) x (r-p) para cada r en pts. int64: con diferencias
    < 1e7 m el resultado es < 2e14, lejos del desborde (9.2e18)."""
    return (q[0] - p[0]) * (pts[:, 1] - p[1]) - (q[1] - p[1]) * (pts[:, 0] - p[0])


def quickhull(pts: np.ndarray) -> np.ndarray:
    """Vértices de la envolvente en sentido antihorario, empezando en el punto
    más a la izquierda. Sin puntos alineados. Entrada: (n, 2) int64 sin repetidos."""
    pts = np.asarray(pts, dtype=np.int64)
    n = len(pts)
    if n == 0:
        return pts.reshape(0, 2)
    if n == 1:
        return pts.copy()
    # extremos: menor (x, y) y mayor (x, y)
    i_a = np.lexsort((pts[:, 1], pts[:, 0]))[0]
    i_b = np.lexsort((pts[:, 1], pts[:, 0]))[-1]
    A, B = pts[i_a], pts[i_b]

    salida = [A]
    # pila explícita (evita límite de recursión): ("seg", pts, P, Q) o ("pt", C)
    # Para cada segmento dirigido P->Q solo interesan los puntos a su DERECHA
    # (afuera de la envolvente antihoraria).
    for P, Q in ((A, B), (B, A)):
        derecha = pts[_cruz(P, Q, pts) < 0]
        pila = [("seg", derecha, P, Q)]
        while pila:
            tipo, *datos = pila.pop()
            if tipo == "pt":
                salida.append(datos[0])
                continue
            sub, p, q = datos
            if len(sub) == 0:
                continue
            c = sub[np.argmin(_cruz(p, q, sub))]       # más lejano (cruz más negativo)
            izq = sub[_cruz(p, c, sub) < 0]            # fuera de P->C
            der = sub[_cruz(c, q, sub) < 0]            # fuera de C->Q
            pila.append(("seg", der, c, q))
            pila.append(("pt", c))
            pila.append(("seg", izq, p, c))
        if P is A:
            salida.append(B)
    return np.array(salida, dtype=np.int64)


# ------------------------------------------------------------ SciPy (comparación)
def hull_scipy(pts: np.ndarray) -> np.ndarray:
    return pts[ConvexHull(pts.astype(float)).vertices]


def mismos_vertices(a: np.ndarray, b: np.ndarray) -> bool:
    return {tuple(v) for v in a.tolist()} == {tuple(v) for v in b.tolist()}


# ------------------------------------------------------------ experimento
def cmd_experimento():
    import osmnx as ox
    RESULTS.mkdir(exist_ok=True)
    G = ox.load_graphml(RED_PROCESADA)
    conjuntos = [("Nodos de la red", puntos_de_red(G))]
    conjuntos += [(f"Cuadrado, {n:,} puntos".replace(",", " "), puntos_cuadrado(n)) for n in TAMANOS]

    filas = []
    for nombre, pts in conjuntos:
        h_propio, ms_propio, t_propio = medir(quickhull, pts)
        h_scipy, ms_scipy, t_scipy = medir(hull_scipy, pts)
        ok = mismos_vertices(h_propio, h_scipy)
        filas.append({"Conjunto de puntos": nombre, "n": len(pts),
                      "Vértices de la envolvente": len(h_propio),
                      "Tiempo propio (ms)": ms_propio, "Tiempo SciPy (ms)": ms_scipy,
                      "Cociente": ms_propio / ms_scipy, "Coinciden vértices": ok,
                      "Propio min (ms)": min(t_propio), "Propio max (ms)": max(t_propio),
                      "SciPy min (ms)": min(t_scipy), "SciPy max (ms)": max(t_scipy)})
        print(filas[-1])
        if nombre == "Nodos de la red":  # para dibujarla en la app (R5)
            lon, lat = _A_GEO.transform(h_propio[:, 0].astype(float), h_propio[:, 1].astype(float))
            (RESULTS / "r3_envolvente_red.json").write_text(
                json.dumps({"vertices_lonlat": [[float(a), float(b)] for a, b in zip(lon, lat)]}))
    pd.DataFrame(filas).to_csv(RESULTS / "r3_tiempos.csv", index=False)
    (RESULTS / "maquina_r3.json").write_text(json.dumps(info_maquina(), indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("accion", choices=["experimento"])
    ap.parse_args()
    cmd_experimento()