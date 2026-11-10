"""MOTOR DE INFERENCIA + MÓDULO DE EXPLICACIÓN (no toca la base de datos).

inferir  : encadenamiento hacia adelante con factores de certeza
explicar : traza de qué regla se disparó y por qué
"""
import operator

OPS = {"==": operator.eq, "!=": operator.ne, ">=": operator.ge,
       "<=": operator.le, ">": operator.gt, "<": operator.lt}
ORDEN_SEV = {"baja": 0, "media": 1, "alta": 2}

# Hechos que calcula la consulta SQL (sirve para la verificación estructural)
HECHOS_BASE = {"fallos_login", "login_exitoso", "host_nuevo", "fuera_horario",
               "es_admin", "lee_sensible", "usa_sudo", "lecturas"}


def inferir(hechos, reglas):
    """Dispara reglas hasta que no haya ninguna nueva. Cada conclusión se vuelve un hecho."""
    hechos, certezas, disparos = dict(hechos), {}, []
    pendientes, hubo_cambio = list(reglas), True
    while hubo_cambio:
        hubo_cambio = False
        for r in list(pendientes):
            if all(OPS[op](hechos.get(c, False), v) for c, op, v in r["si"]):
                # certeza = certeza de la regla x la más baja de las conclusiones previas usadas
                cf = r["certeza"] * min([certezas.get(c, 1.0) for c, _, _ in r["si"]])
                hechos[r["entonces"]], certezas[r["entonces"]] = True, cf
                disparos.append({"regla": r, "certeza": round(cf, 2),
                                 "usados": {c: hechos[c] for c, _, _ in r["si"]}})
                pendientes.remove(r)
                hubo_cambio = True
    return disparos


def explicar(d):
    r = d["regla"]
    usados = ", ".join(f"{c}={v}" for c, v in d["usados"].items())
    return (f"[{r['id']}] {r['descripcion']} -> {r['entonces']} "
            f"(severidad {r['severidad']}, certeza {d['certeza']:.0%}). Porque: {usados}")


def diagnosticar(hechos, reglas):
    disparos = inferir(hechos, reglas)
    for d in disparos:
        d["explicacion"] = explicar(d)
    return {
        "disparos": disparos,
        "alerta": bool(disparos),
        "severidad": max((d["regla"]["severidad"] for d in disparos), key=ORDEN_SEV.get, default="ninguna"),
        "certeza": max((d["certeza"] for d in disparos), default=0),
    }
