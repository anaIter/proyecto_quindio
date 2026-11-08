"""Verifica que el entorno esté listo. Ejecutar: python verificar_entorno.py"""
import importlib
import sys

PAQUETES = ["osmnx", "networkx", "geopandas", "pyproj", "numpy", "pandas",
            "scipy", "matplotlib", "folium", "streamlit", "psutil", "pytest"]

ok = True
print(f"Python {sys.version.split()[0]}")
if sys.version_info < (3, 11):
    print("  [!] Se recomienda Python 3.11 o superior")
    ok = False

for nombre in PAQUETES:
    try:
        m = importlib.import_module(nombre)
        print(f"  [ok] {nombre} {getattr(m, '__version__', '')}")
    except Exception as e:
        print(f"  [FALLA] {nombre}: {e}")
        ok = False

# Prueba mínima de red: descarga un barrio pequeño de Armenia
try:
    import osmnx as ox
    G = ox.graph_from_point((4.5339, -75.6811), dist=300, network_type="drive")
    print(f"  [ok] descarga OSM: {G.number_of_nodes()} nodos, {G.number_of_edges()} aristas")
except Exception as e:
    print(f"  [FALLA] descarga OSM (¿internet?): {e}")
    ok = False

print("\nEntorno LISTO" if ok else "\nRevisar los puntos marcados")
