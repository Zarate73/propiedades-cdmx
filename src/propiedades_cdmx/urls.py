"""Lectura de las URLs a scrapear desde un CSV de enlaces."""
from __future__ import annotations

import logging
import re
from pathlib import Path

import pandas as pd

logger = logging.getLogger("propiedades_cdmx.urls")

PATRON_URL = re.compile(r"https://propiedades\.com/[^\s,\"]+")


def leer_urls_desde_csv(path: Path, max_urls: int) -> list[str]:
    """Lee URLs de propiedades.com desde cualquier columna del CSV. Usa un
    fallback de regex sobre el archivo crudo si `pandas` no puede
    parsearlo (el CSV de enlaces históricamente ha tenido filas mal
    formadas por comas dentro de títulos sin escapar).
    """
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el CSV de URLs: {path}")

    try:
        df = pd.read_csv(path)
        urls: list[str] = []
        for col in df.columns:
            candidatas = df[col].dropna().astype(str)
            urls.extend(u for u in candidatas if "propiedades.com" in u and len(u) > 30)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Fallo el parseo tabular de %s (%s), usando fallback por regex", path, exc)
        contenido = path.read_text(encoding="utf-8")
        urls = PATRON_URL.findall(contenido)

    urls_unicas = list(dict.fromkeys(urls))[:max_urls]
    logger.info("URLs encontradas: %d (limitadas a %d)", len(urls_unicas), max_urls)
    return urls_unicas
