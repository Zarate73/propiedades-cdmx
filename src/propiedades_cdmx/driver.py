"""Creación del WebDriver de Chrome usado por el scraper: headless, sin
imágenes (para velocidad), con user-agent rotativo y mitigaciones básicas
de detección de automatización.
"""
from __future__ import annotations

import logging
import random

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from .config import Settings

logger = logging.getLogger("propiedades_cdmx.driver")

_CHROME_WIN = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
_CHROME_MAC = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)"

USER_AGENTS = [
    f"{_CHROME_WIN} Chrome/120.0.0.0 Safari/537.36",
    f"{_CHROME_MAC} Chrome/120.0.0.0 Safari/537.36",
    f"{_CHROME_WIN} Edge/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]


def create_driver(settings: Settings) -> webdriver.Chrome:
    """Crea un driver optimizado para velocidad: sin imágenes, headless
    opcional, user-agent aleatorio.
    """
    options = Options()
    options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option("useAutomationExtension", False)

    if settings.headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--blink-settings=imagesEnabled=false")

    options.add_experimental_option("prefs", {"profile.default_content_setting_values.images": 2})

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(settings.page_load_timeout)
    driver.set_script_timeout(settings.page_load_timeout)
    return driver
