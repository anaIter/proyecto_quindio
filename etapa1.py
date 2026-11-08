"""Lanzador de la Etapa 1 (R1 + R3). Parameters = nombre del paso.

Orden: descargar, geocodificar, mapa, validar, memoria, procesar,
       ubicar, escalado, hull, graficas
"""
import sys

from src import catalogo_tools, graficas_etapa1, r1_red, r3_hull

PASOS = {
    "descargar": r1_red.descargar,
    "geocodificar": catalogo_tools.geocodificar,
    "mapa": catalogo_tools.mapa,
    "validar": catalogo_tools.validar,
    "memoria": r1_red.cmd_memoria,
    "procesar": r1_red.cmd_procesar,
    "ubicar": r1_red.cmd_ubicar,
    "escalado": r1_red.cmd_escalado,
    "hull": r3_hull.cmd_experimento,
    "graficas": graficas_etapa1.main,
}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in PASOS:
        print(__doc__)
        sys.exit(1)
    PASOS[sys.argv[1]]()
