
"""Servicios de integración para la aplicación R5."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import networkx as nx
import pandas as pd

from src.r2_caminos import Dijkstra, PESO
from src.r4_tsp import experimento_itinerario
from src.r1_red import estimar_memoria


# ---------------------------------------------------------
# Rutas del proyecto
# ---------------------------------------------------------

RAIZ = Path(__file__).resolve().parents[1]

DATA = RAIZ / "data"
RESULTS = RAIZ / "results"
FIGURES = RAIZ / "figures"

ARCHIVO_GRAFO = DATA / "grafo_procesado.graphml"
ARCHIVO_CATALOGO = DATA / "catalogo_con_nodos.csv"


# ---------------------------------------------------------
# Carga de información
# ---------------------------------------------------------

def cargar_catalogo() -> pd.DataFrame:
    """Carga el catálogo de lugares turísticos."""

    if not ARCHIVO_CATALOGO.exists():
        raise FileNotFoundError(
            f"No se encontró el catálogo: {ARCHIVO_CATALOGO}"
        )

    catalogo = pd.read_csv(
        ARCHIVO_CATALOGO,
        dtype={"id": str, "nodo": str}
    )

    columnas = {
        "id",
        "nombre",
        "categoria",
        "lat",
        "lon",
        "nodo"
    }

    faltantes = columnas - set(catalogo.columns)

    if faltantes:
        raise ValueError(
            f"Faltan columnas en el catálogo: {faltantes}"
        )

    return catalogo


def cargar_grafo_y_dijkstra():
    """Carga la red vial y prepara el algoritmo Dijkstra."""

    if not ARCHIVO_GRAFO.exists():
        raise FileNotFoundError(
            f"No se encontró el grafo: {ARCHIVO_GRAFO}"
        )

    grafo = nx.read_graphml(ARCHIVO_GRAFO)

    if not grafo.is_directed():
        raise ValueError("El grafo debe ser dirigido.")

    algoritmo = Dijkstra(grafo, PESO)

    return grafo, algoritmo


# ---------------------------------------------------------
# Búsqueda de lugares
# ---------------------------------------------------------

def buscar_lugar(catalogo, lugar_id):
    """Busca un lugar por su identificador."""

    resultado = catalogo[
        catalogo["id"].astype(str) == str(lugar_id)
    ]

    if resultado.empty:
        raise ValueError(
            f"No existe el lugar con ID {lugar_id}."
        )

    return resultado.iloc[0]


# ---------------------------------------------------------
# Consulta de rutas (R2)
# ---------------------------------------------------------

def consultar_ruta(
    grafo,
    algoritmo,
    catalogo,
    origen_id,
    destino_id
) -> dict[str, Any]:
    """Calcula la ruta vial entre dos lugares."""

    origen = buscar_lugar(catalogo, origen_id)
    destino = buscar_lugar(catalogo, destino_id)

    resultado = algoritmo.heap(
        str(origen["nodo"]),
        str(destino["nodo"])
    )

    if not resultado.ruta or not math.isfinite(resultado.tiempo_s):
        raise ValueError(
            "No se encontró una ruta entre los lugares seleccionados."
        )

    coordenadas = []

    for nodo in resultado.ruta:

        datos = grafo.nodes[nodo]

        latitud = float(datos["y"])
        longitud = float(datos["x"])

        coordenadas.append((latitud, longitud))

    return {
        "origen": origen.to_dict(),
        "destino": destino.to_dict(),
        "tiempo_s": resultado.tiempo_s,
        "tiempo_min": resultado.tiempo_s / 60,
        "ruta_nodos": resultado.ruta,
        "coordenadas": coordenadas,
        "nodos_explorados": resultado.nodos_explorados
    }


# ---------------------------------------------------------
# Envolvente convexa (R3)
# ---------------------------------------------------------

def obtener_envolvente():
    """Obtiene los vértices de la envolvente convexa."""

    archivo = RESULTS / "r3_envolvente_red.json"

    if not archivo.exists():
        raise FileNotFoundError(
            "No se encontró el resultado de la envolvente convexa."
        )

    with open(archivo, "r", encoding="utf-8") as f:
        datos = json.load(f)

    vertices = datos.get("vertices_lonlat", [])

    if len(vertices) < 3:
        raise ValueError(
            "No existen suficientes vértices para dibujar la envolvente."
        )

    # Conversión de longitud/latitud a latitud/longitud.
    return [
        (float(lat), float(lon))
        for lon, lat in vertices
    ]


# ---------------------------------------------------------
# Planificación de itinerarios (R4)
# ---------------------------------------------------------

def calcular_itinerario(
    inicio_id: str,
    atractivos_ids: list[str]
):
    """Genera un itinerario reutilizando las funciones de R4."""

    if not 6 <= len(atractivos_ids) <= 8:
        raise ValueError(
            "Debes seleccionar entre 6 y 8 atractivos."
        )

    if len(set(atractivos_ids)) != len(atractivos_ids):
        raise ValueError(
            "No puedes seleccionar atractivos repetidos."
        )

    return experimento_itinerario(
        inicio_id,
        atractivos_ids
    )


# ---------------------------------------------------------
# Resultados experimentales
# ---------------------------------------------------------

def cargar_resultado_csv(nombre):
    """Carga un archivo CSV de resultados."""

    archivo = RESULTS / nombre

    if not archivo.exists():
        return None

    return pd.read_csv(archivo)


def cargar_resultado_json(nombre):
    """Carga un archivo JSON de resultados."""

    archivo = RESULTS / nombre

    if not archivo.exists():
        return None

    with open(archivo, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------
# Información del catálogo
# ---------------------------------------------------------

def obtener_opciones_inicio(catalogo):
    """Obtiene las cabeceras municipales."""

    return catalogo[
        catalogo["categoria"] == "cabecera"
    ].copy()


def obtener_atractivos(catalogo):
    """Obtiene los atractivos con duración de visita."""

    atractivos = catalogo[
        catalogo["categoria"] == "atractivo"
    ].copy()

    return atractivos.dropna(
        subset=["duracion_visita_min"]
    )


# ---------------------------------------------------------
# Estimación de memoria (R1)
# ---------------------------------------------------------

def tabla_memoria():
    """Calcula la memoria estimada de las estructuras de R1."""

    grafo, _ = cargar_grafo_y_dijkstra()

    estimacion = estimar_memoria(
        grafo.number_of_nodes(),
        grafo.number_of_edges()
    )

    return pd.DataFrame([
        {
            "Estructura": "Matriz de adyacencia",
            "Memoria estimada (MB)": estimacion["matriz_MB"]
        },
        {
            "Estructura": "Listas de adyacencia",
            "Memoria estimada (MB)": estimacion["listas_MB"]
        }
    ])
