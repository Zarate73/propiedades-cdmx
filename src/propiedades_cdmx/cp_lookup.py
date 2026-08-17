"""Enriquecimiento de un código postal de CDMX con alcaldía, población y
coordenadas, a partir de la tabla `data/cp_alcaldias_cdmx.csv`.

⚠️ ADVERTENCIA SOBRE LAS COORDENADAS
-------------------------------------
Las columnas `latitud_aprox` / `longitud_aprox` de esa tabla **no son
geocodificación real**. Vienen de una tabla que existía en el notebook
original (`c.ipynb`) etiquetada como "Fuente: INEGI 2020 y Correos de
México", pero al inspeccionar los valores se ve un patrón de decremento
fijo dentro de cada alcaldía (p.ej. cada CP sucesivo resta ~0.001-0.01
grados de lat/lon) — es decir, son coordenadas interpoladas/inventadas
para dar *algún* punto en el mapa por alcaldía, no la ubicación real de
cada colonia. El error puede ser de varios kilómetros para CPs alejados
del "ancla" de la alcaldía.

Son aceptables para un mapa exploratorio a nivel de alcaldía. **No las
uses como verdad para análisis espacial fino** (distancia a amenidades,
clustering por colonia, etc.) — para eso, geocodifica de verdad (el
propio notebook `t.ipynb` original ya tenía un borrador con
`geopy.geocoders.Nominatim`, ver `analysis/` en este repo, o usa el
catálogo oficial de códigos postales de Correos de México).

La población por alcaldía (INEGI 2020) sí es un dato real y razonable de
usar tal cual.
"""
from __future__ import annotations

import functools
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger("propiedades_cdmx.cp_lookup")


@functools.lru_cache(maxsize=1)
def _cargar_tabla(cp_lookup_path: str) -> pd.DataFrame:
    path = Path(cp_lookup_path)
    if not path.exists():
        raise FileNotFoundError(
            f"No se encontró la tabla de códigos postales en {path}. "
            "Debe existir data/cp_alcaldias_cdmx.csv en el repo."
        )
    df = pd.read_csv(path, dtype={"cp": str})
    logger.info("Tabla de códigos postales cargada: %d registros", len(df))
    return df.set_index("cp")


def obtener_alcaldia_por_cp(cp: str, cp_lookup_path: str | Path = "data/cp_alcaldias_cdmx.csv") -> str:
    tabla = _cargar_tabla(str(cp_lookup_path))
    if cp not in tabla.index:
        return ""
    return str(tabla.loc[cp, "alcaldia"])


def obtener_poblacion_por_cp(
    cp: str, cp_lookup_path: str | Path = "data/cp_alcaldias_cdmx.csv"
) -> int | None:
    tabla = _cargar_tabla(str(cp_lookup_path))
    if cp not in tabla.index:
        return None
    return int(tabla.loc[cp, "poblacion_alcaldia_2020"])


def obtener_coordenadas_por_cp(
    cp: str, cp_lookup_path: str | Path = "data/cp_alcaldias_cdmx.csv"
) -> tuple[float | None, float | None]:
    tabla = _cargar_tabla(str(cp_lookup_path))
    if cp not in tabla.index:
        return None, None
    fila = tabla.loc[cp]
    return float(fila["latitud_aprox"]), float(fila["longitud_aprox"])
