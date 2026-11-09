"""Gráficas de R1 y R3 generadas desde results/*.csv (protocolo: regla 8)."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

RESULTS = Path("results")
FIGURES = Path("figures")

# desplazamiento (puntos) y alineación de la etiqueta de cada red, para que no se pisen
_ETIQ_R1 = [((8, -14), "left"), ((8, -14), "left"), ((8, -14), "left"),
            ((10, 5), "left"), ((10, -11), "left")]


def grafica_r1():
    f = RESULTS / "r1_tiempo_componente.csv"
    if not f.exists():
        print("Falta", f); return
    df = pd.read_csv(f)
    x, y = df["V+E"], df["Tiempo (ms)"]
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    if {"Min (ms)", "Max (ms)"} <= set(df.columns):  # barras: mínimo y máximo de las 5 repeticiones
        ax.errorbar(x, y, yerr=[y - df["Min (ms)"], df["Max (ms)"] - y], fmt="o-", capsize=3,
                    label="Mediana de 5 repeticiones (barras: mín. y máx.)")
    else:
        ax.plot(x, y, "o-", label="Mediana de 5 repeticiones")
    ax.plot(x, y.iloc[0] * x / x.iloc[0], "--", color="gray", label="Referencia lineal (pendiente 1)")
    for i, r in df.iterrows():
        (dx, dy), ha = _ETIQ_R1[i % len(_ETIQ_R1)]
        ax.annotate(r["Red"], (r["V+E"], r["Tiempo (ms)"]), fontsize=7,
                    xytext=(dx, dy), textcoords="offset points", ha=ha)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(right=x.max() * 2.2)  # espacio a la derecha para las etiquetas
    ax.set_xlabel("Tamaño de la red, V + E")
    ax.set_ylabel("Tiempo de largest_component (ms)")
    ax.set_title("R1: tiempo de la componente fuertemente conexa")
    ax.grid(True, which="both", alpha=0.3); ax.legend(fontsize=7, loc="upper left")
    FIGURES.mkdir(exist_ok=True)
    fig.tight_layout(); fig.savefig(FIGURES / "r1_tiempo_componente.png", dpi=150); plt.close(fig)


def grafica_r3():
    f = RESULTS / "r3_tiempos.csv"
    if not f.exists():
        print("Falta", f); return
    df = pd.read_csv(f)
    x = list(range(len(df)))
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    b1 = ax.bar([i - 0.2 for i in x], df["Tiempo propio (ms)"], 0.4, label="QuickHull propio")
    b2 = ax.bar([i + 0.2 for i in x], df["Tiempo SciPy (ms)"], 0.4, label="SciPy (Qhull)")
    ax.bar_label(b1, fmt="%.2f", fontsize=7, padding=2)
    ax.bar_label(b2, fmt="%.2f", fontsize=7, padding=2)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{c}\n(n = {n:,})".replace(",", " ") for c, n in zip(df["Conjunto de puntos"], df["n"])],
                       fontsize=7)
    ax.set_ylabel("Tiempo (ms)"); ax.set_title("R3: envolvente convexa"); ax.legend()
    FIGURES.mkdir(exist_ok=True)
    fig.tight_layout(); fig.savefig(FIGURES / "r3_tiempos.png", dpi=150); plt.close(fig)


def main():
    grafica_r1(); grafica_r3()
    print("Figuras en", FIGURES)


if __name__ == "__main__":
    main()