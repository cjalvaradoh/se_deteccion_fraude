"""Acceso a PostgreSQL: todas las consultas del sistema están aquí."""
import os

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()  # lee DATABASE_URL del archivo .env

ACCIONES = ("login", "leer_archivo", "usar_sudo")
RESULTADOS = ("exito", "fallo")
SIN_ETIQUETA = "sin_etiqueta"   # sesiones registradas por el analista (no sirven para validar)


def conectar(url=None):
    return psycopg.connect(url or os.environ["DATABASE_URL"], row_factory=dict_row)


def crear_tablas(conn):
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")
    for sentencia in open(ruta, encoding="utf-8").read().split(";"):
        if sentencia.strip():
            conn.execute(sentencia)


# ------------------------------------------------------------ BASE DE CONOCIMIENTOS
def cargar_reglas(conn):
    """Lee la base de conocimientos."""
    filas = conn.execute("""SELECT id, descripcion, condicion, conclusion, severidad, certeza
                            FROM reglas WHERE activa ORDER BY id""").fetchall()
    return [{"id": f["id"], "descripcion": f["descripcion"],
             "si": [tuple(c) for c in f["condicion"]],
             "entonces": f["conclusion"], "severidad": f["severidad"],
             "certeza": float(f["certeza"])} for f in filas]


# ------------------------------------------------------------ BASE DE HECHOS
# Los HECHOS de cada sesión se calculan directamente con SQL (GROUP BY + FILTER).
# LEFT JOIN: una sesión sin eventos también aparece (con todos los conteos en cero).
SQL_HECHOS = """
SELECT s.id, s.usuario, s.hora_inicio, s.etiqueta_real, s.nota,
       u.es_admin,
       (s.hora_inicio < 6 OR s.hora_inicio >= 20)                                   AS fuera_horario,
       COUNT(e.id) FILTER (WHERE e.accion = 'login' AND e.resultado = 'fallo')     AS fallos_login,
       COUNT(e.id) FILTER (WHERE e.accion = 'login' AND e.resultado = 'exito') > 0 AS login_exitoso,
       COUNT(e.id) FILTER (WHERE e.host_origen <> u.host_habitual) > 0             AS host_nuevo,
       COUNT(e.id) FILTER (WHERE e.accion = 'leer_archivo'
                          AND e.objeto IN (SELECT ruta FROM archivos_sensibles)) > 0 AS lee_sensible,
       COUNT(e.id) FILTER (WHERE e.accion = 'usar_sudo') > 0                       AS usa_sudo,
       COUNT(e.id) FILTER (WHERE e.accion = 'leer_archivo')                        AS lecturas
FROM sesiones s
JOIN usuarios u ON u.usuario = s.usuario
LEFT JOIN eventos e ON e.sesion_id = s.id
{filtro}
GROUP BY s.id, s.usuario, s.hora_inicio, s.etiqueta_real, s.nota, u.es_admin, u.host_habitual
ORDER BY s.id
"""
BOOLEANOS = ("es_admin", "fuera_horario", "login_exitoso", "host_nuevo", "lee_sensible", "usa_sudo")


def cargar_sesiones(conn, sesion_id=None, solo_etiquetadas=False):
    """Devuelve las sesiones con sus hechos ya calculados.
    sesion_id        : solo esa sesión.
    solo_etiquetadas : excluye las sesiones registradas por el analista (para validar)."""
    condiciones, params = [], []
    if sesion_id is not None:
        condiciones.append("s.id = %s"); params.append(sesion_id)
    if solo_etiquetadas:
        condiciones.append("s.etiqueta_real <> %s"); params.append(SIN_ETIQUETA)
    filtro = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""
    sesiones = []
    for f in conn.execute(SQL_HECHOS.format(filtro=filtro), params).fetchall():
        hechos = {k: bool(f[k]) for k in BOOLEANOS}
        hechos.update(fallos_login=int(f["fallos_login"]), lecturas=int(f["lecturas"]))
        sesiones.append({"id": f["id"], "usuario": f["usuario"], "hora_inicio": f["hora_inicio"],
                         "real": f["etiqueta_real"], "nota": f["nota"], "hechos": hechos})
    return sesiones


def listar_usuarios(conn):
    return conn.execute("SELECT usuario, host_habitual, es_admin FROM usuarios ORDER BY usuario").fetchall()


def listar_archivos_sensibles(conn):
    return [f["ruta"] for f in conn.execute("SELECT ruta FROM archivos_sensibles ORDER BY ruta").fetchall()]


def listar_sesiones(conn, limite=15):
    """Las últimas sesiones registradas (para elegir una en el menú)."""
    return conn.execute("""SELECT s.id, s.usuario, s.hora_inicio, s.etiqueta_real, COUNT(e.id) AS n_eventos
                           FROM sesiones s LEFT JOIN eventos e ON e.sesion_id = s.id
                           GROUP BY s.id ORDER BY s.id DESC LIMIT %s""", (limite,)).fetchall()


def insertar_sesion(conn, usuario, hora_inicio, eventos, etiqueta=SIN_ETIQUETA, nota=None):
    """Registra una sesión nueva con sus eventos. eventos: lista de dicts
    {accion, host, resultado, objeto}. Devuelve el id de la sesión."""
    sid = conn.execute(
        """INSERT INTO sesiones (usuario, hora_inicio, etiqueta_real, nota)
           VALUES (%s,%s,%s,%s) RETURNING id""",
        (usuario, hora_inicio, etiqueta, nota)).fetchone()["id"]
    with conn.cursor() as cur:
        cur.executemany(
            """INSERT INTO eventos (sesion_id, accion, objeto, host_origen, resultado)
               VALUES (%s,%s,%s,%s,%s)""",
            [(sid, e["accion"], e.get("objeto"), e["host"], e.get("resultado", "exito")) for e in eventos])
    conn.commit()
    return sid


# ------------------------------------------------------------ MÓDULO DE EXPLICACIÓN
def guardar_alertas(conn, sesiones, resultados):
    """Guarda en la tabla alertas cada regla disparada, con su explicación.
    Reemplaza SOLO las alertas de las sesiones recibidas (no borra las de las demás)."""
    for s in sesiones:
        conn.execute("DELETE FROM alertas WHERE sesion_id = %s", (s["id"],))
    filas = [(s["id"], d["regla"]["id"], d["regla"]["entonces"], d["regla"]["severidad"],
              d["certeza"], d["explicacion"])
             for s in sesiones for d in resultados[s["id"]]["disparos"]]
    with conn.cursor() as cur:
        cur.executemany("""INSERT INTO alertas (sesion_id, regla_id, conclusion, severidad, certeza, explicacion)
                           VALUES (%s,%s,%s,%s,%s,%s)""", filas)
    conn.commit()
    return len(filas)


def explicaciones_de(conn, sesion_id):
    return [f["explicacion"] for f in conn.execute(
        "SELECT explicacion FROM alertas WHERE sesion_id = %s ORDER BY id", (sesion_id,)).fetchall()]


def resumen_alertas(conn):
    return conn.execute("""SELECT conclusion, severidad, COUNT(*) AS total
                           FROM alertas GROUP BY conclusion, severidad ORDER BY total DESC""").fetchall()
