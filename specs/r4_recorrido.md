# Spec R4 – Ruta óptima de recorrido (TSP asimétrico)

## Entradas
- `results/r2_matriz_tiempos.csv`: matriz dirigida 40x40 en segundos (no simétrica).
- `data/catalogo_con_nodos.csv`: ids, nombres y `duracion_visita_min` de los atractivos.
- Partida por defecto: Armenia (C01). Semilla fija: 42 (tiempos), 10000+100k+i (calidad).

## Comportamiento esperado
- `fuerza_bruta`, `held_karp` y `vecino_mas_cercano` reciben (matriz, inicio, lugares) y
  devuelven `ResultadoTSP(costo_s, orden)`. `orden` empieza y termina en el inicio.
- Fuerza bruta y Held-Karp dan el mismo costo óptimo. Held-Karp devuelve el orden de visita.
- Límite 5 min por ejecución: si se pasa, se reporta "no completada" y no se sigue con k mayores.
- Itinerario: 6–8 atractivos, jornada 660 min = visitas + desplazamientos (ida y regreso).

## Subestructura óptima (justificación)
Sea C(S, j) el costo mínimo de salir del inicio, visitar exactamente los lugares de S y
terminar en j. Si el mejor recorrido para (S, j) llega a j desde i, el tramo hasta i debe ser
el mejor recorrido para (S\{j}, i): si hubiera uno más barato, sustituirlo bajaría el costo
total (argumento de corte y pegado). El costo de ir de i a j solo depende de i y j, y la
decisión sobre los lugares ya visitados no afecta lo que viene, salvo por i y por S.

## Recurrencia
- C({j}, j) = d(inicio, j)
- C(S, j) = min_{i en S\{j}} [ C(S\{j}, i) + d(i, j) ]
- Óptimo = min_j [ C(L, j) + d(j, inicio) ], con L = todos los lugares.

## Complejidad
| Algoritmo | Tiempo | Memoria |
|---|---|---|
| Fuerza bruta | O(k! · k) | O(k) |
| Held-Karp | O(2^k · k²) | O(2^k · k) |
| Vecino más cercano | O(k²) | O(k) |

Memoria de Held-Karp: 2^k · k entradas. Con 8 bytes de costo + 1 byte de padre,
k = 12 da 4096 · 12 · 9 ≈ 0,44 MB. (En Python, `r4_tiempos.csv` registra además el pico real.)

## Heurística elegida: vecino más cercano
Desde el lugar actual ir al no visitado con menor d[actual][x] y regresar al inicio.
Se elige porque usa directamente la matriz asimétrica, es O(k²) y es el voraz clásico para el TSP.

## Voraz frente a óptimo (R4.5)
El vecino más cercano mira solo el costo del siguiente salto y puede dejar para el final un lugar
lejano, lo que obliga a un regreso caro (ejemplo a mano en `test_voraz_no_siempre_es_optimo`:
104 contra 53; ejemplo real en `results/r4_ejemplo_voraz.json`).
En Dijkstra la elección voraz sí es óptima porque los pesos son no negativos: el nodo de menor
distancia tentativa ya no puede mejorarse por otro camino (ese camino pasaría por nodos con
distancia mayor o igual y sumaría pesos >= 0). Esa propiedad, que fija el valor de cada elección
sin importar lo que venga después, no existe en el TSP, donde la elección afecta qué
lugares quedan por visitar.

## Casos de prueba (tests/test_r4.py)
Caso a mano asimétrico; HK = fuerza bruta (k = 1..7, 5 semillas); recorrido válido y costo
consistente; HK contra todas las permutaciones; k = 0 y k = 1; el voraz nunca es mejor que el
óptimo; contraejemplo voraz; memoria; itinerario que se recorta y que ya cabe.

## Medición
`results/r4_tiempos.csv`, `r4_calidad.csv`, `r4_calidad_resumen.csv`, `r4_itinerario.json`,
`r4_ejemplo_voraz.json`, `r4_resumen.json`, `maquina_r4.json`. 5 repeticiones y mediana;
una sola vez si pasa de 1 min.