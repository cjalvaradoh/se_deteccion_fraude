"""BASE DE CONOCIMIENTOS: reglas SI-ENTONCES con factor de certeza.

Cada regla: si todas las condiciones se cumplen -> se concluye algo.
Las conclusiones pasan a ser nuevos hechos (así una regla puede apoyarse en otra:
encadenamiento hacia adelante, ver R2).
"""

REGLAS = [
    {"id": "R1", "descripcion": "5 o más logins fallidos en la sesión",
     "si": [("fallos_login", ">=", 5)],
     "entonces": "intento_fuerza_bruta", "severidad": "media", "certeza": 0.80},

    {"id": "R2", "descripcion": "Fuerza bruta desde un host que el usuario nunca usa",
     "si": [("intento_fuerza_bruta", "==", True), ("host_nuevo", "==", True)],
     "entonces": "fuerza_bruta_externa", "severidad": "alta", "certeza": 0.95},

    {"id": "R3", "descripcion": "Login exitoso fuera de horario desde host no habitual",
     "si": [("login_exitoso", "==", True), ("host_nuevo", "==", True),
            ("fuera_horario", "==", True)],
     "entonces": "posible_suplantacion", "severidad": "alta", "certeza": 0.85},

    {"id": "R4", "descripcion": "Usuario no administrador lee un archivo sensible",
     "si": [("lee_sensible", "==", True), ("es_admin", "==", False)],
     "entonces": "acceso_no_autorizado", "severidad": "media", "certeza": 0.75},

    {"id": "R5", "descripcion": "Usuario no administrador usa sudo",
     "si": [("usa_sudo", "==", True), ("es_admin", "==", False)],
     "entonces": "escalada_privilegios", "severidad": "alta", "certeza": 0.85},

    {"id": "R6", "descripcion": "20 o más archivos leídos en la sesión",
     "si": [("lecturas", ">=", 20)],
     "entonces": "posible_exfiltracion", "severidad": "alta", "certeza": 0.80},
]
