"""
propiedades_cdmx
=================

Scraper concurrente de propiedades en venta en CDMX (propiedades.com) con
enriquecimiento por código postal (alcaldía, población, coordenadas
aproximadas).

Refactor del notebook original `c.ipynb`, que tenía todo el código (~1500
líneas, incluyendo una tabla de 1059 códigos postales) en dos celdas. Ver
README.md para el detalle de qué se conservó, qué se corrigió y una
advertencia importante sobre la precisión de las coordenadas.
"""

__version__ = "1.0.0"
