# propiedades-cdmx

[![CI](https://github.com/TU_USUARIO/propiedades-cdmx/actions/workflows/ci.yml/badge.svg)](https://github.com/TU_USUARIO/propiedades-cdmx/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)

Scraper concurrente de propiedades en venta en CDMX (propiedades.com) con enriquecimiento por código postal, más un análisis completo de precios: EDA, regresión lineal, simulación Monte Carlo, Random Forest, clustering de colonias y una red neuronal — comparando los tres modelos con métricas reales fuera de muestra, no solo el mejor caso.

> Reemplaza `TU_USUARIO` en el badge de CI de arriba por tu usuario de GitHub una vez que subas el repo.

## Resultados clave

**Distribución de precios.** El precio y el precio/m² están fuertemente sesgados a la derecha; se trabajó en escala logarítmica para el resto del análisis.

![Distribución del precio](docs/img/distribucion_precio.png)

**Precio por m² por alcaldía.** Miguel Hidalgo, Coyoacán y Cuajimalpa encabezan el precio/m² promedio, consistente con el mercado real de CDMX.

![Precio promedio por alcaldía](docs/img/precio_promedio_alcaldia.png)

> Milpa Alta aparece arriba de Miguel Hidalgo en la muestra cruda (~$359k/m²) — es un artefacto de tamaño de muestra (solo 8 propiedades capturadas ahí), no una señal de mercado real. Lo dejo visible a propósito: es el tipo de cosa que hay que saber leer antes de confiar en un promedio agrupado.

**Correlación entre variables (Pearson).** `m2_construidos` (0.72) y `baños` (0.55) son las variables físicas más correlacionadas con el precio.

![Matriz de correlación](docs/img/correlacion_pearson.png)

**Importancia de variables (Random Forest).** Tamaño construido, baños y estacionamientos dominan por encima de las variables categóricas de ubicación.

![Importancia de variables](docs/img/importancia_variables_rf.png)

### Comparación de modelos (predicción de log-precio/m²)

| Modelo                    | R² train | R² test | MAE test (log) |
| :------------------------ | :------: | :-----: | :-------------: |
| Regresión lineal (OLS)    |   0.686¹  |    —    |        —        |
| **Random Forest**         | **0.913** | **0.421** |     **0.366**     |
| Red Neuronal (MLP, sklearn) |   0.569  |  0.143  |       0.455      |

¹ R² ajustado 0.521 — el modelo OLS se evaluó in-sample (no sobre un conjunto de prueba separado), a diferencia de RF y MLP.

Random Forest generaliza mejor que la red neuronal en este dataset (1537 filas, ~275 variables tras encoding) — con esta cantidad de datos y alta cardinalidad categórica, un modelo de árboles regulariza mejor que una MLP, que muestra sobreajuste severo (gap train-test de 0.43). El propio notebook documenta el diagnóstico completo: multicolinealidad extrema en el OLS (VIF y número de condición ~10²²), no-normalidad de residuos (Jarque-Bera), y las mejoras recomendadas (Lasso/Ridge, XGBoost/LightGBM, modelos espaciales).

### Clustering de colonias (K-Means, k=5)

Segmentación del mercado en 5 perfiles según precio/m² y variabilidad:

- **Cluster 0 — Bajo precio, alta variabilidad**: zonas periféricas, mezcla de oferta formal/informal (ej. Iztapalapa).
- **Cluster 1 — Precio medio estable**: perfil residencial homogéneo (ej. Narvarte, Del Valle).
- **Cluster 2 — Premium consolidado**: precio alto, baja dispersión (ej. Polanco, Condesa, Roma Norte).
- **Cluster 3 — Emergente/transición**: precio medio-alto, alta variabilidad — gentrificación (ej. Escandón, Nuevo Polanco).
- **Cluster 4 — Económico homogéneo**: precio muy bajo, unidades muy similares (vivienda social).

## Limitaciones (documentadas, no escondidas)

- **Coordenadas aproximadas**: `data/cp_alcaldias_cdmx.csv` no es geocodificación real — ver advertencia detallada en `cp_lookup.py`. Sirve para mapas exploratorios a nivel de alcaldía, no para análisis espacial fino.
- **479 de 1537 propiedades (31%) tienen alcaldía "Desconocida"** — el parseo de dirección por regex no siempre logra extraer el código postal del título del anuncio. El gráfico de precio por alcaldía excluye estas filas.
- **Modelos evaluados con un solo split train/test**, sin validación cruzada k-fold — con 1537 filas y ~275 variables tras encoding, los números de R² test tienen varianza no trivial entre splits.
- Todo lo anterior está documentado explícitamente aquí y en el propio notebook en vez de presentarse como resultados definitivos — es intencional: un análisis honesto sobre sus límites vale más que uno que aparenta más precisión de la que tiene.

## Qué hace

- **Scraper** (`src/propiedades_cdmx/`): dado un CSV de URLs de propiedades.com, extrae precio, dirección, tipo de inmueble, recámaras/baños/m², y enriquece con alcaldía/población/coordenadas por código postal. Corre en paralelo con varios workers de Selenium, con reintentos automáticos y checkpoint incremental a un único archivo (no genera decenas de archivos por corrida).
- **Análisis** (`analysis/analisis_precios_cdmx.ipynb`): limpieza de datos, EDA, estadística descriptiva, correlación Pearson/Spearman, regresión lineal, simulación Monte Carlo de incertidumbre del precio, Random Forest, reducción dimensional + clustering de colonias, y una red neuronal — sobre el dataset de 1537 propiedades incluido en `analysis/data/`.

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Solo el scraper:
pip install -e .

# Scraper + notebook de análisis:
pip install -e ".[analysis]"

# Desarrollo (tests, lint):
pip install -e ".[dev]"

cp .env.example .env
```

Chrome debe estar instalado; Selenium 4.20+ resuelve el driver automáticamente (no necesitas `webdriver-manager`).

## Uso del scraper

```bash
# coloca tu CSV de enlaces en input/enlaces_propiedades.csv (o ajusta URLS_CSV_PATH en .env)
propiedades-cdmx scrape
propiedades-cdmx scrape --workers 5 --batch-size 30
```

También: `python -m propiedades_cdmx scrape ...`.

El progreso se anexa en vivo a `output/checkpoint.jsonl` (uno por línea, no se pierde nada si el proceso se interrumpe a la mitad). Al terminar (o cada `CHECKPOINT_EVERY_N_BATCHES` lotes) se consolida en `output/resultados_cdmx.csv`.

> Al releer `resultados_cdmx.csv` con pandas, carga la columna `cp` como texto (`pd.read_csv(..., dtype={"cp": str})`) — si no, pandas infiere tipo numérico y pierde el cero inicial de códigos postales como `03100`.

## Uso del notebook de análisis

```bash
jupyter notebook analysis/analisis_precios_cdmx.ipynb
```

El dataset ya está en `analysis/data/propiedades_cdmx.csv`, no hace falta correr el scraper primero para explorar el análisis. Las imágenes de `docs/img/` están extraídas de las salidas ya ejecutadas del notebook.

## Arquitectura

```
src/propiedades_cdmx/
├── config.py       # Configuración vía .env
├── logging_config.py
├── cp_lookup.py     # Alcaldía/población/coordenadas por CP (advertencia sobre precisión)
├── driver.py         # create_driver: Chrome headless, sin imágenes, anti-detección
├── parsing.py         # Funciones puras: precio, tipo de inmueble, recámaras, dirección...
├── extractor.py        # Combina Selenium + parsing.py + cp_lookup.py por URL
├── scraper.py            # ScraperConcurrente: ThreadPoolExecutor + checkpoint JSONL
├── urls.py                # Lectura del CSV de enlaces (con fallback por regex)
└── cli.py                  # Entrypoint de línea de comandos
```

`parsing.py` y `cp_lookup.py` son funciones puras, testeadas sin necesitar Chrome real. `extractor.py` y `scraper.py` sí hacen I/O (Selenium, disco) y no están cubiertos por tests automatizados — limitación consciente, igual que en el resto de mis proyectos de scraping.

## Tests

```bash
pytest --cov=propiedades_cdmx
```

11 tests cubriendo `parsing.py` y `cp_lookup.py`. Uno de ellos (`test_parsear_direccion_completa_con_calle_y_colonia`) detectó un bug real del código original: `re.findall` con un grupo capturante en el patrón de vialidad devolvía solo "Av." en vez de la dirección completa — corregido en `parsing.py` haciendo el grupo no-capturante.

## Licencia

MIT para el código (`src/`, `tests/`, `analysis/*.ipynb`) — ver [LICENSE](LICENSE). El dataset de `analysis/data/propiedades_cdmx.csv` se incluye con fines educativos/de portafolio; no otorga licencia de redistribución sobre el contenido original de propiedades.com que contiene.

## De dónde viene esto

La carpeta original `Trabajo_Manu/` tenía, además del código:

- ~30 archivos sueltos en la raíz documentando el proceso de depuración a mano (`3_propiedades_100%_PERFECTAS.csv`, `3_propiedades_100PERFECTAS_FINAL.csv`, `propiedad_CORRECTA.csv`, `propiedad_CORREGIDA.csv`, `propiedad_FINAL_100.csv`...). Ninguno sobrevivió a este repo.
- `resultados_masivos/`: ~80 archivos `propiedades_batch_N_<timestamp>_V4.json` (8 KB a 738 KB cada uno) más un `TODAS_CORREGIDAS_V4.json` de 28.2 MB y su `.csv` de 14.6 MB — checkpoints incrementales de una versión anterior del scraper que nunca limpió sus resultados intermedios. El diseño de `scraper.py` en este repo (checkpoint único en JSONL, consolidado al final) existe específicamente para que esto no vuelva a pasar.
- `trabajo.zip` (29.6 MB) y `TODAS_CORREGIDAS_V3.json` (27 MB) en la raíz: respaldos/duplicados de lo anterior.
- `c.ipynb`: todo el scraper (incluida la tabla de 1059 códigos postales) vivía en 2 celdas de Jupyter, una de 78,000 caracteres. Se convirtió en los 8 módulos de `src/propiedades_cdmx/`.
- `t.ipynb`: 141 celdas. Las primeras 11 eran versiones anteriores y descartadas del scraper (una con el comentario literal "ÚLTIMA VERSIÓN — NUNCA MÁS SE TOCA", seguida de más versiones después) mezcladas con el notebook de análisis. Se quedaron fuera; `analysis/analisis_precios_cdmx.ipynb` es el resto (celdas 12-141 del original), que es el análisis real y está bien documentado con markdown.
- `mapa_inmobiliario_cdmx.html` (9.3 MB) y `umap_clusters.png`: salidas regenerables, no se versionan — se regeneran corriendo el notebook.
- `trabajo/`: copia casi completa de los archivos de arriba en una subcarpeta, incluyendo una carpeta llamada literalmente `nada/`. Descartada por completo.

Cambios de código sobre el original (no solo reorganización):

- `obtener_alcaldia_por_cp`/`obtener_poblacion_por_cp`/`obtener_coordenadas_por_cp` ahora leen de un CSV versionado (`data/cp_alcaldias_cdmx.csv`) en vez de un diccionario de 1059 entradas hardcodeado en el código fuente.
- Checkpoint incremental en JSONL en vez de reescritura periódica de CSV completo — es lo que evita la explosión de archivos de `resultados_masivos/`.
- Reintentos con backoff (`tenacity`) en cada URL antes de marcarla como fallida definitivamente.
- `parsing.py` extrae funciones puras testeables (`extraer_precio`, `clasificar_tipo_inmueble`, etc.) que en el original vivían inline dentro de `extraccion_rapida`, y corrige el bug de `re.findall` mencionado en la sección de Tests.
