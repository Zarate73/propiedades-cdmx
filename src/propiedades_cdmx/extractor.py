"""Extracción de los datos de una propiedad a partir de una URL ya
cargada en el navegador. Combina `parsing.py` (texto -> campos) con las
llamadas a Selenium para obtener el HTML y con `cp_lookup.py` para el
enriquecimiento por código postal.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from . import parsing
from .config import Settings
from .cp_lookup import obtener_alcaldia_por_cp, obtener_coordenadas_por_cp, obtener_poblacion_por_cp

logger = logging.getLogger("propiedades_cdmx.extractor")


def _campos_vacios(url: str) -> dict[str, Any]:
    return {
        "url": url,
        "direccion_completa": "",
        "calle": "",
        "colonia": "",
        "cp": "",
        "alcaldia": "",
        "poblacion_alcaldia": None,
        "latitud": None,
        "longitud": None,
        "precio": None,
        "titulo": "",
        "tipo_inmueble": "",
        "recamaras": None,
        "banos": None,
        "m2_construidos": None,
        "estacionamientos": None,
        "antiguedad": None,
        "amenidades": [],
        "precio_m2_colonia": None,
        "fecha_extraccion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def extraccion_rapida(driver, url: str, settings: Settings) -> dict[str, Any]:
    """Carga `url` en `driver` y extrae los campos estructurados de la
    propiedad. Ante cualquier error de red/parseo devuelve el dict con
    los campos vacíos ya inicializados, en vez de propagar la excepción
    (una URL rota no debe tumbar el lote completo).
    """
    data = _campos_vacios(url)

    try:
        driver.get(url)

        try:
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        except Exception:  # noqa: BLE001 - timeout de espera, no fatal
            pass

        source = driver.page_source

        try:
            titulo = driver.find_element(By.TAG_NAME, "h1").text.strip()
        except Exception:  # noqa: BLE001
            titulo = driver.title

        data["titulo"] = titulo

        direccion_completa, calle, colonia, cp = parsing.parsear_direccion_completa(titulo, source)
        data.update(direccion_completa=direccion_completa, calle=calle, colonia=colonia, cp=cp)

        if cp:
            data["alcaldia"] = obtener_alcaldia_por_cp(cp, settings.cp_lookup_path)
            data["poblacion_alcaldia"] = obtener_poblacion_por_cp(cp, settings.cp_lookup_path)
            lat, lon = obtener_coordenadas_por_cp(cp, settings.cp_lookup_path)
            data["latitud"], data["longitud"] = lat, lon

        data["precio"] = parsing.extraer_precio(source)
        data["tipo_inmueble"] = parsing.clasificar_tipo_inmueble(titulo)
        data["recamaras"] = parsing.extraer_recamaras(source)
        data["banos"] = parsing.extraer_banos(source)
        data["m2_construidos"] = parsing.extraer_m2_construidos(source)
        data["estacionamientos"] = parsing.extraer_estacionamientos(source)
        data["antiguedad"] = parsing.extraer_antiguedad(source)
        data["precio_m2_colonia"] = parsing.extraer_precio_m2_colonia(source)

        return data

    except WebDriverException as exc:
        logger.warning("Error en extracción rápida (%s): %s", url, exc)
        return data
