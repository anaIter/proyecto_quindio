"""Gráficas de R1 y R3 generadas desde results/*.csv (protocolo: regla 8)."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

RESULTS = Path("results")
FIGURES = Path("figures")


def grafica_r1():
    f = RESULTS / "r1_tiempo_componente.csv"
    if not f.exists():
        print("Falta", f); return
    df = pd.read_csv(f)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.loglog(df["V+E"], df["Tiempo (ms)"], "o-")
    for _, r in df.iterrows():
        ax.annotate(r["Red"], (r["V+E"], r["Tiempo (ms)"]), fontsize=7, xytext=(4, -10), textcoords="offset points")
    ax.set_xlabel("Tamaño de la red, V + E")
    ax.set_ylabel("Tiempo de largest_component (ms)")
    ax.set_title("R1: tiempo de la componente fuertemente conexa")
    ax.grid(True, which="both", alpha=0.3)
    FIGURES.mkdir(exist_ok=True)
    fig.tight_layout(); fig.savefig(FIGURES / "r1_tiempo_componente.png", dpi=150); plt.close(fig)


def grafica_r3():
    f = RESULTS / "r3_tiempos.csv"
    if not f.exists():
        print("Falta", f); return
    df = pd.read_csv(f)
    x = range(len(df))
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar([i - 0.2 for i in x], df["Tiempo propio (ms)"], 0.4, label="QuickHull propio")
    ax.bar([i + 0.2 for i in x], df["Tiempo SciPy (ms)"], 0.4, label="SciPy (Qhull)")
    ax.set_xticks(list(x)); ax.set_xticklabels(df["Conjunto de puntos"], rotation=15, fontsize=8)
    ax.set_ylabel("Tiempo (ms)"); ax.set_title("R3: envolvente convexa"); ax.legend()
    FIGURES.mkdir(exist_ok=True)
    fig.tight_layout(); fig.savefig(FIGURES / "r3_tiempos.png", dpi=150); plt.close(fig)


def main():
    grafica_r1(); grafica_r3()
    print("Figuras en", FIGURES)


if __name__ == "__main__":
    main()
