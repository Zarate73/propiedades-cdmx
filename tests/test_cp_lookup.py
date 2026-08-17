from pathlib import Path

import pytest

from propiedades_cdmx.cp_lookup import (
    obtener_alcaldia_por_cp,
    obtener_coordenadas_por_cp,
    obtener_poblacion_por_cp,
)

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "cp_alcaldias_cdmx.csv"


@pytest.mark.skipif(not DATA_PATH.exists(), reason="data/cp_alcaldias_cdmx.csv no está presente")
def test_obtener_alcaldia_por_cp_conocido():
    assert obtener_alcaldia_por_cp("06700", DATA_PATH) == "Cuauhtémoc"


@pytest.mark.skipif(not DATA_PATH.exists(), reason="data/cp_alcaldias_cdmx.csv no está presente")
def test_obtener_poblacion_por_cp_conocido():
    poblacion = obtener_poblacion_por_cp("06700", DATA_PATH)
    assert poblacion is not None
    assert poblacion > 0


@pytest.mark.skipif(not DATA_PATH.exists(), reason="data/cp_alcaldias_cdmx.csv no está presente")
def test_obtener_coordenadas_por_cp_conocido():
    lat, lon = obtener_coordenadas_por_cp("06700", DATA_PATH)
    assert lat is not None and lon is not None
    # CDMX: rango aproximado de lat/lon de la ciudad completa
    assert 19.0 < lat < 19.6
    assert -99.4 < lon < -98.9


def test_cp_desconocido_devuelve_vacio(tmp_path):
    csv_vacio = tmp_path / "cp_vacio.csv"
    encabezado = "cp,alcaldia,poblacion_alcaldia_2020,latitud_aprox,longitud_aprox\n"
    csv_vacio.write_text(encabezado, encoding="utf-8")

    assert obtener_alcaldia_por_cp("99999", csv_vacio) == ""
    assert obtener_poblacion_por_cp("99999", csv_vacio) is None
    assert obtener_coordenadas_por_cp("99999", csv_vacio) == (None, None)
