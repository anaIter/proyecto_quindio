
"""Funciones para construir mapas de la aplicación R5."""

import folium
import pandas as pd


# Centro aproximado del departamento del Quindío.
CENTRO_QUINDIO = [4.54, -75.68]


# Colores según la categoría de cada lugar.
COLORES = {
    "cabecera": "red",
    "atractivo": "green",
    "finca_hotel": "blue",
    "acopio": "orange"
}


def mapa_catalogo(catalogo: pd.DataFrame):
    """Construye un mapa general con todos los lugares del catálogo."""

    mapa = folium.Map(
        location=CENTRO_QUINDIO,
        zoom_start=10,
        control_scale=True
    )

    lugares = catalogo.dropna(subset=["lat", "lon"])

    for _, fila in lugares.iterrows():

        categoria = str(fila["categoria"])

        popup = (
            f"<b>{fila['nombre']}</b><br>"
            f"ID: {fila['id']}<br>"
            f"Municipio: {fila.get('municipio', 'No especificado')}<br>"
            f"Categoría: {categoria}"
        )

        folium.CircleMarker(
            location=[
                float(fila["lat"]),
                float(fila["lon"])
            ],
            radius=6,
            color=COLORES.get(categoria, "gray"),
            fill=True,
            fill_opacity=0.8,
            tooltip=str(fila["nombre"]),
            popup=folium.Popup(popup, max_width=280)
        ).add_to(mapa)

    return mapa


def mapa_ruta(
    coordenadas,
    origen,
    destino
):
    """Dibuja la ruta vial calculada mediante Dijkstra."""

    if not coordenadas:
        raise ValueError(
            "No existen coordenadas para representar la ruta."
        )

    mapa = folium.Map(
        location=list(coordenadas[0]),
        zoom_start=11,
        control_scale=True
    )

    # Dibujar el recorrido.
    folium.PolyLine(
        coordenadas,
        color="#1769aa",
        weight=5,
        opacity=0.85,
        tooltip="Ruta calculada con Dijkstra"
    ).add_to(mapa)

    # Marcador del origen.
    folium.Marker(
        location=list(coordenadas[0]),
        tooltip=f"Origen: {origen}",
        icon=folium.Icon(
            color="green",
            icon="play"
        )
    ).add_to(mapa)

    # Marcador del destino.
    folium.Marker(
        location=list(coordenadas[-1]),
        tooltip=f"Destino: {destino}",
        icon=folium.Icon(
            color="red",
            icon="flag"
        )
    ).add_to(mapa)

    mapa.fit_bounds(coordenadas)

    return mapa


def mapa_envolvente(
    catalogo: pd.DataFrame,
    vertices_latlon
):
    """Representa la envolvente convexa calculada en R3."""

    mapa = mapa_catalogo(catalogo)

    folium.Polygon(
        locations=vertices_latlon,
        color="#7b2cbf",
        weight=3,
        fill=True,
        fill_color="#9d4edd",
        fill_opacity=0.12,
        tooltip="Envolvente convexa de la red vial"
    ).add_to(mapa)

    mapa.fit_bounds(vertices_latlon)

    return mapa



def mapa_itinerario(
    catalogo: pd.DataFrame,
    orden_ids
):
    """Representa los lugares en el orden del itinerario."""

    # Conservamos la columna id después de convertirla en índice.
    indice = catalogo.set_index("id", drop=False)

    filas = []

    for lugar_id in orden_ids:

        lugar_id = str(lugar_id)

        if lugar_id not in indice.index:
            raise ValueError(
                f"No se encontró el lugar con ID {lugar_id}."
            )

        fila = indice.loc[lugar_id]

        if isinstance(fila, pd.DataFrame):
            fila = fila.iloc[0]

        if pd.notna(fila["lat"]) and pd.notna(fila["lon"]):
            filas.append(fila)

    if not filas:
        raise ValueError(
            "Los lugares seleccionados no tienen coordenadas."
        )

    coordenadas = [
        (float(fila["lat"]), float(fila["lon"]))
        for fila in filas
    ]

    mapa = folium.Map(
        location=list(coordenadas[0]),
        zoom_start=9,
        control_scale=True
    )

    # Conexiones esquemáticas entre los lugares.
    folium.PolyLine(
        coordenadas,
        color="#1769aa",
        weight=4,
        opacity=0.8,
        tooltip="Orden del itinerario"
    ).add_to(mapa)

    # Marcadores numerados.
    for posicion, (fila, coordenada) in enumerate(
        zip(filas, coordenadas),
        start=1
    ):

        folium.Marker(
            location=list(coordenada),
            tooltip=f"{posicion}. {fila['nombre']}",
            popup=f"{posicion}. {fila['nombre']} ({fila['id']})",
            icon=folium.Icon(
                color="green" if posicion == 1 else "blue",
                icon="map-marker"
            )
        ).add_to(mapa)

    mapa.fit_bounds(coordenadas)

    return mapa
