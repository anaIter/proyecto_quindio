# Spec R1 – Modelo de la red vial

## Entradas
- Red de OSMnx: `graph_from_place("Quindío, Colombia", network_type="drive")` (fecha de descarga en `data/descarga_meta.json`).
- `data/catalogo.csv`: id, nombre, municipio, categoria, lat, lon (+ duración para atractivos).

## Comportamiento esperado
1. `descargar` guarda `data/red_completa.graphml` con, en cada arista, `distancia_m` y `tiempo_s`.
2. `tiempo_s = distancia_m / (velocidad_kmh / 3.6)`. Velocidad = `maxspeed` de OSM si existe; si no, promedio por tipo de vía; si no, 30 km/h.
3. `estimar_memoria(V, E)` devuelve MB de matriz y de listas, con supuestos explícitos.
4. `ubicar_lugares` asigna a cada lugar el nodo de la componente más cercano en UTM 18N (EPSG:32618) y marca `lejano` si la distancia > 500 m.
5. `procesar` guarda `data/grafo_procesado.graphml` (solo la componente fuertemente conexa) y `results/r1_tamano_red.csv`.

## Casos de prueba (pytest)
| # | Caso | Resultado esperado |
|---|------|--------------------|
| 1 | `estimar_memoria(1000, 3000)` con supuestos por defecto | matriz = 8.0 MB; listas = 0.08 MB |
| 2 | Grafo de 4 nodos con una arista de un solo sentido que deja un nodo fuera del ciclo | `largest_component(strongly=True)` conserva solo los nodos del ciclo |
| 3 | Lugar con coordenadas exactas de un nodo | `dist_nodo_m == 0` y `lejano == False` |
| 4 | Lugar a ~1 km de cualquier nodo | `lejano == True` |
| 5 | Toda arista del grafo procesado | `tiempo_s > 0` y `distancia_m > 0` |
| 6 | Grafo procesado | Todo nodo alcanza a todos los demás (`nx.is_strongly_connected`) |

## Medición
- Punto 3: `largest_component` con radios 2, 5, 10, 20 km y departamento completo (5 repeticiones, mediana, ms). La descarga NO se mide.
- Salida: `results/r1_tiempo_componente.csv` con columnas `Red, V, E, V+E, Tiempo (ms)`.
