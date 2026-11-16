
# R5 — Aplicación de consulta y planificación

## 1. Objetivo

Integrar los resultados de los requerimientos R1, R2, R3 y R4 en una aplicación local que permita consultar caminos mínimos, visualizar la envolvente convexa, planificar itinerarios turísticos y revisar los resultados experimentales.

## 2. Tecnología utilizada

La aplicación se desarrolla utilizando Streamlit como herramienta para construir la interfaz y Folium para la representación de mapas interactivos.

La ejecución se realiza localmente desde el mismo repositorio del proyecto, sin necesidad de crear un frontend independiente.

## 3. Fuentes de información

La aplicación utiliza los siguientes archivos generados durante los requerimientos anteriores:

- `data/grafo_procesado.graphml`: contiene la red vial procesada.
- `data/catalogo_con_nodos.csv`: contiene los lugares turísticos, coordenadas y nodos asociados.
- `results/r2_matriz_tiempos.csv`: contiene la matriz de tiempos de desplazamiento.
- `results/r3_envolvente_red.json`: contiene los vértices de la envolvente convexa.
- Archivos CSV y JSON de `results/`: contienen los resultados experimentales de R1, R2, R3 y R4.

## 4. Funcionalidades

### 4.1. Inicio

Presenta un resumen general del catálogo de lugares y un mapa con su distribución geográfica.

### 4.2. Consulta de rutas

Permite seleccionar un lugar de origen y uno de destino para calcular el camino mínimo mediante el algoritmo Dijkstra con heap.

El resultado presenta el tiempo estimado de desplazamiento, la cantidad de nodos de la ruta, los nodos explorados y la representación geográfica del recorrido.

### 4.3. Envolvente convexa

Permite visualizar la envolvente convexa calculada durante R3, junto con los lugares registrados en el catálogo.

### 4.4. Planificador de itinerarios

Permite seleccionar una cabecera municipal como punto de partida y entre seis y ocho atractivos turísticos.

El planificador reutiliza los algoritmos desarrollados en R4 para generar un itinerario y comparar el resultado de Held-Karp con la heurística de vecino más cercano.

También presenta los tiempos de desplazamiento y visita, así como el orden de los lugares seleccionados.

### 4.5. Resultados experimentales

Presenta las tablas y gráficas disponibles de los requerimientos anteriores:

- R1: resultados relacionados con la estructura y almacenamiento de la red.
- R2: mediciones de los algoritmos de caminos mínimos.
- R3: mediciones del cálculo de la envolvente convexa.
- R4: mediciones de los algoritmos de recorridos e itinerarios.

## 5. Consideraciones de implementación

La aplicación funciona como una capa de integración y presentación. No vuelve a implementar los algoritmos desarrollados en los requerimientos anteriores.

Los tiempos utilizados para planificar los itinerarios proceden de la matriz de tiempos de R2.

En la consulta individual de rutas se representa la secuencia de nodos devuelta por Dijkstra. En el mapa del itinerario, las conexiones entre lugares son esquemáticas y no representan necesariamente el trazado exacto de las carreteras.

La aplicación utiliza los archivos locales existentes y no necesita descargar nuevamente la información geográfica al iniciarse.

## 6. Ejecución

Desde la carpeta raíz del proyecto se ejecuta:

```bash
streamlit run app/streamlit_app.py
```
