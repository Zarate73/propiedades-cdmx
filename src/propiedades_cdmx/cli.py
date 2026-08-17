"""Punto de entrada de línea de comandos.

Uso:
    python -m propiedades_cdmx scrape --urls input/enlaces_propiedades.csv
    python -m propiedades_cdmx scrape --urls input/enlaces_propiedades.csv --workers 5 --batch-size 30
"""
from __future__ import annotations

import argparse
import sys

from .config import get_settings
from .logging_config import setup_logging
from .scraper import ScraperConcurrente
from .urls import leer_urls_desde_csv


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="propiedades_cdmx", description="Scraper de propiedades CDMX")
    sub = parser.add_subparsers(dest="comando", required=True)

    p_scrape = sub.add_parser("scrape", help="Scrapea las URLs de un CSV de enlaces")
    p_scrape.add_argument("--urls", type=str, help="Ruta al CSV de enlaces (default: URLS_CSV_PATH en .env)")
    p_scrape.add_argument("--workers", type=int, help="Workers concurrentes (default: MAX_WORKERS en .env)")
    p_scrape.add_argument("--batch-size", type=int, help="Tamaño de lote (default: BATCH_SIZE en .env)")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    settings = get_settings()
    logger = setup_logging(settings.log_dir)

    if args.comando == "scrape":
        from dataclasses import replace

        overrides = {}
        if args.urls:
            overrides["urls_csv_path"] = type(settings.urls_csv_path)(args.urls)
        if args.workers:
            overrides["max_workers"] = args.workers
        if args.batch_size:
            overrides["batch_size"] = args.batch_size
        if overrides:
            settings = replace(settings, **overrides)

        try:
            urls = leer_urls_desde_csv(settings.urls_csv_path, settings.max_urls)
        except FileNotFoundError as exc:
            logger.error(str(exc))
            return 1

        if not urls:
            logger.error("No hay URLs para procesar")
            return 1

        scraper = ScraperConcurrente(settings)
        lotes = [urls[i : i + settings.batch_size] for i in range(0, len(urls), settings.batch_size)]

        for i, lote in enumerate(lotes, start=1):
            logger.info("Progreso: lote %d/%d (%.1f%%)", i, len(lotes), 100 * i / len(lotes))
            scraper.scrape_lote(lote, i)
            if i % settings.checkpoint_every_n_batches == 0:
                scraper.guardar_resultados()

        archivo_final = scraper.guardar_resultados()
        if archivo_final:
            print(f"✅ Scraping completo: {archivo_final}")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
