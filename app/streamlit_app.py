
"""Aplicación principal del requerimiento R5."""

import sys
from pathlib import Path

# Permite importar los módulos desde la raíz del proyecto.
ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from app.mapas import (
    mapa_catalogo,
    mapa_envolvente,
    mapa_itinerario,
    mapa_ruta
)

from app.servicios import (
    cargar_catalogo,
    cargar_grafo_y_dijkstra,
    consultar_ruta,
    obtener_envolvente,
    calcular_itinerario,
    cargar_resultado_csv,
    cargar_resultado_json,
    obtener_opciones_inicio,
    obtener_atractivos,
    tabla_memoria
)

from src.r4_tsp import INICIO_ID, ITINERARIO_DEFECTO


# ---------------------------------------------------------
# Configuración de Streamlit
# ---------------------------------------------------------

st.set_page_config(
    page_title="Rutas del Paisaje Cultural Cafetero",
    page_icon="🗺️",
    layout="wide"
)

st.title("Rutas del Paisaje Cultural Cafetero")

st.caption(
    "Aplicación de consulta de rutas, visualización geográfica "
    "y planificación de itinerarios turísticos."
)


# ---------------------------------------------------------
# Navegación
# ---------------------------------------------------------

with st.sidebar:

    st.header("Navegación")

    seccion = st.radio(
        "Selecciona una sección",
        [
            "Inicio",
            "Consulta de rutas",
            "Envolvente convexa",
            "Planificador de itinerarios",
            "Resultados experimentales"
        ]
    )


# ---------------------------------------------------------
# Carga de información
# ---------------------------------------------------------

@st.cache_data
def cargar_catalogo_cache():
    return cargar_catalogo()


@st.cache_resource
def cargar_red_cache():
    return cargar_grafo_y_dijkstra()


try:

    catalogo = cargar_catalogo_cache()

except Exception as error:

    st.error(
        f"No fue posible cargar el catálogo: {error}"
    )

    st.stop()


# ---------------------------------------------------------
# SECCIÓN 1: INICIO
# ---------------------------------------------------------

if seccion == "Inicio":

    st.header("Panel general")

    st.write(
        "Esta aplicación integra los resultados de los requerimientos "
        "R1, R2, R3 y R4 del proyecto."
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Lugares registrados",
        len(catalogo)
    )

    col2.metric(
        "Atractivos turísticos",
        int(
            (catalogo["categoria"] == "atractivo").sum()
        )
    )

    col3.metric(
        "Cabeceras municipales",
        int(
            (catalogo["categoria"] == "cabecera").sum()
        )
    )

    st.subheader("Mapa general de lugares")

    mapa = mapa_catalogo(catalogo)

    st_folium(
        mapa,
        use_container_width=True,
        height=560,
        key="mapa_inicio"
    )


# ---------------------------------------------------------
# SECCIÓN 2: CONSULTA DE RUTAS
# ---------------------------------------------------------

elif seccion == "Consulta de rutas":

    st.header("Consulta de caminos mínimos")

    st.write(
        "Selecciona un origen y un destino para calcular "
        "el camino mínimo mediante el algoritmo Dijkstra."
    )

    lugares = catalogo[
        ["id", "nombre", "municipio"]
    ].copy()

    lugares["etiqueta"] = lugares.apply(
        lambda fila:
            f"{fila['id']} — {fila['nombre']} "
            f"({fila['municipio']})",
        axis=1
    )

    etiquetas = dict(
        zip(lugares["etiqueta"], lugares["id"])
    )

    opciones = list(etiquetas.keys())

    columna1, columna2 = st.columns(2)

    etiqueta_inicio = next(
        (
            opcion
            for opcion in opciones
            if etiquetas[opcion] == INICIO_ID
        ),
        opciones[0]
    )

    origen = columna1.selectbox(
        "Lugar de origen",
        opciones,
        index=opciones.index(etiqueta_inicio)
    )

    destino = columna2.selectbox(
        "Lugar de destino",
        opciones,
        index=min(13, len(opciones) - 1)
    )

    origen_id = str(etiquetas[origen])
    destino_id = str(etiquetas[destino])

    # Estado inicial de los resultados.
    if "resultado_ruta" not in st.session_state:
        st.session_state.resultado_ruta = None

    if "error_ruta" not in st.session_state:
        st.session_state.error_ruta = None

    if "seleccion_ruta" not in st.session_state:
        st.session_state.seleccion_ruta = None

    if st.button("Calcular ruta", type="primary"):

        st.session_state.resultado_ruta = None
        st.session_state.error_ruta = None
        st.session_state.seleccion_ruta = (
            origen_id,
            destino_id
        )

        if origen_id == destino_id:

            st.session_state.error_ruta = (
                "Selecciona dos lugares diferentes."
            )

        else:

            with st.spinner("Calculando ruta..."):

                try:

                    grafo, algoritmo = cargar_red_cache()

                    resultado = consultar_ruta(
                        grafo,
                        algoritmo,
                        catalogo,
                        origen_id,
                        destino_id
                    )

                    st.session_state.resultado_ruta = resultado

                except Exception as error:

                    st.session_state.error_ruta = str(error)

    # Mostrar los resultados guardados.
    if st.session_state.seleccion_ruta == (
        origen_id,
        destino_id
    ):

        if st.session_state.error_ruta:

            st.error(
                f"No se pudo calcular la ruta: "
                f"{st.session_state.error_ruta}"
            )

        elif st.session_state.resultado_ruta is not None:

            resultado = st.session_state.resultado_ruta

            st.success("Ruta calculada correctamente.")

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Tiempo estimado",
                f"{resultado['tiempo_min']:.1f} min"
            )

            col2.metric(
                "Nodos de la ruta",
                len(resultado["ruta_nodos"])
            )

            col3.metric(
                "Nodos explorados",
                resultado["nodos_explorados"]
            )

            st.subheader("Representación de la ruta")

            mapa = mapa_ruta(
                resultado["coordenadas"],
                resultado["origen"]["nombre"],
                resultado["destino"]["nombre"]
            )

            st_folium(
                mapa,
                use_container_width=True,
                height=560,
                key="mapa_ruta"
            )

# ---------------------------------------------------------
# SECCIÓN 3: ENVOLVENTE CONVEXA
# ---------------------------------------------------------

elif seccion == "Envolvente convexa":

    st.header("Envolvente convexa de la red vial")

    st.write(
        "Esta sección representa geográficamente la envolvente "
        "convexa calculada durante el requerimiento R3."
    )

    try:

        vertices = obtener_envolvente()

        st.metric(
            "Vértices de la envolvente",
            len(vertices)
        )

        mapa = mapa_envolvente(
            catalogo,
            vertices
        )

        st_folium(
            mapa,
            use_container_width=True,
            height=600,
            key="mapa_envolvente"
        )

    except Exception as error:

        st.error(
            f"No fue posible mostrar la envolvente: {error}"
        )


# ---------------------------------------------------------
# SECCIÓN 4: PLANIFICADOR DE ITINERARIOS
# ---------------------------------------------------------


elif seccion == "Planificador de itinerarios":

    st.header("Planificador de itinerarios turísticos")

    st.write(
        "Selecciona una cabecera municipal y entre 6 y 8 atractivos "
        "para construir un itinerario de visita."
    )

    inicios = obtener_opciones_inicio(catalogo)
    atractivos = obtener_atractivos(catalogo)

    # Opciones de inicio.
    opciones_inicio = {
        f"{fila['id']} — {fila['nombre']}": str(fila["id"])
        for _, fila in inicios.iterrows()
    }

    inicio_seleccionado = st.selectbox(
        "Punto de partida",
        list(opciones_inicio.keys())
    )

    # Opciones de atractivos.
    opciones_atractivos = {
        (
            f"{fila['id']} — {fila['nombre']} "
            f"({float(fila['duracion_visita_min']):g} min)"
        ): str(fila["id"])
        for _, fila in atractivos.iterrows()
    }

    valores_defecto = [
        identificador
        for identificador in ITINERARIO_DEFECTO
        if identificador in opciones_atractivos.values()
    ]

    seleccionados = st.multiselect(
        "Atractivos turísticos",
        list(opciones_atractivos.keys()),
        default=[
            etiqueta
            for etiqueta, identificador in opciones_atractivos.items()
            if identificador in valores_defecto
        ]
    )

    ids_seleccionados = [
        opciones_atractivos[etiqueta]
        for etiqueta in seleccionados
    ]

    # -----------------------------------------------------
    # Estado persistente del itinerario
    # -----------------------------------------------------

    if "resultado_itinerario" not in st.session_state:
        st.session_state.resultado_itinerario = None

    if "error_itinerario" not in st.session_state:
        st.session_state.error_itinerario = None

    if "seleccion_itinerario" not in st.session_state:
        st.session_state.seleccion_itinerario = None

    seleccion_actual = (
        opciones_inicio[inicio_seleccionado],
        tuple(ids_seleccionados)
    )

    # -----------------------------------------------------
    # Calcular itinerario
    # -----------------------------------------------------

    if st.button("Generar itinerario", type="primary"):

        st.session_state.resultado_itinerario = None
        st.session_state.error_itinerario = None
        st.session_state.seleccion_itinerario = seleccion_actual

        if not 6 <= len(ids_seleccionados) <= 8:

            st.session_state.error_itinerario = (
                "Debes seleccionar entre 6 y 8 atractivos."
            )

        else:

            with st.spinner("Calculando el itinerario..."):

                try:

                    resultado = calcular_itinerario(
                        opciones_inicio[inicio_seleccionado],
                        ids_seleccionados
                    )

                    st.session_state.resultado_itinerario = resultado

                except Exception as error:

                    st.session_state.error_itinerario = str(error)

    # -----------------------------------------------------
    # Mostrar resultados guardados
    # -----------------------------------------------------

    if st.session_state.seleccion_itinerario == seleccion_actual:

        if st.session_state.error_itinerario:

            st.error(
                f"No se pudo generar el itinerario: "
                f"{st.session_state.error_itinerario}"
            )

        elif st.session_state.resultado_itinerario is not None:

            resultado = st.session_state.resultado_itinerario

            inicial = resultado["inicial"]
            final = resultado["final"]
            voraz = resultado["voraz"]

            st.success("Itinerario generado correctamente.")

            st.subheader("Resultado del itinerario")

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Tiempo total",
                f"{final['total_min']:.1f} min"
            )

            col2.metric(
                "Tiempo de desplazamiento",
                f"{final['viaje_min']:.1f} min"
            )

            col3.metric(
                "Tiempo de visitas",
                f"{final['visitas_min']:.1f} min"
            )

            st.write(
                f"**Jornada disponible:** "
                f"{resultado['jornada_min']:.0f} minutos"
            )

            st.write(
                f"**Atractivos iniciales:** "
                f"{len(inicial['atractivos'])}"
            )

            st.write(
                f"**Atractivos finales:** "
                f"{len(final['atractivos'])}"
            )

            if resultado["quitados"]:

                st.markdown("#### Atractivos retirados")

                st.dataframe(
                    pd.DataFrame(resultado["quitados"]),
                    use_container_width=True
                )

            st.subheader("Comparación de algoritmos")

            comparacion = pd.DataFrame([
                {
                    "Método": "Held-Karp",
                    "Tiempo total (min)": final["total_min"],
                    "Tiempo de viaje (min)": final["viaje_min"]
                },
                {
                    "Método": "Vecino más cercano",
                    "Tiempo total (min)": voraz["total_min"],
                    "Tiempo de viaje (min)": voraz["viaje_min"]
                }
            ])

            st.dataframe(
                comparacion,
                hide_index=True,
                use_container_width=True
            )

            st.write(
                "**Orden de visita:** "
                + " → ".join(final["orden"])
            )

            st.caption(
                "El orden se optimiza utilizando la matriz de "
                "tiempos viales de R2. Las líneas del mapa son "
                "conexiones esquemáticas entre los lugares."
            )

            st.subheader("Mapa del itinerario")

            mapa = mapa_itinerario(
                catalogo,
                final["orden"]
            )

            st_folium(
                mapa,
                use_container_width=True,
                height=560,
                key="mapa_itinerario"
            )

# ---------------------------------------------------------
# SECCIÓN 5: RESULTADOS EXPERIMENTALES
# ---------------------------------------------------------

elif seccion == "Resultados experimentales":

    st.header("Resultados experimentales")

    # -----------------------------------------------------
    # R1
    # -----------------------------------------------------

    st.subheader("R1 — Estructuras de almacenamiento")

    try:

        memoria = tabla_memoria()

        st.dataframe(
            memoria,
            hide_index=True,
            use_container_width=True
        )

    except Exception as error:

        st.info(
            f"No se pudo calcular la estimación de memoria: {error}"
        )

    r1 = cargar_resultado_csv(
        "r1_tiempo_componente.csv"
    )

    if r1 is not None:

        st.write("Mediciones de R1")

        st.dataframe(
            r1,
            use_container_width=True
        )

    # -----------------------------------------------------
    # R2
    # -----------------------------------------------------

    st.subheader("R2 — Caminos mínimos")

    r2 = cargar_resultado_csv(
        "r2_experimentos.csv"
    )

    if r2 is not None:

        st.dataframe(
            r2,
            hide_index=True,
            use_container_width=True
        )

        columnas_grafica = [
            columna
            for columna in ["heap_ms", "lineal_ms"]
            if columna in r2.columns
        ]

        if columnas_grafica:

            st.write(
                "Comparación de tiempos de ejecución"
            )

            st.line_chart(
                r2[columnas_grafica]
            )

    # -----------------------------------------------------
    # R3
    # -----------------------------------------------------

    st.subheader("R3 — Envolvente convexa")

    r3 = cargar_resultado_csv(
        "r3_tiempos.csv"
    )

    if r3 is not None:

        st.dataframe(
            r3,
            hide_index=True,
            use_container_width=True
        )

    # -----------------------------------------------------
    # R4
    # -----------------------------------------------------

    st.subheader("R4 — Recorridos e itinerarios")

    r4 = cargar_resultado_csv(
        "r4_tiempos.csv"
    )

    if r4 is not None:

        st.dataframe(
            r4,
            hide_index=True,
            use_container_width=True
        )

        columnas_grafica = [
            columna
            for columna in ["fb_ms", "hk_ms"]
            if columna in r4.columns
        ]

        if columnas_grafica and "k" in r4.columns:

            st.line_chart(
                r4.set_index("k")[columnas_grafica]
            )

    calidad = cargar_resultado_csv(
        "r4_calidad_resumen.csv"
    )

    if calidad is not None:

        st.write(
            "Calidad de la heurística voraz"
        )

        st.dataframe(
            calidad,
            hide_index=True,
            use_container_width=True
        )

    itinerario = cargar_resultado_json(
        "r4_itinerario.json"
    )

    if itinerario is not None:

        st.write(
            "Itinerario de referencia generado en R4"
        )

        st.json(itinerario)
