
# README — Requerimiento R5

## Descripción

El requerimiento R5 consiste en integrar los resultados de R1, R2, R3 y R4 mediante una aplicación local que facilite la consulta de rutas, la visualización de información geográfica y la planificación de itinerarios turísticos.

La aplicación utiliza Streamlit para la interfaz y Folium para los mapas interactivos.

## Archivos desarrollados

La implementación se encuentra organizada de la siguiente manera:

| Archivo | Descripción |
|---|---|
| `app/__init__.py` | Inicialización del paquete de la aplicación. |
| `app/servicios.py` | Carga de datos e integración con los algoritmos anteriores. |
| `app/mapas.py` | Construcción de los mapas geográficos. |
| `app/streamlit_app.py` | Interfaz principal de la aplicación. |
| `specs/r5_aplicacion.md` | Especificación del requerimiento R5. |

## Instalación de dependencias

Las dependencias necesarias se encuentran declaradas en el archivo `requirements.txt`.

Si todavía no están instaladas en el entorno virtual, se pueden instalar mediante:

```powershell
python -m pip install -r requirements.txt
```

## Ejecución

Para iniciar la aplicación, abre PowerShell desde la carpeta raíz del proyecto y ejecuta:

```powershell
streamlit run app/streamlit_app.py
```

Streamlit iniciará un servidor local y mostrará una dirección para acceder a la aplicación desde el navegador.

Si el navegador no se abre automáticamente, copia la dirección local que aparece en la terminal.

## Secciones de la aplicación

### 1. Inicio

Presenta indicadores generales del catálogo y un mapa con los lugares registrados.

### 2. Consulta de rutas

Permite seleccionar un origen y un destino para calcular el camino mínimo utilizando Dijkstra con heap.

### 3. Envolvente convexa

Muestra la representación geográfica de la envolvente calculada en R3.

### 4. Planificador de itinerarios

Permite seleccionar una cabecera municipal y entre seis y ocho atractivos turísticos para generar un itinerario utilizando los algoritmos de R4.

### 5. Resultados experimentales

Permite consultar los resultados almacenados de los requerimientos R1, R2, R3 y R4.

## Archivos de datos necesarios

La aplicación utiliza los archivos originales del proyecto:

- `data/grafo_procesado.graphml`
- `data/catalogo_con_nodos.csv`
- `results/r2_matriz_tiempos.csv`
- `results/r3_envolvente_red.json`
- Los archivos experimentales CSV y JSON de R1, R2, R3 y R4.

Es importante conservar sus nombres y ubicaciones originales.

## Consideraciones

La aplicación reutiliza los algoritmos existentes y no modifica su implementación.

El mapa de consulta de rutas representa los nodos reales del recorrido calculado. Por otro lado, el mapa del itinerario utiliza conexiones esquemáticas entre los lugares seleccionados.
