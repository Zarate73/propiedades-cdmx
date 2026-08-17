"""Scraper concurrente: reparte URLs entre varios workers de Selenium y
guarda los resultados.

Cambio de diseño respecto al notebook original: en vez de volcar un CSV
completo nuevo cada N lotes (lo que en una versión posterior del proyecto
degeneró en ~80 archivos `propiedades_batch_N_<timestamp>.json` — ver
README, sección "De dónde viene esto"), cada resultado se **anexa
inmediatamente** a un único archivo de checkpoint en formato JSONL
(`output/checkpoint.jsonl`). Esto es más robusto ante un crash a la mitad
de un lote (no se pierde nada ya escrito) y no genera archivos nuevos por
cada checkpoint. `guardar_resultados()` al final consolida ese JSONL en un
único CSV.
"""
from __future__ import annotations

import json
import logging
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

import pandas as pd
from selenium.common.exceptions import WebDriverException
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .config import Settings
from .driver import create_driver
from .extractor import extraccion_rapida

logger = logging.getLogger("propiedades_cdmx.scraper")

COLUMNAS_ORDEN = [
    "url", "titulo", "tipo_inmueble", "precio",
    "direccion_completa", "calle", "colonia", "cp", "alcaldia",
    "poblacion_alcaldia", "latitud", "longitud",
    "recamaras", "banos", "m2_construidos", "estacionamientos",
    "antiguedad", "amenidades", "precio_m2_colonia", "fecha_extraccion",
]


class ScraperConcurrente:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.fallidos: list[str] = []
        self._lock = Lock()
        settings.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

    @retry(
        reraise=True,
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(WebDriverException),
    )
    def _scrape_con_reintento(self, url: str) -> dict:
        driver = create_driver(self.settings)
        try:
            return extraccion_rapida(driver, url, self.settings)
        finally:
            driver.quit()

    def scrape_url(self, url: str) -> bool:
        """Scrapea una URL individual y anexa el resultado al checkpoint."""
        try:
            datos = self._scrape_con_reintento(url)
        except WebDriverException as exc:
            with self._lock:
                self.fallidos.append(url)
            logger.warning("Fallo definitivo en %s: %s", url, exc)
            return False

        with self._lock:
            with open(self.settings.checkpoint_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(datos, ensure_ascii=False, default=str) + "\n")

        precio_str = f"${datos['precio']:,}" if datos["precio"] else "N/A"
        logger.info(
            "✓ %s | %s | CP: %s | %s",
            datos["tipo_inmueble"] or "?", precio_str,
            datos["cp"] or "sin CP", datos["alcaldia"] or "sin alcaldía",
        )
        return True

    def scrape_lote(self, urls: list[str], lote_num: int) -> None:
        logger.info("📦 Procesando lote %d (%d URLs)", lote_num, len(urls))

        with ThreadPoolExecutor(max_workers=self.settings.max_workers) as executor:
            futures = [executor.submit(self.scrape_url, url) for url in urls]
            for future in as_completed(futures):
                try:
                    future.result(timeout=30)
                except TimeoutError:
                    logger.warning("Tiempo de espera agotado para una URL del lote %d", lote_num)

        if lote_num % 3 == 0:
            pausa = random.uniform(10, 20)
            logger.info("⏸️  Pausa de %.1fs entre lotes", pausa)
            time.sleep(pausa)

    def _leer_checkpoint(self) -> list[dict]:
        if not self.settings.checkpoint_path.exists():
            return []
        resultados = []
        with open(self.settings.checkpoint_path, encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if linea:
                    resultados.append(json.loads(linea))
        return resultados

    def guardar_resultados(self) -> Path | None:
        """Consolida el checkpoint JSONL en un único CSV final."""
        resultados = self._leer_checkpoint()
        if not resultados:
            logger.warning("No hay resultados en el checkpoint para guardar")
            return None

        df = pd.DataFrame(resultados).reindex(columns=COLUMNAS_ORDEN)
        self.settings.output_dir.mkdir(parents=True, exist_ok=True)
        archivo = self.settings.output_dir / "resultados_cdmx.csv"
        df.to_csv(archivo, index=False, encoding="utf-8-sig")

        logger.info("💾 Resultados guardados en: %s", archivo)
        logger.info("📊 Total propiedades: %d | ❌ Fallidos: %d", len(resultados), len(self.fallidos))

        if self.fallidos:
            fallidos_path = self.settings.output_dir / "urls_fallidas.txt"
            fallidos_path.write_text("\n".join(self.fallidos), encoding="utf-8")

        return archivo
