from propiedades_cdmx.parsing import (
    clasificar_tipo_inmueble,
    extraer_antiguedad,
    extraer_banos,
    extraer_estacionamientos,
    extraer_m2_construidos,
    extraer_precio,
    extraer_precio_m2_colonia,
    extraer_recamaras,
    parsear_direccion_completa,
)


def test_extraer_precio():
    assert extraer_precio("Precio: $1,399,000 MXN") == 1399000
    assert extraer_precio("Sin precio visible") is None


def test_clasificar_tipo_inmueble():
    assert clasificar_tipo_inmueble("Departamento en venta Roma Norte") == "Departamento"
    assert clasificar_tipo_inmueble("Casa sola en Coyoacán") == "Casa"
    assert clasificar_tipo_inmueble("Terreno comercial") == "Terreno"
    assert clasificar_tipo_inmueble("Local en plaza comercial") == "Local Comercial"
    assert clasificar_tipo_inmueble("Bodega industrial") == "Otro"


def test_extraer_recamaras_banos_m2():
    source = "Departamento con 3 recamaras, 2 baños, 85 m² de construcción"
    assert extraer_recamaras(source) == 3
    assert extraer_banos(source) == 2
    assert extraer_m2_construidos(source) == 85


def test_extraer_estacionamientos_y_antiguedad():
    source = "2 estacionamientos, 15 años de antigüedad"
    assert extraer_estacionamientos(source) == 2
    assert extraer_antiguedad(source) == 15


def test_extraer_precio_m2_colonia():
    assert extraer_precio_m2_colonia("$35 mil por m² en la zona") == 35000
    assert extraer_precio_m2_colonia("sin dato de precio por m2") is None


def test_parsear_direccion_completa_con_calle_y_colonia():
    titulo = "Departamento en Av. Insurgentes Sur 123, Col. Del Valle, 03100"
    direccion, calle, colonia, cp = parsear_direccion_completa(titulo, source="")

    assert cp == "03100"
    assert colonia.startswith("Del Valle")
    assert "Insurgentes" in calle
    assert "03100" in direccion


def test_parsear_direccion_completa_sin_datos():
    direccion, calle, colonia, cp = parsear_direccion_completa("Sin dirección clara", source="")
    assert direccion == ""
    assert calle == ""
    assert colonia == ""
    assert cp == ""
