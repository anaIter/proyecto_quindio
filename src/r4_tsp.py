"""Requerimiento 4: ruta óptima de recorrido (TSP asimétrico).

Uso desde la raíz del proyecto:
    python -m src.r4_tsp tiempos      # fuerza bruta vs Held-Karp, k = 5..12
    python -m src.r4_tsp calidad      # heurística voraz vs óptimo (k = 5, 8, 10, 12)
    python -m src.r4_tsp itinerario   # itinerario de un día (11 h)
    python -m src.r4_tsp ejemplo      # ejemplo donde el voraz no es óptimo
    python -m src.r4_tsp todo

Entrada: results/r2_matriz_tiempos.csv (segundos, dirigida) y
data/catalogo_con_nodos.csv. Los recorridos se representan con índices de la
matriz y siempre empiezan y terminan en el lugar de partida.

Algoritmos (implementación propia):
  - fuerza_bruta: todas las permutaciones de los k lugares. O(k! * k) tiempo, O(k) memoria.
  - held_karp: DP sobre subconjuntos. O(2^k * k^2) tiempo, O(2^k * k) memoria.
  - vecino_mas_cercano: heurística voraz. O(k^2) tiempo, O(k) memoria.
Fuentes sugeridas para el informe: Held & Karp (1962), "A Dynamic Programming
Approach to Sequencing Problems"; Cormen et al., Introduction to Algorithms
(NP-completitud del viajante); Rosenkrantz, Stearns & Lewis (1977) para la
heurística del vecino más cercano.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import random
import tracemalloc
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.bench import LIMITE_S, UMBRAL_UNA_VEZ_S, ejecutar_con_limite, info_maquina, medir

DATA = Path("data")
RESULTS = Path("results")
MATRIZ = RESULTS / "r2_matriz_tiempos.csv"
CATALOGO = DATA / "catalogo_con_nodos.csv"

INICIO_ID = "C01"          # Armenia (plaza de Bolívar)
SEMILLA = 42               # semilla fija de todos los experimentos de R4
K_MIN, K_MAX = 5, 12
JORNADA_MIN = 11 * 60      # 660 minutos
ITINERARIO_DEFECTO = ["A01", "A04", "A05", "A07", "A08", "A11", "A06", "A03"]


@dataclass
class ResultadoTSP:
    """Recorrido cerrado: `orden` incluye el inicio al principio y al final."""
    costo_s: float
    orden: list[int]


# ----------------------------------------------------------------------------
# Algoritmos
# ----------------------------------------------------------------------------
def costo_recorrido(d: list[list[float]], orden: list[int]) -> float:
    """Suma d[i][j] a lo largo de un recorrido ya cerrado."""
    return sum(d[orden[i]][orden[i + 1]] for i in range(len(orden) - 1))


def fuerza_bruta(d: list[list[float]], inicio: int, lugares: list[int]) -> ResultadoTSP:
    """Prueba las k! permutaciones de `lugares`. O(k! * k)."""
    if not lugares:
        return ResultadoTSP(0.0, [inicio, inicio])
    mejor = math.inf
    mejor_perm: tuple[int, ...] = ()
    d_ini = d[inicio]
    for perm in itertools.permutations(lugares):
        costo = d_ini[perm[0]]
        anterior = perm[0]
        for x in perm[1:]:
            costo += d[anterior][x]
            anterior = x
        costo += d[anterior][inicio]
        if costo < mejor:
            mejor, mejor_perm = costo, perm
    return ResultadoTSP(mejor, [inicio, *mejor_perm, inicio])


def held_karp(d: list[list[float]], inicio: int, lugares: list[int]) -> ResultadoTSP:
    """Held-Karp con máscaras de bits. O(2^k k^2) tiempo, O(2^k k) memoria.

    dp[S][j] = costo mínimo de salir del inicio, visitar exactamente los
    lugares del subconjunto S y terminar en j (j en S).
      dp[{j}][j] = d(inicio, j)
      dp[S][j]   = min_{i en S\\{j}} dp[S\\{j}][i] + d(i, j)
      óptimo     = min_j dp[todos][j] + d(j, inicio)
    Se implementa "hacia adelante" (cada estado propaga a sus sucesores).
    """
    k = len(lugares)
    if k == 0:
        return ResultadoTSP(0.0, [inicio, inicio])
    inf = math.inf
    n_mascaras = 1 << k
    dp = [[inf] * k for _ in range(n_mascaras)]
    padre = [[-1] * k for _ in range(n_mascaras)]
    for j in range(k):
        dp[1 << j][j] = d[inicio][lugares[j]]

    for mascara in range(1, n_mascaras):
        fila = dp[mascara]
        for j in range(k):
            if not (mascara >> j) & 1:
                continue
            costo_j = fila[j]
            if costo_j == inf:
                continue
            d_j = d[lugares[j]]
            for t in range(k):
                if (mascara >> t) & 1:
                    continue
                nueva = mascara | (1 << t)
                c = costo_j + d_j[lugares[t]]
                if c < dp[nueva][t]:
                    dp[nueva][t] = c
                    padre[nueva][t] = j

    completa = n_mascaras - 1
    mejor, ultimo = inf, -1
    for j in range(k):
        c = dp[completa][j] + d[lugares[j]][inicio]
        if c < mejor:
            mejor, ultimo = c, j

    # Reconstrucción del orden de visita a partir de la tabla de padres.
    orden_inv = []
    mascara, j = completa, ultimo
    while j != -1:
        orden_inv.append(lugares[j])
        previo = padre[mascara][j]
        mascara &= ~(1 << j)
        j = previo
    orden_inv.reverse()
    return ResultadoTSP(mejor, [inicio, *orden_inv, inicio])


def vecino_mas_cercano(d: list[list[float]], inicio: int, lugares: list[int]) -> ResultadoTSP:
    """Heurística voraz: desde el lugar actual ir al no visitado más cercano
    (según d[actual][x], que es asimétrica) y al final regresar al inicio. O(k^2)."""
    pendientes = list(lugares)
    orden = [inicio]
    actual = inicio
    costo = 0.0
    while pendientes:
        siguiente = min(pendientes, key=lambda x: (d[actual][x], x))
        costo += d[actual][siguiente]
        pendientes.remove(siguiente)
        orden.append(siguiente)
        actual = siguiente
    costo += d[actual][inicio]
    orden.append(inicio)
    return ResultadoTSP(costo, orden)


def memoria_held_karp_bytes(k: int) -> int:
    """Tamaño teórico de la tabla: 2^k * k entradas de 8 bytes (costo) + 1 byte (padre)."""
    return (1 << k) * k * (8 + 1)


# ----------------------------------------------------------------------------
# Carga de datos
# ----------------------------------------------------------------------------
def cargar_matriz() -> tuple[list[str], list[list[float]], pd.DataFrame]:
    """Devuelve (ids, matriz en segundos como lista de listas, catálogo)."""
    if not MATRIZ.exists():
        raise FileNotFoundError(f"No existe {MATRIZ}. Ejecuta primero: python -m src.r2_caminos matriz")
    m = pd.read_csv(MATRIZ, index_col=0)
    ids = [str(x) for x in m.index]
    if list(m.columns.astype(str)) != ids:
        raise ValueError("La matriz no es cuadrada con los mismos ids en filas y columnas.")
    d = m.to_numpy(dtype=float).tolist()
    if any(not math.isfinite(x) for fila in d for x in fila):
        raise ValueError("La matriz tiene tiempos infinitos o vacíos.")
    catalogo = pd.read_csv(CATALOGO, dtype={"id": str})
    return ids, d, catalogo


def elegir_lugares(ids: list[str], inicio: int, k: int, semilla: int) -> list[int]:
    """k lugares al azar (todas las categorías), distintos del inicio, con semilla fija."""
    candidatos = [i for i in range(len(ids)) if i != inicio]
    return random.Random(semilla).sample(candidatos, k)


def medir_con_limite(fn, *args):
    """Protocolo de la sección 6 para algoritmos que pueden pasar de 5 min.

    1) Una ejecución en otro proceso con límite de 5 min (regla 7).
    2) Si tardó <= 1 min, se repite hasta 5 veces y se toma la mediana (regla 3).
    Devuelve (resultado, mediana_ms, repeticiones_ms) o None si no se completó.
    """
    primera = ejecutar_con_limite(fn, *args, limite_s=LIMITE_S, repeticiones=1)
    if primera is None:
        return None
    resultado, mediana_ms, tiempos = primera
    if mediana_ms / 1000.0 <= UMBRAL_UNA_VEZ_S:
        resultado, mediana_ms, tiempos = medir(fn, *args)
    return resultado, mediana_ms, tiempos


def _pico_memoria_mb(fn, *args) -> float:
    """Pico de memoria de Python (tracemalloc) en una ejecución aparte, sin cronometrar."""
    tracemalloc.start()
    fn(*args)
    _, pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return pico / 1e6


def _nombres(ids: list[str], orden: list[int]) -> str:
    return "->".join(ids[i] for i in orden)


# ----------------------------------------------------------------------------
# Experimentos
# ----------------------------------------------------------------------------
def experimento_tiempos(k_min: int = K_MIN, k_max: int = K_MAX) -> pd.DataFrame:
    """R4.1: tiempo de fuerza bruta y Held-Karp para k = k_min..k_max."""
    ids, d, _ = cargar_matriz()
    inicio = ids.index(INICIO_ID)
    activo = {"fb": True, "hk": True}
    filas = []
    for k in range(k_min, k_max + 1):
        lugares = elegir_lugares(ids, inicio, k, SEMILLA + k)
        fila: dict = {"k": k, "lugares": ";".join(ids[i] for i in lugares)}
        costos = {}
        for clave, fn in (("fb", fuerza_bruta), ("hk", held_karp)):
            if not activo[clave]:
                fila.update({f"{clave}_ms": math.nan, f"{clave}_costo_s": math.nan,
                             f"{clave}_estado": "no completada (k menor ya superó 5 min)"})
                continue
            salida = medir_con_limite(fn, d, inicio, lugares)
            if salida is None:
                activo[clave] = False
                fila.update({f"{clave}_ms": math.nan, f"{clave}_costo_s": math.nan,
                             f"{clave}_estado": "no completada (> 5 min)"})
                print(f"k={k:2d} {clave}: no completada (> 5 min)")
                continue
            res, mediana, tiempos = salida
            costos[clave] = res.costo_s
            fila.update({f"{clave}_ms": mediana, f"{clave}_costo_s": res.costo_s,
                         f"{clave}_estado": "ok", f"{clave}_repeticiones_ms":
                         ";".join(f"{t:.6f}" for t in tiempos)})
            if clave == "hk":
                fila["hk_orden"] = _nombres(ids, res.orden)
                fila["hk_tabla_entradas"] = (1 << k) * k
                fila["hk_memoria_teorica_mb"] = memoria_held_karp_bytes(k) / 1e6
                fila["hk_pico_python_mb"] = _pico_memoria_mb(held_karp, d, inicio, lugares)
            print(f"k={k:2d} {clave}: {mediana:12.3f} ms  costo={res.costo_s:.2f} s")
        if "fb" in costos and "hk" in costos:
            if not math.isclose(costos["fb"], costos["hk"], rel_tol=1e-9, abs_tol=1e-6):
                raise AssertionError(f"Fuerza bruta y Held-Karp difieren para k={k}.")
            fila["coinciden"] = True
        else:
            fila["coinciden"] = ""
        filas.append(fila)

    df = pd.DataFrame(filas)
    RESULTS.mkdir(exist_ok=True)
    df.to_csv(RESULTS / "r4_tiempos.csv", index=False, encoding="utf-8")
    resueltos = {c: [int(r["k"]) for r in filas if r.get(f"{c}_estado") == "ok"] for c in ("fb", "hk")}
    resumen = {
        "semilla": SEMILLA, "inicio": INICIO_ID, "limite_s": LIMITE_S,
        "mayor_k_fuerza_bruta": max(resueltos["fb"], default=None),
        "mayor_k_held_karp": max(resueltos["hk"], default=None),
    }
    (RESULTS / "r4_resumen.json").write_text(json.dumps(resumen, indent=2), encoding="utf-8")
    (RESULTS / "maquina_r4.json").write_text(
        json.dumps(info_maquina(), indent=2, ensure_ascii=False), encoding="utf-8")
    print("Resumen:", resumen)
    return df


def experimento_calidad(ks=(5, 8, 10, 12), instancias: int = 5) -> pd.DataFrame:
    """R4.3: brecha porcentual de la heurística frente al óptimo de Held-Karp."""
    ids, d, _ = cargar_matriz()
    inicio = ids.index(INICIO_ID)
    filas = []
    for k in ks:
        for inst in range(instancias):
            semilla = 10_000 + 100 * k + inst
            lugares = elegir_lugares(ids, inicio, k, semilla)
            opt = held_karp(d, inicio, lugares)
            voraz = vecino_mas_cercano(d, inicio, lugares)
            brecha = 100.0 * (voraz.costo_s - opt.costo_s) / opt.costo_s
            filas.append({
                "k": k, "instancia": inst + 1, "semilla": semilla,
                "optimo_s": opt.costo_s, "voraz_s": voraz.costo_s, "brecha_pct": brecha,
                "orden_optimo": _nombres(ids, opt.orden), "orden_voraz": _nombres(ids, voraz.orden),
            })
    df = pd.DataFrame(filas)
    RESULTS.mkdir(exist_ok=True)
    df.to_csv(RESULTS / "r4_calidad.csv", index=False, encoding="utf-8")
    resumen = (df.groupby("k")["brecha_pct"].agg(promedio_pct="mean", maximo_pct="max", instancias="count")
               .reset_index())
    resumen.to_csv(RESULTS / "r4_calidad_resumen.csv", index=False, encoding="utf-8")
    print(resumen.to_string(index=False))
    return df


def itinerario_dia(d: list[list[float]], inicio: int, atractivos: list[int],
                   duracion_min: dict[int, float], jornada_min: float = JORNADA_MIN) -> dict:
    """R4.4: ordena con Held-Karp y, si no cabe en la jornada, quita atractivos.

    Criterio de eliminación: en cada paso se quita el atractivo cuya salida
    libera más tiempo (su duración más el desvío que causaba). Es la decisión
    que reduce más el total y, por tanto, tiende a quitar la menor cantidad
    de atractivos; después se recalcula el recorrido con Held-Karp.
    """
    def evaluar(sel: list[int]) -> tuple[ResultadoTSP, float, float, float]:
        r = held_karp(d, inicio, sel)
        viaje = r.costo_s / 60.0
        visitas = sum(duracion_min[a] for a in sel)
        return r, viaje, visitas, viaje + visitas

    seleccion = list(atractivos)
    r, viaje, visitas, total = evaluar(seleccion)
    inicial = {"atractivos": list(seleccion), "orden": r.orden, "viaje_min": viaje,
               "visitas_min": visitas, "total_min": total}
    quitados = []
    while total > jornada_min and seleccion:
        mejor = None
        for a in seleccion:
            resto = [x for x in seleccion if x != a]
            r2, v2, vis2, t2 = evaluar(resto)
            if mejor is None or t2 < mejor[0]:
                mejor = (t2, a, r2, v2, vis2)
        t2, a, r2, v2, vis2 = mejor
        quitados.append({"atractivo": a, "liberado_min": total - t2, "total_antes_min": total,
                         "total_despues_min": t2})
        seleccion = [x for x in seleccion if x != a]
        r, viaje, visitas, total = r2, v2, vis2, t2
    voraz = vecino_mas_cercano(d, inicio, seleccion)
    return {
        "jornada_min": jornada_min, "inicial": inicial, "quitados": quitados,
        "final": {"atractivos": list(seleccion), "orden": r.orden, "viaje_min": viaje,
                  "visitas_min": visitas, "total_min": total, "cabe": total <= jornada_min},
        "voraz": {"orden": voraz.orden, "viaje_min": voraz.costo_s / 60.0,
                  "total_min": voraz.costo_s / 60.0 + visitas,
                  "diferencia_min": (voraz.costo_s - r.costo_s) / 60.0},
    }


def experimento_itinerario(inicio_id: str = INICIO_ID, atractivos_ids: list[str] | None = None) -> dict:
    ids, d, cat = cargar_matriz()
    atractivos_ids = atractivos_ids or ITINERARIO_DEFECTO
    if not 6 <= len(atractivos_ids) <= 8:
        raise ValueError("El itinerario debe tener entre 6 y 8 atractivos.")
    dur = cat.set_index("id")["duracion_visita_min"].to_dict()
    nombre = cat.set_index("id")["nombre"].to_dict()
    inicio = ids.index(inicio_id)
    atractivos = [ids.index(a) for a in atractivos_ids]
    res = itinerario_dia(d, inicio, atractivos, {ids.index(a): float(dur[a]) for a in atractivos_ids})

    res["inicio"] = inicio_id
    for bloque in (res["inicial"], res["final"], res["voraz"]):
        if "atractivos" in bloque:
            bloque["atractivos"] = [ids[i] for i in bloque["atractivos"]]
        bloque["orden"] = [ids[i] for i in bloque["orden"]]
    for q in res["quitados"]:
        q["atractivo"] = ids[q["atractivo"]]
        q["nombre"] = nombre[q["atractivo"]]
        q["duracion_min"] = float(dur[q["atractivo"]])
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "r4_itinerario.json").write_text(
        json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Inicial: {res['inicial']['total_min']:.1f} min (jornada {res['jornada_min']:.0f})")
    for q in res["quitados"]:
        print(f"  quitar {q['atractivo']} {q['nombre']}: libera {q['liberado_min']:.1f} min")
    f = res["final"]
    print(f"Final: {f['total_min']:.1f} min, cabe={f['cabe']}, orden={'->'.join(f['orden'])}")
    print(f"Voraz: {res['voraz']['total_min']:.1f} min (+{res['voraz']['diferencia_min']:.1f} min)")
    return res


def experimento_ejemplo_voraz(k: int = 5, intentos: int = 2000) -> dict:
    """R4.5: instancia real (k pequeño) donde el vecino más cercano no es óptimo."""
    ids, d, _ = cargar_matriz()
    inicio = ids.index(INICIO_ID)
    mejor = None
    for semilla in range(intentos):
        lugares = elegir_lugares(ids, inicio, k, semilla)
        opt = held_karp(d, inicio, lugares)
        voraz = vecino_mas_cercano(d, inicio, lugares)
        brecha = 100.0 * (voraz.costo_s - opt.costo_s) / opt.costo_s
        if mejor is None or brecha > mejor["brecha_pct"]:
            mejor = {"k": k, "semilla": semilla, "lugares": [ids[i] for i in lugares],
                     "optimo_s": opt.costo_s, "voraz_s": voraz.costo_s, "brecha_pct": brecha,
                     "orden_optimo": _nombres(ids, opt.orden), "orden_voraz": _nombres(ids, voraz.orden)}
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "r4_ejemplo_voraz.json").write_text(
        json.dumps(mejor, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(mejor, indent=2, ensure_ascii=False))
    return mejor


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("accion", choices=["tiempos", "calidad", "itinerario", "ejemplo", "todo"])
    a = ap.parse_args()
    acciones = {"tiempos": experimento_tiempos, "calidad": experimento_calidad,
                "itinerario": experimento_itinerario, "ejemplo": experimento_ejemplo_voraz}
    if a.accion == "todo":
        for f in acciones.values():
            f()
    else:
        acciones[a.accion]()


if __name__ == "__main__":
    main()