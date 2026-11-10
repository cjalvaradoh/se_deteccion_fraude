"""BASE DE HECHOS (simulada): sesiones de acceso a sistemas financieros con su etiqueta real.

Una 'sesión' es la ventana de observación de un usuario. Cada sesión es un caso
de prueba: se sabe de antemano si fue normal o un ataque (estándar de referencia).
"""
import random

random.seed(42)  # resultados repetibles

USUARIOS = {  # perfil conocido de cada usuario
    "ana":         {"host": "10.0.0.11", "admin": False},
    "luis":        {"host": "10.0.0.12", "admin": False},
    "carla":       {"host": "10.0.0.13", "admin": False},
    "pedro":       {"host": "10.0.0.14", "admin": False},
    "marta_admin": {"host": "10.0.0.10", "admin": True},
}
ARCHIVOS_SENSIBLES = {"/core/cuentas_clientes", "/core/usuarios_sistema", "/core/clientes.sql"}
HOST_EXTERNO = "203.0.113.45"
NO_ADMINS = [u for u, p in USUARIOS.items() if not p["admin"]]


def ev(accion, host, resultado="exito", objeto=None):
    return {"accion": accion, "host": host, "resultado": resultado, "objeto": objeto}


def sesion(id_, usuario, hora, eventos, real="normal", nota=""):
    return {"id": id_, "usuario": usuario, "hora_inicio": hora,
            "eventos": eventos, "real": real, "nota": nota}


def _normal(u):
    h = USUARIOS[u]["host"]
    e = []
    if random.random() < 0.10:                       # error de tecleo ocasional
        e.append(ev("login", h, "fallo"))
    e.append(ev("login", h))
    e += [ev("leer_archivo", h, objeto=f"/home/{u}/doc{random.randint(1, 3)}.txt")
          for _ in range(random.randint(5, 12))]
    if USUARIOS[u]["admin"]:                         # el admin usa privilegios elevados (sudo) con normalidad
        e += [ev("usar_sudo", h, objeto="root") for _ in range(random.randint(1, 3))]
        e.append(ev("leer_archivo", h, objeto="/core/usuarios_sistema"))
    return e


def _ataque(tipo, u):
    h = USUARIOS[u]["host"]
    if tipo == "fuerza_bruta":
        return 2, [ev("login", HOST_EXTERNO, "fallo") for _ in range(8)]
    if tipo == "suplantacion":
        return 3, [ev("login", HOST_EXTERNO)] + [
            ev("leer_archivo", HOST_EXTERNO, objeto=f"/home/{u}/doc{i}.txt") for i in (1, 2)]
    if tipo == "acceso_sensible":
        return 11, [ev("login", h), ev("leer_archivo", h, objeto="/core/cuentas_clientes"),
                    ev("leer_archivo", h, objeto="/core/clientes.sql")]
    if tipo == "escalada_privilegios":
        return 14, [ev("login", h)] + [ev("usar_sudo", h, "fallo", "root") for _ in range(3)] \
                   + [ev("usar_sudo", h, objeto="root")]
    if tipo == "exfiltracion":
        return 15, [ev("login", h)] + [
            ev("leer_archivo", h, objeto=f"/home/{u}/docs/doc_{k}.pdf") for k in range(40)]


def casos_de_prueba():
    random.seed(42)  # cada llamada genera exactamente los mismos 56 casos
    casos, n = [], 0
    # --- Casos históricos: 30 sesiones normales + 20 ataques (4 de cada tipo)
    for u in USUARIOS:
        for _ in range(6):
            n += 1
            casos.append(sesion(n, u, random.randint(7, 9), _normal(u)))
    tipos = ["fuerza_bruta", "suplantacion", "acceso_sensible",
             "escalada_privilegios", "exfiltracion"]
    for tipo in tipos:
        for i in range(4):
            n += 1
            u = NO_ADMINS[i % len(NO_ADMINS)]
            hora, eventos = _ataque(tipo, u)
            casos.append(sesion(n, u, hora, eventos, tipo))

    # --- Casos críticos o límite (escritos a mano)
    h = USUARIOS["ana"]["host"]
    limites = [
        ("luis", 2, [ev("login", HOST_EXTERNO, "fallo") for _ in range(4)], "fuerza_bruta",
         "Fuerza bruta lenta: solo 4 fallos (bajo el umbral)"),
        ("pedro", 2, [ev("login", HOST_EXTERNO, "fallo") for _ in range(5)], "fuerza_bruta",
         "Fuerza bruta con exactamente 5 fallos (en el umbral)"),
        ("marta_admin", 10, [ev("login", USUARIOS["marta_admin"]["host"]),
                             ev("usar_sudo", "10.0.0.10", objeto="root"),
                             ev("leer_archivo", "10.0.0.10", objeto="/core/cuentas_clientes")], "normal",
         "Admin usa privilegios elevados (sudo) y lee /core/cuentas_clientes (legítimo)"),
        ("ana", 10, [ev("login", h)] + [ev("leer_archivo", h, objeto=f"/home/ana/d{k}") for k in range(19)],
         "normal", "19 lecturas (justo bajo el umbral)"),
        ("ana", 10, [ev("login", h)] + [ev("leer_archivo", h, objeto=f"/home/ana/d{k}") for k in range(20)],
         "normal", "20 lecturas legítimas (respaldo de ana)"),
        ("carla", 21, [ev("login", HOST_EXTERNO), ev("leer_archivo", HOST_EXTERNO, objeto="/home/carla/doc1.txt")],
         "normal", "Carla viaja y trabaja a las 21:00 desde otra red (legítimo)"),
    ]
    for u, hora, eventos, real, nota in limites:
        n += 1
        casos.append(sesion(n, u, hora, eventos, real, "LÍMITE: " + nota))
    return casos
