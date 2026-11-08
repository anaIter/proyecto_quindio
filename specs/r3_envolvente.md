# Spec R3 – Envolvente convexa de la red vial

## Entradas
- Nodos de `data/grafo_procesado.graphml` (lon, lat) y puntos aleatorios en un cuadrado (semilla 42, lado 100 000 m; n = 1 000, 10 000, 50 000).

## Preparación (no se mide)
Convertir a UTM 18N (EPSG:32618), redondear al entero más cercano, eliminar repetidos, int64.

## Comportamiento esperado
- `quickhull(pts)` devuelve los vértices en sentido antihorario, empezando por el punto más a la izquierda (menor x, desempate menor y).
- Los puntos alineados sobre un lado no son vértices.
- Casos degenerados: 1 punto -> 1 vértice; todos alineados -> los 2 extremos.
- Debe dar el mismo conjunto de vértices que `scipy.spatial.ConvexHull`.

## Elección del algoritmo
QuickHull: los nodos de una red vial se agrupan en ciudades y la envolvente tiene pocos vértices (h << n), caso en que QuickHull rinde cerca de O(n log n).

## Casos de prueba (tests/test_r3.py)
Cuadrado con interiores y alineados; antihorario; degenerados; triángulo a mano; empate en distancia máxima; coordenadas ~9e6 sin desbordar; 8 semillas aleatorias vs SciPy; malla con muchos alineados; círculo con 400 vértices.

## Medición
`results/r3_tiempos.csv`: Conjunto, n, Vértices, Tiempo propio (ms), Tiempo SciPy (ms), Cociente, Coinciden vértices. 5 repeticiones, mediana.
