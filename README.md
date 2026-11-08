# Rutas del Paisaje Cultural Cafetero

Proyecto final – análisis de algoritmos. Lenguaje: Python 3.11+.

## Instalación
```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Reproducir R1
```bash
python -m src.r1_red descargar   # requiere internet; anota la fecha (data/descarga_meta.json)
python -m src.r1_red memoria
python -m src.r1_red procesar
# completar data/catalogo.csv (>= 40 lugares) y luego:
python -m src.r1_red ubicar
python -m src.r1_red escalado
```

## Estructura
- `specs/`: especificaciones (SDD) por requerimiento.
- `data/`: red, catálogo y grafo procesado.
- `src/`: algoritmos (`r1_red.py`, `bench.py`; luego R2, R3, R4).
- `results/`: CSV/JSON de mediciones. `figures/`: gráficas generadas desde esos CSV.
- `app/`: aplicación (R5). `docs/`: documento técnico y anexo de IA.

## Protocolo de medición
5 repeticiones y mediana; una sola vez si pasa de 1 min; límite 5 min; milisegundos; semillas fijas documentadas. Ver `src/bench.py`.

## Pendiente
Semilla fija: _por definir_. Máquina de medición: ver `results/maquina_r1.json`.
