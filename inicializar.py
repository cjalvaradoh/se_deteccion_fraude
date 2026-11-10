"""Crea las tablas y las llena: usuarios, reglas (base de conocimientos) y sesiones de prueba.
Ejecutar una vez:  python inicializar.py   (se puede repetir: borra y recrea todo)
"""
import json

from db import conectar, crear_tablas
from reglas import REGLAS
from datos import USUARIOS, ARCHIVOS_SENSIBLES, casos_de_prueba


def inicializar(conn):
    crear_tablas(conn)
    for u, p in USUARIOS.items():
        conn.execute("INSERT INTO usuarios (usuario, host_habitual, es_admin) VALUES (%s,%s,%s)",
                     (u, p["host"], p["admin"]))
    for ruta in sorted(ARCHIVOS_SENSIBLES):
        conn.execute("INSERT INTO archivos_sensibles (ruta) VALUES (%s)", (ruta,))

    for r in REGLAS:
        conn.execute("""INSERT INTO reglas (id, descripcion, condicion, conclusion, severidad, certeza)
                        VALUES (%s,%s,%s::jsonb,%s,%s,%s)""",
                     (r["id"], r["descripcion"], json.dumps(r["si"]),
                      r["entonces"], r["severidad"], r["certeza"]))

    casos = casos_de_prueba()
    for c in casos:
        sid = conn.execute(
            """INSERT INTO sesiones (usuario, hora_inicio, etiqueta_real, nota)
               VALUES (%s,%s,%s,%s) RETURNING id""",
            (c["usuario"], c["hora_inicio"], c["real"], c["nota"])).fetchone()["id"]
        with conn.cursor() as cur:
            cur.executemany(
                """INSERT INTO eventos (sesion_id, accion, objeto, host_origen, resultado)
                   VALUES (%s,%s,%s,%s,%s)""",
                [(sid, e["accion"], e["objeto"], e["host"], e["resultado"]) for e in c["eventos"]])
    conn.commit()
    n_ev = conn.execute("SELECT COUNT(*) AS n FROM eventos").fetchone()["n"]
    return len(USUARIOS), len(REGLAS), len(casos), n_ev


if __name__ == "__main__":
    with conectar() as conn:
        u, r, s, e = inicializar(conn)
    print(f"Listo: {u} usuarios, {r} reglas, {s} sesiones, {e} eventos.")
