# Implementación R2 – Caminos mínimos

## Archivos
- `src/r2_caminos.py`: implementación propia de Dijkstra lineal y Dijkstra con heap; selección de pares, experimentos y matriz de tiempos.
- `src/graficas_r2.py`: gráfica de tiempo de ejecución frente a nodos explorados.
- `tests/test_r2.py`: pruebas unitarias.

## Integración
Copia `r2_caminos.py` y `graficas_r2.py` dentro de la carpeta `src/` del proyecto. Copia `test_r2.py` dentro de `tests/`.

Se usan los archivos existentes `data/grafo_procesado.graphml` y `data/catalogo_con_nodos.csv`. El peso es `tiempo_s` (segundos).

## Ejecución
Desde la raíz del repositorio:

```bash
python -m src.r2_caminos experimentos
python -m src.graficas_r2
python -m src.r2_caminos matriz
pytest tests/test_r2.py -q
```

Los resultados se guardan en:
- `results/r2_experimentos.csv`
- `results/r2_resumen.json`
- `results/r2_matriz_tiempos.csv`
- `figures/r2_tiempo_vs_nodos.png`

La matriz es dirigida: el tiempo de A a B puede ser distinto del tiempo de B a A.
