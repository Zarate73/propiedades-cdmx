"""Configuración centralizada, resuelta desde variables de entorno."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "si", "sí"}


def _env_path(name: str, default: str) -> Path:
    return Path(os.getenv(name, default))


@dataclass(frozen=True)
class Settings:
    urls_csv_path: Path = field(
        default_factory=lambda: _env_path("URLS_CSV_PATH", "input/enlaces_propiedades.csv")
    )
    cp_lookup_path: Path = field(
        default_factory=lambda: _env_path("CP_LOOKUP_PATH", "data/cp_alcaldias_cdmx.csv")
    )
    output_dir: Path = field(default_factory=lambda: _env_path("OUTPUT_DIR", "output"))
    checkpoint_path: Path = field(
        default_factory=lambda: _env_path("CHECKPOINT_PATH", "output/checkpoint.jsonl")
    )
    log_dir: Path = field(default_factory=lambda: _env_path("LOG_DIR", "output/logs"))

    headless: bool = field(default_factory=lambda: _env_bool("HEADLESS", True))
    max_workers: int = field(default_factory=lambda: int(os.getenv("MAX_WORKERS", "3")))
    batch_size: int = field(default_factory=lambda: int(os.getenv("BATCH_SIZE", "50")))
    max_urls: int = field(default_factory=lambda: int(os.getenv("MAX_URLS", "20000")))
    page_load_timeout: int = field(default_factory=lambda: int(os.getenv("PAGE_LOAD_TIMEOUT", "15")))
    checkpoint_every_n_batches: int = field(
        default_factory=lambda: int(os.getenv("CHECKPOINT_EVERY_N_BATCHES", "5"))
    )

    def ensure_output_dirs(self) -> None:
        for path in (self.output_dir, self.log_dir):
            path.mkdir(parents=True, exist_ok=True)


def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_output_dirs()
    return settings
