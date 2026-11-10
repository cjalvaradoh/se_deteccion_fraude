"""PRUEBAS DE VALIDACIÓN con los 56 casos (sin base de datos)."""
import csv

from reglas import REGLAS
from validar import (matriz_confusion, verificar_estructura, sensibilidad,
                     matriz_de_pruebas, exportar_matriz_csv)
from tests.util import sesiones_en_memoria


def test_hay_56_casos():
    assert len(sesiones_en_memoria()) == 56


def test_matriz_de_confusion_esperada():
    m, errores = matriz_confusion(sesiones_en_memoria(), REGLAS)
    assert (m["VP"], m["FN"], m["FP"], m["VN"]) == (21, 1, 2, 32)
    assert round(m["exactitud"], 2) == 0.95 and round(m["F1"], 2) == 0.93
    # los 3 errores son casos límite documentados
    assert all(s["nota"].startswith("LÍMITE") for _, s in errores) and len(errores) == 3


def test_verificacion_estructural_sin_hallazgos():
    assert verificar_estructura(REGLAS, sesiones_en_memoria()) == ["Sin hallazgos"]


def test_sensibilidad_r1_y_r6():
    ses = sesiones_en_memoria()
    r1 = {v: (fp, fn) for v, fp, fn, *_ in sensibilidad(ses, REGLAS, "R1", [3, 5, 8])}
    assert r1[5] == (2, 1) and r1[3][1] == 0                     # bajar a 3 elimina el FN
    r6 = {v: fp for v, fp, *_ in sensibilidad(ses, REGLAS, "R6", [10, 20, 30])}
    assert r6[20] == 2 and r6[10] == 13                          # bajar a 10 sube los FP a 13


def test_matriz_de_pruebas_y_csv(tmp_path):
    filas = matriz_de_pruebas(sesiones_en_memoria(), REGLAS)
    assert len(filas) == 56 and sum(f["prueba"] == "OK" for f in filas) == 53
    assert {f["prueba"] for f in filas if f["prueba"] != "OK"} == {"ERROR (falso negativo)",
                                                                   "ERROR (falso positivo)"}
    ruta = exportar_matriz_csv(filas, str(tmp_path / "m.csv"))
    leidas = list(csv.DictReader(open(ruta, encoding="utf-8-sig")))
    assert len(leidas) == 56 and leidas[0]["id_caso"] == "CP-01"
