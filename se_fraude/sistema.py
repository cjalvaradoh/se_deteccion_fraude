"""Flujo principal del sistema experto: hechos (SQL) -> inferencia -> explicación (tabla alertas)."""
from db import cargar_reglas, cargar_sesiones, guardar_alertas, explicaciones_de
from motor import diagnosticar


def diagnosticar_sesion(conn, sesion_id, reglas=None):
    """Diagnostica UNA sesión y guarda sus alertas.
    Devuelve (sesion, diagnostico, explicaciones) o None si la sesión no existe."""
    reglas = reglas if reglas is not None else cargar_reglas(conn)
    sesiones = cargar_sesiones(conn, sesion_id=sesion_id)
    if not sesiones:
        return None
    s = sesiones[0]
    resultado = diagnosticar(s["hechos"], reglas)
    guardar_alertas(conn, [s], {s["id"]: resultado})
    return s, resultado, explicaciones_de(conn, s["id"])


def diagnosticar_todas(conn, reglas=None, solo_etiquetadas=False):
    """Diagnostica todas las sesiones y guarda las alertas. Devuelve (sesiones, resultados, n_alertas)."""
    reglas = reglas if reglas is not None else cargar_reglas(conn)
    sesiones = cargar_sesiones(conn, solo_etiquetadas=solo_etiquetadas)
    resultados = {s["id"]: diagnosticar(s["hechos"], reglas) for s in sesiones}
    n = guardar_alertas(conn, sesiones, resultados)
    return sesiones, resultados, n
