"""PRUEBAS INTEGRALES con PostgreSQL real: SQL de hechos + motor + alertas + interfaz.

ATENCIÓN: inicializar() BORRA y recrea las tablas. Por eso estas pruebas solo corren si
existe la variable TEST_DATABASE_URL (use una base de pruebas, no la de la demostración):
    set TEST_DATABASE_URL=postgresql://usuario:clave@host/base      (Windows)
    export TEST_DATABASE_URL=postgresql://usuario:clave@host/base   (Linux / Mac)
"""
import os

import pytest

from tests.util import sesiones_en_memoria

URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="defina TEST_DATABASE_URL para correr las pruebas integrales")


@pytest.fixture()
def conn():
    from db import conectar
    from inicializar import inicializar
    with conectar(URL) as c:
        inicializar(c)
        yield c


def test_inicializar_crea_todo(conn):
    n = lambda t: conn.execute(f"SELECT COUNT(*) AS n FROM {t}").fetchone()["n"]
    assert (n("usuarios"), n("reglas"), n("sesiones")) == (5, 6, 56) and n("alertas") == 0


def test_hechos_sql_coinciden_con_los_calculados_en_python(conn):
    from db import cargar_sesiones
    desde_sql = {s["id"]: s["hechos"] for s in cargar_sesiones(conn)}
    for s in sesiones_en_memoria():
        assert desde_sql[s["id"]] == s["hechos"], f"difieren los hechos de la sesión {s['id']}"


def test_validacion_completa_con_la_base(conn):
    from db import cargar_reglas, cargar_sesiones
    from validar import matriz_confusion
    m, _ = matriz_confusion(cargar_sesiones(conn, solo_etiquetadas=True), cargar_reglas(conn))
    assert (m["VP"], m["FN"], m["FP"], m["VN"]) == (21, 1, 2, 32)


def test_diagnosticar_una_sesion_no_borra_las_alertas_de_otras(conn):
    from sistema import diagnosticar_todas, diagnosticar_sesion
    _, _, total = diagnosticar_todas(conn)
    assert total > 0
    diagnosticar_sesion(conn, 1)
    assert conn.execute("SELECT COUNT(*) AS n FROM alertas").fetchone()["n"] == total


def test_alertas_con_explicacion_y_certeza(conn):
    from sistema import diagnosticar_sesion
    # sesión 31 = primer ataque de fuerza bruta (8 fallos desde host externo)
    s, d, expl = diagnosticar_sesion(conn, 31)
    assert s["real"] == "fuerza_bruta" and d["alerta"]
    assert [x["regla"]["id"] for x in d["disparos"]] == ["R1", "R2"]
    assert len(expl) == 2 and all("Porque:" in e for e in expl)
    fila = conn.execute("SELECT certeza FROM alertas WHERE sesion_id=31 AND regla_id='R2'").fetchone()
    assert float(fila["certeza"]) == 0.76


def test_sesion_sin_eventos_no_desaparece(conn):
    from db import insertar_sesion, cargar_sesiones
    conn.execute("INSERT INTO sesiones (usuario, hora_inicio, etiqueta_real) VALUES ('ana', 9, 'sin_etiqueta')")
    conn.commit()
    s = cargar_sesiones(conn, sesion_id=57)[0]
    assert s["hechos"]["lecturas"] == 0 and not s["hechos"]["login_exitoso"]


def test_registrar_sesion_nueva_y_diagnosticarla(conn):
    from db import insertar_sesion, cargar_sesiones
    from sistema import diagnosticar_sesion
    ev = [{"accion": "login", "host": "203.0.113.45", "resultado": "fallo", "objeto": None}] * 6
    sid = insertar_sesion(conn, "pedro", 3, ev)
    _, d, _ = diagnosticar_sesion(conn, sid)
    assert d["alerta"] and d["severidad"] == "alta"
    # las sesiones registradas por el analista no contaminan la validación
    assert len(cargar_sesiones(conn, solo_etiquetadas=True)) == 56


def test_flujo_completo_por_la_interfaz(conn, monkeypatch, capsys):
    """Simula al analista: menú -> registrar sesión (usuario 1, hora 2, 8 logins fallidos desde host externo)."""
    import main
    from db import cargar_reglas
    respuestas = iter(["2",            # menú: registrar sesión nueva
                       "1",            # usuario 1 (ana)
                       "2",            # hora 2
                       "4", "203.0.113.45", "8",   # 8 logins fallidos desde host externo
                       "0",            # terminar eventos
                       "5"])           # salir
    monkeypatch.setattr("builtins.input", lambda *_: next(respuestas))
    main.bucle_menu(conn, cargar_reglas(conn))
    salida = capsys.readouterr().out
    assert "registrada con 8 evento(s)" in salida
    assert "*** ALERTA ***" in salida and "[R1]" in salida and "[R2]" in salida and "76%" in salida
