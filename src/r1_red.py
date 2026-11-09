"""Requerimiento 1: modelo de la red vial.

Uso (desde la raíz del repo):
    python -m src.r1_red descargar     # baja la red, agrega pesos, guarda data/red_completa.graphml
    python -m src.r1_red memoria       # estimación matriz vs listas (punto 1)
    python -m src.r1_red escalado      # tiempos de largest_component (punto 3)
    python -m src.r1_red ubicar        # nodo más cercano de cada lugar (punto 4)
    python -m src.r1_red procesar      # guarda la componente + tamaños antes/después (punto 5)
"""
import argparse
import datetime
import json
import sys
import time
from pathlib import Path

import numpy as np
import osmnx as ox
import pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree

from src.bench import info_maquina, medir

DATA = Path("data")
RESULTS = Path("results")
RED_COMPLETA = DATA / "red_completa.graphml"
RED_PROCESADA = DATA / "grafo_procesado.graphml"
CATALOGO = DATA / "catalogo.csv"
CATALOGO_NODOS = DATA / "catalogo_con_nodos.csv"

PLAZA_BOLIVAR = (4.5339, -75.6811)  # (lat, lon) aproximada: VERIFICAR en un mapa
RADIOS_M = [2000, 5000, 10000, 20000]
UMBRAL_LEJANO_M = 500


# ---------------------------------------------------------------- descarga y pesos
def agregar_pesos(G):
    """Agrega a cada arista: distancia_m y tiempo_s.

    Velocidad: OSMnx usa el atributo maxspeed de OSM cuando existe; para los
    tramos sin él imputa el promedio de maxspeed de las aristas del mismo tipo
    de vía (highway), y si no hay ninguna de ese tipo usa `fallback` km/h.
    Documentar en el informe cuántas aristas tenían maxspeed real.
    """
    add_speeds = getattr(ox, "routing", ox).add_edge_speeds
    add_times = getattr(ox, "routing", ox).add_edge_travel_times
    con_maxspeed = sum(1 for *_, d in G.edges(data=True) if "maxspeed" in d)
    G = add_speeds(G, fallback=30)  # km/h para tipos sin ningún dato
    G = add_times(G)               # travel_time en segundos = length / speed
    for _, _, d in G.edges(data=True):
        d["distancia_m"] = float(d["length"])
        d["tiempo_s"] = float(d["travel_time"])
    print(f"Aristas con maxspeed en OSM: {con_maxspeed} de {G.number_of_edges()}")
    return G


def descargar():
    DATA.mkdir(exist_ok=True)
    G = ox.graph_from_place("Quindío, Colombia", network_type="drive")
    G = agregar_pesos(G)
    ox.save_graphml(G, RED_COMPLETA)
    meta = {"fecha_descarga": datetime.date.today().isoformat(),
            "osmnx": ox.__version__, "nodos": G.number_of_nodes(),
            "aristas": G.number_of_edges()}
    (DATA / "descarga_meta.json").write_text(json.dumps(meta, indent=2))
    print(meta)


def cargar(path=RED_COMPLETA):
    return ox.load_graphml(path)


# ---------------------------------------------------------------- punto 1: memoria
def estimar_memoria(V, E, bytes_celda=8, bytes_entrada=24, bytes_puntero=8):
    """MB (1 MB = 1e6 B).

    Supuestos:
    - Matriz: V*V celdas de float64 (un solo peso). Con dos pesos, duplicar.
    - Listas: por arista, 8 B id destino + 8 B distancia + 8 B tiempo = 24 B,
      más un puntero/cabecera de lista por nodo. Ignora overhead de Python.
    """
    matriz = V * V * bytes_celda / 1e6
    listas = (E * bytes_entrada + V * bytes_puntero) / 1e6
    return {"V": V, "E": E, "matriz_MB": matriz, "listas_MB": listas}


def cmd_memoria():
    G = cargar()
    r = estimar_memoria(G.number_of_nodes(), G.number_of_edges())
    print(json.dumps(r, indent=2))


# ---------------------------------------------------------------- punto 3: escalado
def _con_reintentos(fn, intentos=6, espera_s=20):
    """Reintenta con espera exponencial (20, 40, 80... s) si Overpass está saturado."""
    for i in range(intentos):
        try:
            return fn()
        except Exception as e:
            if i == intentos - 1:
                raise
            print(f"  descarga fallida ({type(e).__name__}); reintento {i + 1}/{intentos - 1} en {espera_s} s")
            time.sleep(espera_s)
            espera_s *= 2


def cmd_escalado():
    RESULTS.mkdir(exist_ok=True)
    salida = RESULTS / "r1_tiempo_componente.csv"
    filas = []

    def registrar(nombre, G):
        Gc, ms, tiempos = medir(ox.truncate.largest_component, G, strongly=True)
        V, E = G.number_of_nodes(), G.number_of_edges()
        filas.append({"Red": nombre, "V": V, "E": E, "V+E": V + E, "Tiempo (ms)": ms,
                      "Min (ms)": min(tiempos), "Max (ms)": max(tiempos),
                      "V componente": Gc.number_of_nodes(), "E componente": Gc.number_of_edges()})
        print(filas[-1])
        pd.DataFrame(filas).to_csv(salida, index=False)  # guarda tras cada red

    for r in RADIOS_M:
        # la descarga NO se mide; OSMnx reutiliza la carpeta cache/ si ya se bajó
        G = _con_reintentos(lambda: ox.graph_from_point(PLAZA_BOLIVAR, dist=r, network_type="drive"))
        registrar(f"Radio de {r // 1000} km", G)
    registrar("Departamento completo", cargar())
    (RESULTS / "maquina_r1.json").write_text(json.dumps(info_maquina(), indent=2))


# ---------------------------------------------------------------- punto 4: ubicar lugares
def ubicar_lugares(G, catalogo: pd.DataFrame):
    """Nodo más cercano en línea recta, en metros (UTM 18N, EPSG:32618).

    """
    tr = Transformer.from_crs("EPSG:4326", "EPSG:32618", always_xy=True)
    ids = list(G.nodes)
    nx_, ny_ = tr.transform([G.nodes[n]["x"] for n in ids], [G.nodes[n]["y"] for n in ids])
    arbol = cKDTree(np.column_stack([nx_, ny_]))
    px, py = tr.transform(catalogo["lon"].to_numpy(), catalogo["lat"].to_numpy())
    dist, idx = arbol.query(np.column_stack([px, py]))
    out = catalogo.copy()
    out["nodo"] = [ids[i] for i in idx]
    out["dist_nodo_m"] = dist
    out["lejano"] = out["dist_nodo_m"] > UMBRAL_LEJANO_M
    return out


def cmd_ubicar():
    G = ox.truncate.largest_component(cargar(), strongly=True)
    cat = pd.read_csv(CATALOGO)
    res = ubicar_lugares(G, cat)
    res.to_csv(CATALOGO_NODOS, index=False)
    lejanos = res[res["lejano"]]
    print(f"{len(lejanos)} lugares a más de {UMBRAL_LEJANO_M} m de su nodo:")
    print(lejanos[["id", "nombre", "dist_nodo_m"]].to_string(index=False))


# ---------------------------------------------------------------- punto 5: procesar
def cmd_procesar():
    G = cargar()
    Gc = ox.truncate.largest_component(G, strongly=True)
    ox.save_graphml(Gc, RED_PROCESADA)
    tam = pd.DataFrame([
        {"Red": "Red descargada", "Nodos": G.number_of_nodes(), "Aristas": G.number_of_edges()},
        {"Red": "Componente fuertemente conexa", "Nodos": Gc.number_of_nodes(), "Aristas": Gc.number_of_edges()},
    ])
    RESULTS.mkdir(exist_ok=True)
    tam.to_csv(RESULTS / "r1_tamano_red.csv", index=False)
    print(tam.to_string(index=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("accion", choices=["descargar", "memoria", "escalado", "ubicar", "procesar"])
    a = ap.parse_args()
    {"descargar": descargar, "memoria": cmd_memoria, "escalado": cmd_escalado,
     "ubicar": cmd_ubicar, "procesar": cmd_procesar}[a.accion]()