"""PRUEBAS de la validación de datos de la interfaz de ingreso (sin base de datos)."""
from interfaz import validar_datos_sesion

USUARIOS = {"ana", "luis"}
OK = [{"accion": "login", "host": "10.0.0.11", "resultado": "exito"}]


def test_datos_validos():
    assert validar_datos_sesion("ana", 10, OK, USUARIOS) == []


def test_usuario_inexistente():
    assert any("no existe" in e for e in validar_datos_sesion("zzz", 10, OK, USUARIOS))


def test_hora_fuera_de_rango():
    assert validar_datos_sesion("ana", 24, OK, USUARIOS)
    assert validar_datos_sesion("ana", -1, OK, USUARIOS)


def test_sesion_sin_eventos():
    assert any("al menos un evento" in e for e in validar_datos_sesion("ana", 10, [], USUARIOS))


def test_accion_y_resultado_invalidos():
    malos = [{"accion": "borrar", "host": "h", "resultado": "tal vez"}]
    assert len(validar_datos_sesion("ana", 10, malos, USUARIOS)) == 2
