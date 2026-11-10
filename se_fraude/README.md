# SE-FRAUDE · Sistema experto de diagnóstico de fraude en accesos financieros

Sistema experto basado en reglas (SI–ENTONCES con factor de certeza) que diagnostica sesiones de acceso
a sistemas de una entidad financiera. Python + PostgreSQL (Neon o local). Encadenamiento **hacia adelante**.
Proyecto final de Sistemas Expertos (USPG), inspirado en IDES de SRI.

## Cómo ejecutarlo
1. `pip install -r requirements.txt`
2. Copie `.env.example` a `.env` y ponga su `DATABASE_URL` (Neon: copie la cadena de conexión del panel).
3. `python inicializar.py` → crea las 6 tablas, carga 6 reglas y 56 sesiones de prueba (se puede repetir: borra y recrea).
4. `python main.py` → menú interactivo.

Atajos para la demostración (sin menú):

| Comando | Qué hace |
|---|---|
| `python main.py --sesion 31` | Diagnostica la sesión 31 y muestra la explicación |
| `python main.py --todas` | Diagnostica las 56 sesiones y resume las alertas |
| `python main.py --validar` | Verificación estructural, matriz de confusión, sensibilidad y **matriz de pruebas** (guarda `reportes/matriz_de_pruebas.csv`) |

## Componentes (según el documento de la Fase 1)
| Componente | Archivo(s) | Tabla(s) |
|---|---|---|
| Interfaz de usuario (ingreso / selección de sesión) | `interfaz.py` | `sesiones`, `eventos` |
| Base de hechos | `db.py` (`SQL_HECHOS`), `datos.py` | `usuarios`, `sesiones`, `eventos`, `archivos_sensibles` |
| Base de conocimiento | `reglas.py` → `inicializar.py` | `reglas` |
| Motor de inferencia | `motor.py` | — |
| Interfaz de resultados y explicación | `resultados.py`, `sistema.py` | `alertas` |
| Validación y matriz de pruebas | `validar.py` | — |

Menú de `main.py`: 1) diagnosticar sesión existente, 2) registrar sesión nueva y diagnosticarla,
3) diagnosticar todas, 4) validar el sistema, 5) salir.

## Reglas
| Id | Condición | Conclusión | Sev. | Certeza |
|---|---|---|---|---|
| R1 | fallos_login ≥ 5 | intento_fuerza_bruta | media | 0.80 |
| R2 | intento_fuerza_bruta y host_nuevo | fuerza_bruta_externa | alta | 0.95 (× 0.80 = 0.76) |
| R3 | login_exitoso, host_nuevo, fuera_horario | posible_suplantacion | alta | 0.85 |
| R4 | lee_sensible y no es_admin | acceso_no_autorizado | media | 0.75 |
| R5 | usa_sudo (privilegios elevados) y no es_admin | escalada_privilegios | alta | 0.85 |
| R6 | lecturas ≥ 20 | posible_exfiltracion | alta | 0.80 |

## Pruebas
- **Unitarias y de validación (no necesitan base de datos):** `python -m pytest`
- **Integrales (PostgreSQL real):** defina `TEST_DATABASE_URL` y ejecute `python -m pytest`.
  ⚠ `inicializar()` borra las tablas: use una base de pruebas (en Neon, una *branch* o base aparte), no la de la demostración.
  Sin esa variable las integrales se omiten (aparecen como *skipped*).

Qué se prueba: umbrales de R1 y R6 (4/5 fallos, 19/20 lecturas), encadenamiento R1→R2 (certeza 0.76),
excepción del administrador, severidad global, explicación en cada alerta, los 56 casos, que los hechos calculados
por SQL coinciden con los calculados en Python, que diagnosticar una sesión no borra las alertas de otras,
sesiones sin eventos, registro de sesión nueva y el flujo completo del menú.

## Resultado de la validación (56 casos)
VP = 21, FN = 1, FP = 2, VN = 32 → exactitud 0.95, precisión 0.91, sensibilidad 0.95, especificidad 0.94, F1 0.93.
Los 3 errores son casos límite documentados:
- **FN:** fuerza bruta lenta con 4 fallos (bajo el umbral de R1).
- **FP:** respaldo legítimo de 20 lecturas (R6).
- **FP:** colaborador que viaja y trabaja a las 21:00 desde otra red (R3).

Sensibilidad: bajar el umbral de R1 de 5 a 3 elimina el FN; bajar el de R6 de 20 a 10 sube los FP de 2 a 13.

## Cambios respecto a la versión DRA original
- **Nuevo:** `interfaz.py` (ingreso con validación y selección de sesión), `resultados.py` (pantalla de resultado y
  explicación), `sistema.py` (flujo hechos → inferencia → alertas), pruebas en `tests/`, matriz de pruebas (CSV),
  `.env.example`.
- **Corregido:** `guardar_alertas` ya no borra las alertas de todas las sesiones, solo las de la sesión diagnosticada.
- **Corregido:** `SQL_HECHOS` usa `LEFT JOIN`, así una sesión sin eventos no desaparece.
- **Corregido:** `casos_de_prueba()` es determinista en cada llamada (`random.seed(42)` dentro de la función).
- **Mejorado:** `main.py` es el programa principal (menú + atajos `--sesion`, `--todas`, `--validar`);
  las sesiones registradas por el analista usan la etiqueta `sin_etiqueta` y no entran en la validación.
- **Enfoque financiero:** los recursos sensibles simulados ahora son del core financiero
  (`/core/cuentas_clientes`, `/core/usuarios_sistema`, `/core/clientes.sql`); los nombres técnicos de hechos y columnas no cambian.
- El README anterior mencionaba `psycopg2`; el proyecto usa `psycopg` 3 (ver `requirements.txt`).

## Limitaciones
Datos simulados; umbrales fijos (causa de los casos límite); cada sesión se analiza de forma independiente.
Falta validar las reglas con datos reales y un experto.
