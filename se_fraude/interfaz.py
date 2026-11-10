"""INTERFAZ DE USUARIO (consola): ingreso o selección de la sesión de acceso a diagnosticar."""
from db import (ACCIONES, RESULTADOS, listar_usuarios, listar_archivos_sensibles,
                listar_sesiones, insertar_sesion)


# ---------------------------------------------------------------- validación
def validar_datos_sesion(usuario, hora, eventos, usuarios_validos):
    """Devuelve la lista de errores (vacía si los datos son correctos)."""
    errores = []
    if usuario not in usuarios_validos:
        errores.append(f"El usuario '{usuario}' no existe.")
    if not isinstance(hora, int) or not 0 <= hora <= 23:
        errores.append("La hora de inicio debe ser un entero entre 0 y 23.")
    if not eventos:
        errores.append("La sesión debe tener al menos un evento.")
    for i, e in enumerate(eventos, 1):
        if e.get("accion") not in ACCIONES:
            errores.append(f"Evento {i}: acción '{e.get('accion')}' no permitida {ACCIONES}.")
        if e.get("resultado", "exito") not in RESULTADOS:
            errores.append(f"Evento {i}: resultado '{e.get('resultado')}' no válido {RESULTADOS}.")
        if not e.get("host"):
            errores.append(f"Evento {i}: falta el host de origen.")
    return errores


# ---------------------------------------------------------------- lectura segura
def leer_entero(mensaje, minimo, maximo):
    while True:
        txt = input(mensaje).strip()
        try:
            v = int(txt)
            if minimo <= v <= maximo:
                return v
        except ValueError:
            pass
        print(f"  Valor no válido: escriba un número entre {minimo} y {maximo}.")


def leer_texto(mensaje, por_defecto=""):
    txt = input(mensaje).strip()
    return txt or por_defecto


# ---------------------------------------------------------------- registrar sesión
def _elegir_usuario(usuarios):
    print("\nUsuarios disponibles:")
    for i, u in enumerate(usuarios, 1):
        rol = "administrador" if u["es_admin"] else "usuario"
        print(f"  {i}. {u['usuario']:<14} ({rol}, host habitual {u['host_habitual']})")
    return usuarios[leer_entero("Elija el usuario (número): ", 1, len(usuarios)) - 1]


def _leer_evento(usuario, sensibles):
    """Pide un evento. Devuelve la lista de eventos creados ([] = terminar)."""
    print("\n  Tipo de evento:  1) login   2) leer archivo   3) usar privilegios elevados (sudo)"
          "\n                   4) varios logins fallidos   0) terminar")
    op = leer_entero("  Opción: ", 0, 4)
    if op == 0:
        return []
    host = leer_texto(f"  Host de origen [Enter = habitual {usuario['host_habitual']}]: ",
                      usuario["host_habitual"])
    if op == 4:
        n = leer_entero("  ¿Cuántos logins fallidos? ", 1, 100)
        return [{"accion": "login", "host": host, "resultado": "fallo", "objeto": None} for _ in range(n)]
    if op == 1:
        res = leer_texto("  Resultado (exito/fallo) [exito]: ", "exito").lower()
        return [{"accion": "login", "host": host, "resultado": res, "objeto": None}]
    if op == 2:
        print(f"  Recursos sensibles: {', '.join(sensibles)}")
        obj = leer_texto("  Archivo/recurso leído: ", "/home/documento.txt")
        n = leer_entero("  ¿Cuántas veces? [1-100]: ", 1, 100)
        return [{"accion": "leer_archivo", "host": host, "resultado": "exito", "objeto": obj}
                for _ in range(n)]
    res = leer_texto("  Resultado (exito/fallo) [exito]: ", "exito").lower()
    return [{"accion": "usar_sudo", "host": host, "resultado": res, "objeto": "root"}]


def ingresar_sesion(conn):
    """Captura una sesión nueva, la valida y la guarda. Devuelve su id (o None si se cancela)."""
    usuarios = listar_usuarios(conn)
    sensibles = listar_archivos_sensibles(conn)
    usuario = _elegir_usuario(usuarios)
    hora = leer_entero("Hora de inicio de la sesión (0-23): ", 0, 23)
    eventos = []
    while True:
        nuevos = _leer_evento(usuario, sensibles)
        if not nuevos:
            break
        eventos += nuevos
        print(f"  -> {len(eventos)} evento(s) acumulados.")
    errores = validar_datos_sesion(usuario["usuario"], hora, eventos, {u["usuario"] for u in usuarios})
    if errores:
        print("\nNo se pudo registrar la sesión:")
        for e in errores:
            print("  -", e)
        return None
    sid = insertar_sesion(conn, usuario["usuario"], hora, eventos, nota="Registrada desde la interfaz")
    print(f"\nSesión #{sid} registrada con {len(eventos)} evento(s).")
    return sid


# ---------------------------------------------------------------- seleccionar sesión
def seleccionar_sesion(conn):
    """Muestra las últimas sesiones y devuelve el id elegido (o None)."""
    filas = listar_sesiones(conn)
    if not filas:
        print("No hay sesiones registradas. Ejecute inicializar.py.")
        return None
    print("\nÚltimas sesiones:")
    print(f"  {'Id':>4}  {'Usuario':<14}{'Hora':>5}  {'Eventos':>7}  Etiqueta real")
    for f in filas:
        print(f"  {f['id']:>4}  {f['usuario']:<14}{f['hora_inicio']:>5}  {f['n_eventos']:>7}  {f['etiqueta_real']}")
    sid = leer_entero("Número de sesión a diagnosticar (0 = cancelar): ", 0, 10**9)
    return sid or None


def menu():
    print("\n" + "-" * 72)
    print(" SE-FRAUDE · Diagnóstico de fraude en accesos financieros")
    print("-" * 72)
    print(" 1) Diagnosticar una sesión existente")
    print(" 2) Registrar una sesión nueva (y diagnosticarla)")
    print(" 3) Diagnosticar todas las sesiones (resumen de alertas)")
    print(" 4) Validar el sistema (matriz de confusión y matriz de pruebas)")
    print(" 5) Salir")
    return leer_entero("Opción: ", 1, 5)
