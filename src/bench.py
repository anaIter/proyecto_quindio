"""Utilidad de medición según el protocolo experimental (sección 6).

Reglas que implementa:
- 5 repeticiones y mediana (regla 3).
- Si la primera ejecución pasa de 1 minuto, se mide una sola vez (regla 3).
- Tiempos en milisegundos (regla 4).
- Solo se mide la llamada al algoritmo: preparar datos ANTES de llamar a medir().
- Reporta datos de la máquina (regla 1).

Límite de 5 minutos (regla 7): ver ejecutar_con_limite(), que corre la función
en un proceso aparte y lo termina si se pasa.
"""
import multiprocessing as mp
import platform
import statistics
import sys
import time

REPETICIONES = 5
UMBRAL_UNA_VEZ_S = 60.0
LIMITE_S = 300.0


def info_maquina() -> dict:
    info = {
        "procesador": platform.processor() or platform.machine(),
        "so": platform.platform(),
        "python": sys.version.split()[0],
        "ram_gb": None,
    }
    try:
        import psutil
        info["ram_gb"] = round(psutil.virtual_memory().total / 1e9, 1)
    except ImportError:
        pass
    return info


def medir(fn, *args, repeticiones=REPETICIONES, **kwargs):
    """Devuelve (resultado, mediana_ms, lista_tiempos_ms).

    La función debe ser pura respecto a sus argumentos (no modificarlos),
    para que las repeticiones sean comparables.
    """
    t0 = time.perf_counter_ns()
    resultado = fn(*args, **kwargs)
    dt = time.perf_counter_ns() - t0
    tiempos = [dt / 1e6]
    if dt / 1e9 <= UMBRAL_UNA_VEZ_S:
        for _ in range(repeticiones - 1):
            t0 = time.perf_counter_ns()
            fn(*args, **kwargs)
            tiempos.append((time.perf_counter_ns() - t0) / 1e6)
    return resultado, statistics.median(tiempos), tiempos


def _worker(q, fn, args, kwargs):
    q.put(medir(fn, *args, **kwargs))


def ejecutar_con_limite(fn, *args, limite_s=LIMITE_S, **kwargs):
    """Corre medir(fn, ...) en otro proceso. Devuelve None si pasa el límite
    (se reporta como 'no completada'). En Windows, llamar bajo
    `if __name__ == "__main__":` y usar funciones definidas a nivel de módulo."""
    q = mp.Queue()
    p = mp.Process(target=_worker, args=(q, fn, args, kwargs))
    p.start()
    p.join(limite_s)
    if p.is_alive():
        p.terminate()
        p.join()
        return None
    return q.get()
