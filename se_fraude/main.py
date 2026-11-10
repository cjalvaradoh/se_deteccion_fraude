"""SE-FRAUDE: sistema experto de diagnóstico de fraude en accesos financieros (estilo IDES).

Requisito previo:   python inicializar.py
Menú interactivo:   python main.py
Sin menú (demo):    python main.py --validar          (validación completa + matriz de pruebas)
                    python main.py --sesion 52        (diagnostica la sesión 52)
                    python main.py --todas            (diagnostica todas las sesiones)
"""
import argparse

from db import conectar, cargar_reglas, cargar_sesiones, resumen_alertas
from sistema import diagnosticar_sesion, diagnosticar_todas
from interfaz import menu, ingresar_sesion, seleccionar_sesion
from resultados import mostrar_resultado, mostrar_resumen_alertas, mostrar_validacion


def diagnosticar_y_mostrar(conn, sesion_id, reglas):
    res = diagnosticar_sesion(conn, sesion_id, reglas)
    if res is None:
        print(f"La sesión #{sesion_id} no existe.")
        return
    mostrar_resultado(*res)


def accion_todas(conn, reglas):
    sesiones, _, n = diagnosticar_todas(conn, reglas)
    mostrar_resumen_alertas(resumen_alertas(conn), len(sesiones), len(reglas), n)


def accion_validar(conn, reglas):
    sesiones = cargar_sesiones(conn, solo_etiquetadas=True)
    mostrar_validacion(sesiones, reglas)


def bucle_menu(conn, reglas):
    while True:
        op = menu()
        if op == 1:
            sid = seleccionar_sesion(conn)
            if sid is not None:
                diagnosticar_y_mostrar(conn, sid, reglas)
        elif op == 2:
            sid = ingresar_sesion(conn)
            if sid is not None:
                diagnosticar_y_mostrar(conn, sid, reglas)
        elif op == 3:
            accion_todas(conn, reglas)
        elif op == 4:
            accion_validar(conn, reglas)
        else:
            print("Hasta pronto.")
            return


def main():
    ap = argparse.ArgumentParser(description="SE-FRAUDE")
    ap.add_argument("--validar", action="store_true", help="validación completa y matriz de pruebas")
    ap.add_argument("--sesion", type=int, help="diagnosticar la sesión indicada")
    ap.add_argument("--todas", action="store_true", help="diagnosticar todas las sesiones")
    a = ap.parse_args()
    with conectar() as conn:
        reglas = cargar_reglas(conn)            # base de conocimiento (tabla reglas)
        if a.sesion is not None:
            diagnosticar_y_mostrar(conn, a.sesion, reglas)
        elif a.todas:
            accion_todas(conn, reglas)
        elif a.validar:
            accion_todas(conn, reglas)
            accion_validar(conn, reglas)
        else:
            bucle_menu(conn, reglas)


if __name__ == "__main__":
    main()
