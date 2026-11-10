"""Utilidades de prueba: calcula en Python los mismos hechos que calcula la consulta SQL."""
from datos import USUARIOS, ARCHIVOS_SENSIBLES, casos_de_prueba


def hechos_desde_caso(c):
    u, ev = USUARIOS[c["usuario"]], c["eventos"]
    return dict(
        es_admin=u["admin"],
        fuera_horario=c["hora_inicio"] < 6 or c["hora_inicio"] >= 20,
        fallos_login=sum(e["accion"] == "login" and e["resultado"] == "fallo" for e in ev),
        login_exitoso=any(e["accion"] == "login" and e["resultado"] == "exito" for e in ev),
        host_nuevo=any(e["host"] != u["host"] for e in ev),
        lee_sensible=any(e["accion"] == "leer_archivo" and e["objeto"] in ARCHIVOS_SENSIBLES for e in ev),
        usa_sudo=any(e["accion"] == "usar_sudo" for e in ev),
        lecturas=sum(e["accion"] == "leer_archivo" for e in ev))


def sesiones_en_memoria():
    return [{"id": c["id"], "usuario": c["usuario"], "hora_inicio": c["hora_inicio"], "real": c["real"],
             "nota": c["nota"], "hechos": hechos_desde_caso(c)} for c in casos_de_prueba()]


BASE = dict(fallos_login=0, login_exitoso=True, host_nuevo=False, fuera_horario=False,
            es_admin=False, lee_sensible=False, usa_sudo=False, lecturas=5)


def hechos(**cambios):
    return {**BASE, **cambios}
