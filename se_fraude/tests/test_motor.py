"""PRUEBAS UNITARIAS del motor de inferencia y de la base de conocimiento (sin base de datos)."""
import pytest

from motor import diagnosticar, inferir
from reglas import REGLAS
from tests.util import hechos


def ids(d):
    return [x["regla"]["id"] for x in d["disparos"]]


def test_sesion_normal_no_genera_alerta():
    d = diagnosticar(hechos(), REGLAS)
    assert not d["alerta"] and d["severidad"] == "ninguna" and d["certeza"] == 0


@pytest.mark.parametrize("fallos,esperado", [(4, False), (5, True), (8, True)])
def test_umbral_r1_fuerza_bruta(fallos, esperado):
    assert ("R1" in ids(diagnosticar(hechos(fallos_login=fallos), REGLAS))) is esperado


def test_encadenamiento_r1_r2_y_certeza():
    d = diagnosticar(hechos(fallos_login=8, login_exitoso=False, host_nuevo=True), REGLAS)
    assert ids(d) == ["R1", "R2"]                      # R2 se apoya en la conclusión de R1
    cert = {x["regla"]["id"]: x["certeza"] for x in d["disparos"]}
    assert cert["R1"] == 0.80
    assert cert["R2"] == pytest.approx(0.95 * 0.80, abs=0.005)    # 0.76
    assert d["severidad"] == "alta" and d["certeza"] == 0.80


def test_r2_no_se_dispara_sin_host_nuevo():
    assert ids(diagnosticar(hechos(fallos_login=8, host_nuevo=False), REGLAS)) == ["R1"]


def test_el_orden_de_las_reglas_no_altera_la_inferencia():
    h = hechos(fallos_login=8, host_nuevo=True)
    assert sorted(ids({"disparos": inferir(h, list(reversed(REGLAS)))})) == ["R1", "R2"]


def test_r3_suplantacion():
    d = diagnosticar(hechos(host_nuevo=True, fuera_horario=True), REGLAS)
    assert ids(d) == ["R3"] and d["severidad"] == "alta"


def test_r4_y_r5_solo_para_no_administradores():
    assert ids(diagnosticar(hechos(lee_sensible=True), REGLAS)) == ["R4"]
    assert ids(diagnosticar(hechos(usa_sudo=True), REGLAS)) == ["R5"]
    assert not diagnosticar(hechos(lee_sensible=True, usa_sudo=True, es_admin=True), REGLAS)["alerta"]


@pytest.mark.parametrize("lecturas,esperado", [(19, False), (20, True), (40, True)])
def test_umbral_r6_exfiltracion(lecturas, esperado):
    assert ("R6" in ids(diagnosticar(hechos(lecturas=lecturas), REGLAS))) is esperado


def test_severidad_global_es_la_mayor():
    d = diagnosticar(hechos(lee_sensible=True, lecturas=30), REGLAS)       # R4 media + R6 alta
    assert set(ids(d)) == {"R4", "R6"} and d["severidad"] == "alta"


def test_toda_alerta_trae_explicacion():
    d = diagnosticar(hechos(fallos_login=8, host_nuevo=True), REGLAS)
    for x in d["disparos"]:
        assert x["explicacion"].startswith(f"[{x['regla']['id']}]") and "Porque:" in x["explicacion"]
