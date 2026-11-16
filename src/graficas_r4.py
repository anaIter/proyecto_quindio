"""Gráficas del requerimiento R4 a partir de sus CSV."""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

RESULTS = Path("results")
FIGURES = Path("figures")


def grafica_tiempo_vs_k() -> None:
    archivo = RESULTS / "r4_tiempos.csv"
    if not archivo.exists():
        raise FileNotFoundError(f"No existe {archivo}. Ejecuta: python -m src.r4_tsp tiempos")
    df = pd.read_csv(archivo)
    FIGURES.mkdir(exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 6))
    for col, etiqueta, marca in (("fb_ms", "Fuerza bruta", "o"), ("hk_ms", "Held-Karp", "s")):
        datos = df.dropna(subset=[col])
        ax.plot(datos["k"], datos[col], marker=marca, label=etiqueta)
    for col, etiqueta in (("fb_estado", "Fuerza bruta"), ("hk_estado", "Held-Karp")):
        fallo = df[df[col].astype(str).str.startswith("no completada")]
        if not fallo.empty:
            ax.axvline(fallo["k"].min(), linestyle=":", color="gray")
            ax.text(fallo["k"].min() - 0.05, 0.97, f"{etiqueta}: no completada (> 5 min)",
                transform=ax.get_xaxis_transform(), rotation=90, va="top", ha="right", fontsize=8)
    ax.set_yscale("log")
    ax.set_title("R4: tiempo de ejecución vs. k (salida desde Armenia)")
    ax.set_xlabel("k (lugares a visitar, sin contar el de partida)")
    ax.set_ylabel("Tiempo de ejecución (ms, escala logarítmica)")
    ax.grid(True, alpha=0.3, which="both")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES / "r4_tiempo_vs_k.png", dpi=180)
    plt.close(fig)
    print(f"Gráfica guardada en {FIGURES / 'r4_tiempo_vs_k.png'}")


def grafica_calidad() -> None:
    archivo = RESULTS / "r4_calidad_resumen.csv"
    if not archivo.exists():
        raise FileNotFoundError(f"No existe {archivo}. Ejecuta: python -m src.r4_tsp calidad")
    df = pd.read_csv(archivo)
    FIGURES.mkdir(exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    x = range(len(df))
    ax.bar([i - 0.2 for i in x], df["promedio_pct"], width=0.4, label="Promedio")
    ax.bar([i + 0.2 for i in x], df["maximo_pct"], width=0.4, label="Máximo")
    ax.set_xticks(list(x))
    ax.set_xticklabels([f"k={k}" for k in df["k"]])
    ax.set_ylabel("Brecha respecto al óptimo de Held-Karp (%)")
    ax.set_title("R4: calidad del vecino más cercano")
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES / "r4_calidad_voraz.png", dpi=180)
    plt.close(fig)
    print(f"Gráfica guardada en {FIGURES / 'r4_calidad_voraz.png'}")


def main() -> None:
    grafica_tiempo_vs_k()
    grafica_calidad()


if __name__ == "__main__":
    main()
    