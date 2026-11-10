"""VALIDACIÓN Y VERIFICACIÓN (según el temario de la clase).

1) Verificación estructural : reglas duplicadas, contradictorias, inalcanzables, sin disparar
2) Casos de prueba          : matriz de confusión sobre casos históricos + casos límite
3) Análisis de sensibilidad : ¿qué pasa si se mueve un umbral de una regla?
4) Matriz de pruebas        : una fila por caso (esperado vs obtenido) -> anexo del informe de la Fase 3
"""
import copy
import csv
import os
from motor import diagnosticar, HECHOS_BASE


def verificar_estructura(reglas, sesiones):
    hallazgos = []
    conclusiones = {r["entonces"] for r in reglas}
    vistas = {}
    for r in reglas:
        for campo, _, _ in r["si"]:                                   # reglas inalcanzables
            if campo not in HECHOS_BASE and campo not in conclusiones:
                hallazgos.append(f"{r['id']}: usa '{campo}' pero nadie lo produce (inalcanzable)")
        clave = tuple(sorted(map(str, r["si"])))
        if clave in vistas:                                           # duplicadas / contradictorias
            o = vistas[clave]
            tipo = "CONTRADICTORIA" if (o["entonces"], o["severidad"]) != (r["entonces"], r["severidad"]) else "REDUNDANTE"
            hallazgos.append(f"{r['id']} y {o['id']} tienen las mismas condiciones ({tipo})")
        vistas[clave] = r
    disparadas = {d["regla"]["id"] for s in sesiones for d in diagnosticar(s["hechos"], reglas)["disparos"]}
    for r in reglas:                                                  # reglas que nunca se activan
        if r["id"] not in disparadas:
            hallazgos.append(f"{r['id']}: nunca se disparó con los casos de prueba")
    return hallazgos or ["Sin hallazgos"]


def matriz_confusion(sesiones, reglas):
    vp = fp = fn = vn = 0
    errores = []
    for s in sesiones:
        real = s["real"] != "normal"
        pred = diagnosticar(s["hechos"], reglas)["alerta"]
        if real and pred:   vp += 1
        elif pred:          fp += 1; errores.append(("FALSO POSITIVO", s))
        elif real:          fn += 1; errores.append(("FALSO NEGATIVO", s))
        else:               vn += 1
    div = lambda a, b: a / b if b else 0.0
    prec, rec = div(vp, vp + fp), div(vp, vp + fn)
    return {"VP": vp, "FP": fp, "FN": fn, "VN": vn,
            "exactitud": div(vp + vn, len(sesiones)), "precisión": prec,
            "sensibilidad": rec, "especificidad": div(vn, vn + fp),
            "F1": div(2 * prec * rec, prec + rec)}, errores


def sensibilidad(sesiones, reglas, regla_id, valores):
    """Cambia el umbral de una regla y mide el efecto en los errores."""
    filas = []
    for v in valores:
        rs = copy.deepcopy(reglas)
        for r in rs:
            if r["id"] == regla_id:
                campo, op, _ = r["si"][0]
                r["si"][0] = (campo, op, v)
        m, _ = matriz_confusion(sesiones, rs)
        filas.append((v, m["FP"], m["FN"], m["sensibilidad"], m["precisión"]))
    return filas


# ---------------------------------------------------------------- MATRIZ DE PRUEBAS
# Regla que debería dispararse según el tipo de ataque simulado
ESPERADAS = {"fuerza_bruta": ["R1"], "suplantacion": ["R3"], "acceso_sensible": ["R4"],
             "escalada_privilegios": ["R5"], "exfiltracion": ["R6"]}

COLUMNAS = ["id_caso", "categoria", "usuario", "tipo_real", "descripcion", "resultado_esperado",
            "reglas_esperadas", "reglas_disparadas", "resultado_obtenido", "severidad", "certeza", "prueba"]


def matriz_de_pruebas(sesiones, reglas):
    """Una fila por caso: qué se esperaba, qué se obtuvo y si la prueba pasó."""
    filas = []
    for s in sesiones:
        d = diagnosticar(s["hechos"], reglas)
        es_ataque = s["real"] != "normal"
        es_limite = (s["nota"] or "").startswith("LÍMITE")
        obtenido = "ALERTA" if d["alerta"] else "SIN ALERTA"
        esperado = "ALERTA" if es_ataque else "SIN ALERTA"
        if obtenido == esperado:
            prueba = "OK"
        else:
            prueba = "ERROR (falso negativo)" if es_ataque else "ERROR (falso positivo)"
        descripcion = (s["nota"] or "").replace("LÍMITE: ", "") or \
            (f"Ataque simulado: {s['real']}" if es_ataque else "Sesión normal de trabajo")
        filas.append({
            "id_caso": f"CP-{s['id']:02d}",
            "categoria": "Límite" if es_limite else ("Ataque" if es_ataque else "Normal"),
            "usuario": s["usuario"], "tipo_real": s["real"], "descripcion": descripcion,
            "resultado_esperado": esperado,
            "reglas_esperadas": ",".join(ESPERADAS.get(s["real"], [])) or "-",
            "reglas_disparadas": ",".join(x["regla"]["id"] for x in d["disparos"]) or "-",
            "resultado_obtenido": obtenido, "severidad": d["severidad"],
            "certeza": f"{d['certeza']:.2f}", "prueba": prueba})
    return filas


def exportar_matriz_csv(filas, ruta="reportes/matriz_de_pruebas.csv"):
    """Guarda la matriz en CSV (utf-8 con BOM para que Excel respete los acentos)."""
    carpeta = os.path.dirname(ruta)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS)
        w.writeheader()
        w.writerows(filas)
    return ruta
