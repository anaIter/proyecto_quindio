"""Herramientas para construir y verificar el catálogo.

    python -m src.catalogo_tools geocodificar   # pre-llena lat/lon vacías con Nominatim (OSM)
    python -m src.catalogo_tools mapa           # results/catalogo_mapa.html para verificar

IMPORTANTE: el geocodificador es solo una ayuda. Cada coordenada debe revisarse en el
mapa (el enunciado lo exige) y corregirse a mano si cae en otro sitio. Las filas cuyo
nombre empieza por "ELEGIR" son para que el grupo escoja el lugar y escriba su nombre.
"""
import argparse
from pathlib import Path

import pandas as pd

CATALOGO = Path("data/catalogo.csv")
COLORES = {"cabecera": "red", "atractivo": "green", "finca_hotel": "blue", "acopio": "orange"}


def geocodificar():
    import osmnx as ox
    df = pd.read_csv(CATALOGO)
    for i, f in df.iterrows():
        if pd.notna(f["lat"]) and pd.notna(f["lon"]):
            continue
        if str(f["nombre"]).startswith("ELEGIR"):
            continue
        nombre = str(f["nombre"]).replace("(plaza principal)", "").replace("(Plaza de Bolívar)", "plaza de Bolívar")
        muni = "" if pd.isna(f["municipio"]) else f["municipio"]
        consulta = f"{nombre}, {muni}, Quindío, Colombia"
        try:
            lat, lon = ox.geocode(consulta)
            df.loc[i, ["lat", "lon"]] = [round(lat, 6), round(lon, 6)]
            print(f"[ok] {f['id']} {nombre}: {lat:.5f}, {lon:.5f}")
        except Exception as e:
            print(f"[sin resultado] {f['id']} {nombre} -> llenar a mano ({type(e).__name__})")
    df.to_csv(CATALOGO, index=False, encoding="utf-8")


def mapa():
    import folium
    df = pd.read_csv(CATALOGO).dropna(subset=["lat", "lon"])
    m = folium.Map(location=[4.54, -75.68], zoom_start=10)
    for _, f in df.iterrows():
        folium.CircleMarker([f["lat"], f["lon"]], radius=6, color=COLORES.get(f["categoria"], "gray"),
                            fill=True, tooltip=f"{f['id']} {f['nombre']}").add_to(m)
    Path("results").mkdir(exist_ok=True)
    m.save("results/catalogo_mapa.html")
    print(f"{len(df)} lugares en results/catalogo_mapa.html (ábrelo en el navegador)")


def validar():
    df = pd.read_csv(CATALOGO)
    print(df["categoria"].value_counts().to_string())
    faltan = df[df["lat"].isna() | df["lon"].isna()]
    print(f"\nSin coordenadas: {len(faltan)}")
    print(faltan[["id", "nombre"]].to_string(index=False))
    at = df[(df["categoria"] == "atractivo") & df["duracion_visita_min"].isna()]
    print(f"\nAtractivos sin duración: {len(at)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("accion", choices=["geocodificar", "mapa", "validar"])
    a = ap.parse_args()
    {"geocodificar": geocodificar, "mapa": mapa, "validar": validar}[a.accion]()
