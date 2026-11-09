"""Generación de gráficas del requerimiento R2 a partir de sus CSV."""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

RESULTS = Path("results")
FIGURES = Path("figures")


def grafica_tiempo_vs_explorados() -> None:
    archivo = RESULTS / "r2_experimentos.csv"
    if not archivo.exists():
        raise FileNotFoundError(f"No existe {archivo}. Ejecuta primero R2 experimentos.")
    df = pd.read_csv(archivo)
    FIGURES.mkdir(exist_ok=True)

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.scatter(df["heap_nodos_explorados"], df["heap_ms"],
               label="Dijkstra con heap", marker="o", alpha=0.8)
    lineal = df.dropna(subset=["lineal_ms", "lineal_nodos_explorados"])
    ax.scatter(lineal["lineal_nodos_explorados"], lineal["lineal_ms"],
               label="Dijkstra lineal", marker="x", alpha=0.8)
    ax.set_title("R2: tiempo de ejecución vs. nodos explorados")
    ax.set_xlabel("Nodos explorados")
    ax.set_ylabel("Tiempo de ejecución (ms)")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    destino = FIGURES / "r2_tiempo_vs_nodos.png"
    fig.savefig(destino, dpi=180)
    plt.close(fig)
    print(f"Gráfica guardada en {destino}")


def main() -> None:
    grafica_tiempo_vs_explorados()


if __name__ == "__main__":
    main()
