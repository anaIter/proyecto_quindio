"""Requerimiento 2: caminos mínimos mediante Dijkstra.

Uso desde la raíz del proyecto:
    python -m src.r2_caminos experimentos
    python -m src.r2_caminos matriz

El peso utilizado es `tiempo_s` (segundos). El grafo de R1 es un
MultiDiGraph; por ello, la lista de adyacencia conserva el menor peso entre
las aristas paralelas que conectan el mismo par de nodos.
"""
from __future__ import annotations

import argparse
import itertools
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import networkx as nx
import pandas as pd

from src.bench import info_maquina, medir

DATA = Path("data")
RESULTS = Path("results")
FIGURES = Path("figures")
GRAFO = DATA / "grafo_procesado.graphml"
CATALOGO = DATA / "catalogo_con_nodos.csv"
PESO = "tiempo_s"


@dataclass
class ResultadoCamino:
    """Resultado de una consulta de camino mínimo."""
    origen: str
    destino: str
    tiempo_s: float
    ruta: list[str]
    nodos_explorados: int


class Dijkstra:
    """Implementa Dijkstra lineal y con heap sin usar algoritmos de NetworkX."""

    def __init__(self, grafo: nx.Graph, peso: str = PESO):
        if not grafo.is_directed():
            raise ValueError("El grafo debe ser dirigido.")
        self.grafo = grafo
        self.peso = peso
        self.adyacencia = self._crear_adyacencia(grafo, peso)
        self.nodos = list(grafo.nodes)

    @staticmethod
    def _crear_adyacencia(grafo: nx.Graph, peso: str) -> dict[str, dict[str, float]]:
        """Convierte el grafo en adyacencia y reduce aristas paralelas al mínimo."""
        ady: dict[str, dict[str, float]] = {n: {} for n in grafo.nodes}
        for u, v, datos in grafo.edges(data=True):
            if peso not in datos:
                raise ValueError(f"La arista ({u}, {v}) no contiene el peso '{peso}'.")
            try:
                valor = float(datos[peso])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Peso no numérico en la arista ({u}, {v}).") from exc
            if not math.isfinite(valor) or valor < 0:
                raise ValueError(f"El peso de ({u}, {v}) debe ser finito y no negativo.")
            anterior = ady[u].get(v)
            if anterior is None or valor < anterior:
                ady[u][v] = valor
        return ady

    def _validar_extremos(self, origen: str, destino: str | None = None) -> None:
        if origen not in self.adyacencia:
            raise ValueError(f"El nodo de origen '{origen}' no existe en el grafo.")
        if destino is not None and destino not in self.adyacencia:
            raise ValueError(f"El nodo de destino '{destino}' no existe en el grafo.")

    @staticmethod
    def _reconstruir_ruta(predecesor: dict[str, str], origen: str,
                          destino: str) -> list[str]:
        if destino != origen and destino not in predecesor:
            return []
        ruta = [destino]
        while ruta[-1] != origen:
            ruta.append(predecesor[ruta[-1]])
        ruta.reverse()
        return ruta

    def lineal(self, origen: str, destino: str) -> ResultadoCamino:
        """Dijkstra con búsqueda lineal del mínimo: O(V² + E)."""
        self._validar_extremos(origen, destino)
        dist = {n: math.inf for n in self.nodos}
        pred: dict[str, str] = {}
        no_visitados = set(self.nodos)
        dist[origen] = 0.0
        explorados = 0

        while no_visitados:
            actual = min(no_visitados, key=dist.__getitem__)
            if math.isinf(dist[actual]):
                break
            no_visitados.remove(actual)
            explorados += 1  # se cuenta una sola vez, al seleccionar el mínimo
            if actual == destino:
                break

            for vecino, costo in self.adyacencia[actual].items():
                if vecino in no_visitados:
                    nueva = dist[actual] + costo
                    if nueva < dist[vecino]:
                        dist[vecino] = nueva
                        pred[vecino] = actual

        return ResultadoCamino(
            origen, destino, dist[destino],
            self._reconstruir_ruta(pred, origen, destino), explorados
        )

    def heap(self, origen: str, destino: str) -> ResultadoCamino:
        """Dijkstra con cola de prioridad: O((V + E) log V)."""
        import heapq

        self._validar_extremos(origen, destino)
        dist = {n: math.inf for n in self.nodos}
        pred: dict[str, str] = {}
        visitados: set[str] = set()
        cola: list[tuple[float, str]] = [(0.0, origen)]
        dist[origen] = 0.0
        explorados = 0

        while cola:
            distancia, actual = heapq.heappop(cola)
            if actual in visitados:
                continue  # entrada antigua de la cola
            visitados.add(actual)
            explorados += 1  # primera extracción válida de este nodo
            if actual == destino:
                break

            for vecino, costo in self.adyacencia[actual].items():
                if vecino in visitados:
                    continue
                nueva = distancia + costo
                if nueva < dist[vecino]:
                    dist[vecino] = nueva
                    pred[vecino] = actual
                    heapq.heappush(cola, (nueva, vecino))

        return ResultadoCamino(
            origen, destino, dist[destino],
            self._reconstruir_ruta(pred, origen, destino), explorados
        )

    def heap_todos(self, origen: str) -> tuple[dict[str, float], int]:
        """Ejecuta Dijkstra con heap hasta agotar la cola (para la matriz)."""
        import heapq

        self._validar_extremos(origen)
        dist = {n: math.inf for n in self.nodos}
        visitados: set[str] = set()
        cola: list[tuple[float, str]] = [(0.0, origen)]
        dist[origen] = 0.0
        explorados = 0
        while cola:
            distancia, actual = heapq.heappop(cola)
            if actual in visitados:
                continue
            visitados.add(actual)
            explorados += 1
            for vecino, costo in self.adyacencia[actual].items():
                if vecino in visitados:
                    continue
                nueva = distancia + costo
                if nueva < dist[vecino]:
                    dist[vecino] = nueva
                    heapq.heappush(cola, (nueva, vecino))
        return dist, explorados


def cargar_datos() -> tuple[nx.MultiDiGraph, pd.DataFrame, Dijkstra]:
    """Carga el grafo procesado y el catálogo asociado de R1."""
    if not GRAFO.exists():
        raise FileNotFoundError(f"No se encontró {GRAFO}. Ejecuta primero R1.")
    if not CATALOGO.exists():
        raise FileNotFoundError(f"No se encontró {CATALOGO}.")
    grafo = nx.read_graphml(GRAFO)
    catalogo = pd.read_csv(CATALOGO, dtype={"id": str, "nodo": str})
    requeridas = {"id", "nombre", "nodo"}
    faltantes = requeridas - set(catalogo.columns)
    if faltantes:
        raise ValueError(f"Faltan columnas en el catálogo: {sorted(faltantes)}")
    if catalogo["nodo"].isna().any():
        raise ValueError("Hay lugares sin nodo asociado en el catálogo.")
    nodos_grafo = set(grafo.nodes)
    fuera = catalogo.loc[~catalogo["nodo"].isin(nodos_grafo), ["id", "nodo"]]
    if not fuera.empty:
        raise ValueError("Hay nodos del catálogo que no están en el grafo:\n" + fuera.to_string(index=False))
    return grafo, catalogo, Dijkstra(grafo, PESO)


def seleccionar_pares_cercanos(catalogo: pd.DataFrame, cantidad: int = 20) -> list[tuple[str, str]]:
    """Selecciona pares geográficamente cercanos sin reutilizar lugares."""
    if not {"lat", "lon"}.issubset(catalogo.columns):
        raise ValueError("El catálogo necesita las columnas lat y lon para seleccionar pares.")
    filas = catalogo.dropna(subset=["lat", "lon"]).to_dict("records")
    candidatos = []
    for a, b in itertools.combinations(filas, 2):
        # Aproximación local en grados: suficiente para ordenar proximidad en Quindío.
        lat_media = (float(a["lat"]) + float(b["lat"])) / 2
        dx = (float(a["lon"]) - float(b["lon"])) * math.cos(math.radians(lat_media))
        dy = float(a["lat"]) - float(b["lat"])
        candidatos.append((dx * dx + dy * dy, str(a["id"]), str(a["nodo"]),
                           str(b["id"]), str(b["nodo"])))
    candidatos.sort()
    usados: set[str] = set()
    pares = []
    for _, id_a, nodo_a, id_b, nodo_b in candidatos:
        if id_a in usados or id_b in usados:
            continue
        pares.append((id_a, nodo_a, id_b, nodo_b))
        usados.update((id_a, id_b))
        if len(pares) == cantidad:
            break
    if len(pares) < cantidad:
        raise ValueError(f"Solo fue posible seleccionar {len(pares)} pares con coordenadas.")
    return [(f"{a}|{na}", f"{b}|{nb}") for a, na, b, nb in pares]


def ejecutar_experimentos() -> pd.DataFrame:
    """Mide heap en 20 pares y lineal en los primeros 10 pares compartidos."""
    _, catalogo, algoritmo = cargar_datos()
    pares = seleccionar_pares_cercanos(catalogo, 20)
    nombres = catalogo.set_index("id")["nombre"].to_dict()
    filas: list[dict[str, Any]] = []

    for i, (origen_info, destino_info) in enumerate(pares):
        id_o, nodo_o = origen_info.split("|", 1)
        id_d, nodo_d = destino_info.split("|", 1)
        res_heap, med_heap, rep_heap = medir(algoritmo.heap, nodo_o, nodo_d)
        fila = {
            "par": i + 1, "origen_id": id_o, "origen": nombres.get(id_o, id_o),
            "destino_id": id_d, "destino": nombres.get(id_d, id_d),
            "heap_tiempo_s": res_heap.tiempo_s,
            "heap_ms": med_heap, "heap_nodos_explorados": res_heap.nodos_explorados,
            "heap_repeticiones_ms": ";".join(f"{x:.6f}" for x in rep_heap),
            "lineal_ms": math.nan, "lineal_nodos_explorados": math.nan,
            "lineal_repeticiones_ms": "", "cociente_lineal_heap": math.nan,
        }
        if i < 10:
            res_lineal, med_lineal, rep_lineal = medir(algoritmo.lineal, nodo_o, nodo_d)
            if not math.isclose(res_heap.tiempo_s, res_lineal.tiempo_s, rel_tol=1e-9, abs_tol=1e-6):
                raise AssertionError(f"Dijkstra no coincide para el par {id_o} -> {id_d}.")
            if res_heap.ruta != res_lineal.ruta and not math.isclose(
                res_heap.tiempo_s, res_lineal.tiempo_s, rel_tol=1e-9, abs_tol=1e-6
            ):
                raise AssertionError("Las rutas obtenidas no tienen el mismo costo.")
            fila.update({
                "lineal_ms": med_lineal,
                "lineal_nodos_explorados": res_lineal.nodos_explorados,
                "lineal_repeticiones_ms": ";".join(f"{x:.6f}" for x in rep_lineal),
                "cociente_lineal_heap": med_lineal / med_heap if med_heap else math.nan,
            })
        filas.append(fila)
        print(f"[{i + 1:02}/20] {id_o} -> {id_d}: heap={med_heap:.3f} ms")

    df = pd.DataFrame(filas)
    RESULTS.mkdir(exist_ok=True)
    df.to_csv(RESULTS / "r2_experimentos.csv", index=False, encoding="utf-8")
    comparables = df["cociente_lineal_heap"].dropna()
    resumen = {
        "pares_heap": len(df), "pares_comparacion": int(comparables.size),
        "cociente_mediana": float(comparables.median()),
        "cociente_minimo": float(comparables.min()),
        "cociente_maximo": float(comparables.max()),
    }
    (RESULTS / "r2_resumen.json").write_text(
        pd.Series({**resumen, **{f"maquina_{k}": v for k, v in info_maquina().items()}})
        .to_json(indent=2, force_ascii=False), encoding="utf-8"
    )
    print("\nResumen lineal / heap:", resumen)
    return df


def generar_matriz() -> pd.DataFrame:
    """Genera la matriz dirigida de tiempos entre todos los lugares del catálogo."""
    _, catalogo, algoritmo = cargar_datos()
    ids = catalogo["id"].astype(str).tolist()
    nodos = catalogo["nodo"].astype(str).tolist()
    matriz = []
    for i, (id_origen, nodo_origen) in enumerate(zip(ids, nodos), start=1):
        distancias, explorados = algoritmo.heap_todos(nodo_origen)
        matriz.append([distancias[nodo_destino] for nodo_destino in nodos])
        print(f"Origen {i}/{len(ids)} ({id_origen}): {explorados} nodos explorados")
    df = pd.DataFrame(matriz, index=ids, columns=ids)
    df.index.name = "origen_id"
    RESULTS.mkdir(exist_ok=True)
    df.to_csv(RESULTS / "r2_matriz_tiempos.csv", encoding="utf-8")
    print(f"Matriz guardada: {RESULTS / 'r2_matriz_tiempos.csv'} ({len(ids)} x {len(ids)})")
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("accion", choices=["experimentos", "matriz"])
    args = parser.parse_args()
    if args.accion == "experimentos":
        ejecutar_experimentos()
    else:
        generar_matriz()


if __name__ == "__main__":
    main()
