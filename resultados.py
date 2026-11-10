"""INTERFAZ DE RESULTADOS Y EXPLICACIÓN: todo lo que se muestra en pantalla."""
from validar import (verificar_estructura, matriz_confusion, sensibilidad,
                     matriz_de_pruebas, exportar_matriz_csv)

NOMBRES = {  # nombre técnico del hecho -> texto para el analista
    "fallos_login": "Intentos de login fallidos",
    "login_exitoso": "Login exitoso",
    "host_nuevo": "Origen distinto al habitual",
    "fuera_horario": "Fuera de horario (antes de 6:00 o desde 20:00)",
    "es_admin": "Usuario administrador",
    "lee_sensible": "Lee recursos sensibles",
    "usa_sudo": "Usa privilegios elevados",
    "lecturas": "Archivos leídos",
}


def titulo(t):
    print(f"\n{'=' * 72}\n{t}\n{'=' * 72}")


def _valor(v):
    return "Sí" if v is True else "No" if v is False else str(v)


def mostrar_resultado(sesion, diagnostico, explicaciones):
    """Muestra el diagnóstico de una sesión y la explicación de cada regla disparada."""
    titulo(f"DIAGNÓSTICO  |  Sesión #{sesion['id']}  |  usuario: {sesion['usuario']}")
    print(f"Hora de inicio: {sesion['hora_inicio']}:00   Etiqueta real: {sesion['real']}")
    print("\nHechos de la sesión:")
    for k, v in sesion["hechos"].items():
        print(f"  - {NOMBRES.get(k, k):<48} {_valor(v)}")
    print()
    if diagnostico["alerta"]:
        print(f"RESULTADO: *** ALERTA ***  severidad {diagnostico['severidad'].upper()}  "
              f"certeza {diagnostico['certeza']:.0%}")
        print("\nExplicación (reglas disparadas, en orden de inferencia):")
        for linea in explicaciones:
            print(f"  {linea}")
    else:
        print("RESULTADO: sin alerta. Ninguna regla se cumple: la sesión parece normal.")


def mostrar_resumen_alertas(filas, n_sesiones, n_reglas, n_alertas):
    titulo(f"INFERENCIA: {n_sesiones} sesiones, {n_reglas} reglas, {n_alertas} alertas guardadas")
    print(f"  {'conclusión':<26}{'severidad':<11}total")
    for f in filas:
        print(f"  {f['conclusion']:<26}{f['severidad']:<11}{f['total']}")


def mostrar_validacion(sesiones, reglas, ruta_csv="reportes/matriz_de_pruebas.csv"):
    titulo("VERIFICACIÓN ESTRUCTURAL de la base de conocimiento")
    for h in verificar_estructura(reglas, sesiones):
        print(" -", h)

    titulo(f"VALIDACIÓN con {len(sesiones)} casos de prueba (matriz de confusión)")
    m, errores = matriz_confusion(sesiones, reglas)
    print("               Predice ATAQUE   Predice NORMAL")
    print(f"Real ATAQUE    VP = {m['VP']:<10}   FN = {m['FN']}")
    print(f"Real NORMAL    FP = {m['FP']:<10}   VN = {m['VN']}")
    print(f"\nExactitud={m['exactitud']:.2f}  Precisión={m['precisión']:.2f}  "
          f"Sensibilidad={m['sensibilidad']:.2f}  Especificidad={m['especificidad']:.2f}  F1={m['F1']:.2f}")
    print("\nErrores encontrados:")
    for tipo, s in errores:
        print(f" - {tipo}: sesión #{s['id']} ({s['usuario']}) -> {s['nota']}")

    titulo("ANÁLISIS DE SENSIBILIDAD de umbrales")
    for rid, nombre, valores in [("R1", "fallos de login", [3, 5, 8]), ("R6", "lecturas", [10, 20, 30])]:
        print(f"\n{rid} (umbral de {nombre}):")
        print("  umbral   FP   FN   sensibilidad   precisión")
        for v, fp, fn, rec, prec in sensibilidad(sesiones, reglas, rid, valores):
            print(f"  {v:>6}  {fp:>3}  {fn:>3}   {rec:>11.2f}   {prec:>9.2f}")

    titulo("MATRIZ DE PRUEBAS (esperado vs obtenido)")
    filas = matriz_de_pruebas(sesiones, reglas)
    print(f"  {'Caso':<7}{'Categoría':<10}{'Usuario':<13}{'Esperado':<12}{'Obtenido':<12}{'Reglas':<10}Prueba")
    for f in filas:
        print(f"  {f['id_caso']:<7}{f['categoria']:<10}{f['usuario']:<13}{f['resultado_esperado']:<12}"
              f"{f['resultado_obtenido']:<12}{f['reglas_disparadas']:<10}{f['prueba']}")
    ok = sum(f["prueba"] == "OK" for f in filas)
    print(f"\n  Pruebas OK: {ok} de {len(filas)}")
    print(f"  Matriz guardada en: {exportar_matriz_csv(filas, ruta_csv)}")
    return m, filas
