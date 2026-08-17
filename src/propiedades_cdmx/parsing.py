"""Funciones puras de parseo de texto (título + HTML fuente de la página)
hacia los campos estructurados de una propiedad. Separadas de
`extractor.py` (que sí hace I/O contra el navegador) para poder testear
esta lógica sin Selenium.
"""
from __future__ import annotations

import re

PATRONES_DIRECCION = (
    # El grupo del tipo de vialidad es NO capturante (?:...): el original
    # (con grupo capturante) hacía que `re.findall` devolviera solo "Av."
    # o "Calle" en vez de la dirección completa ("Av. Insurgentes Sur
    # 123") — un bug real detectado al escribir los tests de este módulo.
    r"(?:Calle|Av\.|Avenida|Blvd|Boulevard|Cerrada|Privada|Andador|Eje|Calzada|Camino|Carretera|Circuito)"
    r"[\s\w\d\.\-\#\/]+",
    r"Entre[\s\w\d\.\-\#\/]+y[\s\w\d\.\-\#\/]+",
    r"#[\s\d\-]+",
)


def parsear_direccion_completa(titulo: str, source: str) -> tuple[str, str, str, str]:
    """Extrae (dirección_completa, calle, colonia, cp) del título del
    anuncio y del HTML fuente de la página.
    """
    cp = ""
    cp_match = re.search(r"\b(\d{5})\b", titulo + " " + source)
    if cp_match:
        cp = cp_match.group(1)

    direccion_parts: list[str] = []
    for patron in PATRONES_DIRECCION:
        direccion_parts.extend(re.findall(patron, titulo, re.IGNORECASE))

    colonia = ""
    colonia_match = re.search(r"Col\.?\s+([\w\s\d\-]+)", titulo, re.IGNORECASE)
    if colonia_match:
        colonia = colonia_match.group(1).strip()
    else:
        colonia_match = re.search(r"colonia[^>]*>([^<]+)", source, re.IGNORECASE)
        if colonia_match:
            colonia = colonia_match.group(1).strip()

    direccion_completa = ""
    if direccion_parts:
        direccion_completa = ", ".join(direccion_parts)
        if colonia:
            direccion_completa += f", Colonia {colonia}"
        if cp:
            direccion_completa += f", C.P. {cp}, CDMX"

    calle = direccion_parts[0].strip() if direccion_parts else ""

    return direccion_completa, calle, colonia, cp


def extraer_precio(source: str) -> int | None:
    match = re.search(r"\$[\s]*([\d,]+)[\s]*(?:MXN|MN)", source)
    return int(match.group(1).replace(",", "")) if match else None


def clasificar_tipo_inmueble(titulo: str) -> str:
    titulo_lower = titulo.lower()
    if any(x in titulo_lower for x in ("departamento", "apartamento")):
        return "Departamento"
    if "casa" in titulo_lower:
        return "Casa"
    if "terreno" in titulo_lower:
        return "Terreno"
    if "local" in titulo_lower:
        return "Local Comercial"
    return "Otro"


def _extraer_entero(patron: str, source: str) -> int | None:
    match = re.search(patron, source, re.IGNORECASE)
    return int(match.group(1)) if match else None


def extraer_recamaras(source: str) -> int | None:
    return _extraer_entero(r"(\d+)\s*rec[áa]m", source)


def extraer_banos(source: str) -> int | None:
    return _extraer_entero(r"(\d+)\s*baños?", source)


def extraer_m2_construidos(source: str) -> int | None:
    match = re.search(r"(\d+)\s*m²", source)
    return int(match.group(1)) if match else None


def extraer_estacionamientos(source: str) -> int | None:
    return _extraer_entero(r"(\d+)\s*estacionamientos?", source)


def extraer_antiguedad(source: str) -> int | None:
    match = re.search(r"(\d+)\s*años", source)
    return int(match.group(1)) if match else None


def extraer_precio_m2_colonia(source: str) -> int | None:
    match = re.search(r"\$?\s*([\d,]+)\s*(?:mil|k)\s*por\s*m²", source, re.IGNORECASE)
    if not match:
        return None
    return int(float(match.group(1).replace(",", "")) * 1000)
