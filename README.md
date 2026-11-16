# Rutas del Paisaje Cultural Cafetero

Proyecto final de **Análisis de Algoritmos**. Modela la red vial del departamento del Quindío (Colombia) con datos de OpenStreetMap y resuelve sobre ella problemas clásicos de algoritmos: caminos mínimos, envolvente convexa y ruta óptima de recorrido turístico (TSP asimétrico). Todo se integra en una aplicación local de consulta y planificación.

**Lenguaje:** Python 3.11+

---

## Contenido

- [Requerimientos](#requerimientos)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Instalación](#instalación)
- [Reproducir los experimentos](#reproducir-los-experimentos)
- [Aplicación (R5)](#aplicación-r5)
- [Pruebas](#pruebas)
- [Datos](#datos)
- [Resultados principales](#resultados-principales)
- [Protocolo de medición](#protocolo-de-medición)
- [Documentación adicional](#documentación-adicional)

---

## Requerimientos

| Req. | Tema | Algoritmo / técnica | Módulo |
|------|------|---------------------|--------|
| **R1** | Modelo de la red vial | Descarga con OSMnx, pesos `distancia_m` y `tiempo_s`, componente fuertemente conexa, ubicación de lugares en el nodo más cercano (UTM 18N) | `src/r1_red.py` |
| **R2** | Caminos mínimos | Dijkstra lineal vs. Dijkstra con heap (implementación propia) y matriz dirigida de tiempos 40×40 | `src/r2_caminos.py` |
| **R3** | Envolvente convexa | QuickHull (divide y vencerás), validado contra `scipy.spatial.ConvexHull` | `src/r3_hull.py` |
| **R4** | Ruta óptima de recorrido | Fuerza bruta, Held-Karp (programación dinámica) y heurística del vecino más cercano | `src/r4_tsp.py` |
| **R5** | Aplicación | Interfaz en Streamlit con mapas Folium | `app/` |

Cada requerimiento tiene su especificación en `specs/` (enfoque SDD).

---

## Estructura del repositorio

```text
proyecto_quindio/
├── app/                      # R5: aplicación Streamlit
│   ├── streamlit_app.py      #   interfaz principal
│   ├── servicios.py          #   carga de datos e integración con R1–R4
│   └── mapas.py              #   construcción de mapas Folium
├── src/                      # Algoritmos y experimentos
│   ├── r1_red.py             #   R1
│   ├── r2_caminos.py         #   R2
│   ├── r3_hull.py            #   R3
│   ├── r4_tsp.py             #   R4
│   ├── bench.py              #   utilidad de medición (protocolo experimental)
│   ├── catalogo_tools.py     #   geocodificar, validar y mapear el catálogo
│   └── graficas_*.py         #   gráficas generadas desde results/*.csv
├── specs/                    # Especificaciones por requerimiento (R1–R5)
├── tests/                    # Pruebas unitarias (pytest) de R1–R4
├── data/                     # Red vial, catálogo y grafo procesado
├── results/                  # CSV/JSON de mediciones y mapa del catálogo
├── figures/                  # Gráficas generadas a partir de results/
├── docs/                     # Documentación técnica por requerimiento
├── etapa1.py                 # Lanzador de la Etapa 1 (R1 + R3)
├── verificar_entorno.py      # Verifica dependencias y acceso a OSM
├── requirements.txt
└── pytest.ini
```

---

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python verificar_entorno.py      # comprueba paquetes, versión de Python y descarga de OSM
```

Dependencias principales: `osmnx`, `networkx`, `geopandas`, `pyproj`, `numpy`, `pandas`, `scipy`, `matplotlib`, `folium`, `streamlit`, `streamlit-folium`, `psutil`, `pytest`.

> **Nota:** Todos los comandos se ejecutan desde la **raíz del proyecto**.

---

## Reproducir los experimentos

Los datos y resultados ya incluidos permiten ejecutar la aplicación directamente. Para regenerar todo desde cero, siga este orden.

### R1 – Red vial

```bash
python -m src.r1_red descargar     # requiere internet; guarda la fecha en data/descarga_meta.json
python -m src.r1_red memoria       # estimación de memoria: matriz vs. listas de adyacencia
python -m src.r1_red procesar      # componente fuertemente conexa -> data/grafo_procesado.graphml
python -m src.r1_red ubicar        # nodo más cercano de cada lugar -> data/catalogo_con_nodos.csv
python -m src.r1_red escalado      # tiempo de largest_component según tamaño de la red
```

Herramientas para el catálogo (`data/catalogo.csv`):

```bash
python -m src.catalogo_tools geocodificar   # completa lat/lon vacías con Nominatim
python -m src.catalogo_tools validar        # valida el catálogo
python -m src.catalogo_tools mapa           # genera results/catalogo_mapa.html
```

### R2 – Caminos mínimos

```bash
python -m src.r2_caminos experimentos   # Dijkstra lineal vs. heap
python -m src.r2_caminos matriz         # matriz dirigida de tiempos (results/r2_matriz_tiempos.csv)
python -m src.graficas_r2
```

### R3 – Envolvente convexa

```bash
python -m src.r3_hull experimento       # QuickHull vs. SciPy
```

### R4 – Recorrido óptimo (TSP)

```bash
python -m src.r4_tsp tiempos      # fuerza bruta vs. Held-Karp, k = 5..12
python -m src.r4_tsp calidad      # heurística voraz vs. óptimo (k = 5, 8, 10, 12)
python -m src.r4_tsp itinerario   # itinerario de un día (jornada de 11 h)
python -m src.r4_tsp ejemplo      # caso donde el voraz no es óptimo
python -m src.r4_tsp todo         # todo lo anterior
```

### Etapa 1 (atajo)

`etapa1.py` ejecuta los pasos de R1 y R3 con un solo comando:

```bash
python etapa1.py <paso>
# pasos: descargar, geocodificar, mapa, validar, memoria, procesar,
#        ubicar, escalado, hull, graficas
```

---

## Aplicación (R5)

```bash
streamlit run app/streamlit_app.py
```

Streamlit levanta un servidor local; si el navegador no se abre solo, copie la dirección que aparece en la terminal. La aplicación **no descarga datos al iniciar**: usa los archivos locales de `data/` y `results/`, por lo que deben conservar sus nombres y ubicaciones.

| Sección | Qué ofrece |
|---------|------------|
| **Inicio** | Indicadores del catálogo y mapa con los lugares registrados |
| **Consulta de rutas** | Camino mínimo entre dos lugares con Dijkstra (heap): tiempo estimado, nodos de la ruta, nodos explorados y trazado en el mapa |
| **Envolvente convexa** | Envolvente de la red calculada en R3 junto con los lugares del catálogo |
| **Planificador de itinerarios** | Cabecera de partida + 6 a 8 atractivos; itinerario con Held-Karp comparado con vecino más cercano, tiempos de viaje y de visita |
| **Resultados experimentales** | Tablas y gráficas de R1, R2, R3 y R4 |

Detalles: el mapa de **consulta de rutas** dibuja los nodos reales del recorrido; el mapa del **itinerario** usa conexiones esquemáticas entre lugares (no el trazado exacto de las vías). La app reutiliza los algoritmos existentes sin modificarlos.

---

## Pruebas

```bash
pytest -q
```

Hay pruebas para R1, R2, R3 y R4 en `tests/` (p. ej., QuickHull contra SciPy con varias semillas, Held-Karp contra fuerza bruta, conectividad fuerte del grafo procesado).

---

## Datos

| Archivo | Descripción |
|---------|-------------|
| `data/red_completa.graphml` | Red vial `drive` del Quindío descargada de OSM (8 807 nodos, 20 153 aristas; descargada el 2026-11-07 con OSMnx 2.1.1) |
| `data/grafo_procesado.graphml` | Componente fuertemente conexa (8 791 nodos, 20 132 aristas) |
| `data/catalogo.csv` | 40 lugares: 12 cabeceras municipales, 15 atractivos, 8 fincas/hoteles y 5 centros de acopio |
| `data/catalogo_con_nodos.csv` | Catálogo con el nodo de la red asignado a cada lugar |
| `data/descarga_meta.json` | Fecha de descarga, versión de OSMnx y tamaño de la red |

Peso de las aristas: `tiempo_s = distancia_m / (velocidad_kmh / 3.6)`, con `maxspeed` de OSM si existe, promedio por tipo de vía en su defecto y 30 km/h como último recurso. Un lugar se marca `lejano` si su nodo más cercano está a más de 500 m.

---

## Resultados principales

- **R1:** el preprocesamiento conserva la componente fuertemente conexa: de 8 807 a 8 791 nodos y de 20 153 a 20 132 aristas.
- **R2:** Dijkstra con heap es mucho más rápido que la versión lineal (cociente mediano ≈ 46×, con rango ≈ 6× a ≈ 227× en las pares medidas). La matriz de tiempos es **dirigida**: el tiempo de A a B puede diferir del de B a A.
- **R3:** la envolvente de la red tiene 14 vértices. QuickHull coincide en vértices con SciPy en todos los conjuntos probados (red real y cuadrados de 1 000, 10 000 y 50 000 puntos).
- **R4:** con el límite de 5 min por ejecución, la fuerza bruta llega hasta k = 11 y Held-Karp hasta k = 12. La heurística del vecino más cercano se desvía del óptimo en promedio entre ≈ 4 % (k = 5) y ≈ 17 % (k = 12).

Los datos completos están en `results/` y las gráficas en `figures/`.

---

## Protocolo de medición

- 5 repeticiones y se reporta la **mediana**; si la primera ejecución supera 1 min, se mide una sola vez.
- Límite de 5 minutos por ejecución (si se excede, se reporta "no completada").
- Tiempos en **milisegundos**; solo se mide la llamada al algoritmo (los datos se preparan antes).
- Semilla fija: **42** (R3 y R4; en la calidad de R4 se usa `10000 + 100·k + i`).
- Datos de la máquina de medición en `results/maquina_r1.json`, `maquina_r3.json` y `maquina_r4.json`, y en `results/r2_resumen.json` para R2.

La implementación está en `src/bench.py`.

---

## Documentación adicional

- `specs/` – especificación de cada requerimiento (entradas, comportamiento, casos de prueba, complejidad).
- `docs/README_R2.md` – implementación y ejecución de R2.
- `docs/README_R5.md` – detalle de la aplicación.
- `docs/plantilla_documento_etapa1.md` – plantilla del documento de la Etapa 1.

## Referencias

- Barber, Dobkin & Huhdanpaa (1996). *The Quickhull algorithm for convex hulls.*
- Held & Karp (1962). *A Dynamic Programming Approach to Sequencing Problems.*
- Rosenkrantz, Stearns & Lewis (1977). *An analysis of several heuristics for the traveling salesman problem.*
- Cormen et al. *Introduction to Algorithms* (geometría computacional y NP-completitud).
- Datos de red vial: © colaboradores de OpenStreetMap.