# SE-FRAUDE · Sistema experto de diagnóstico de fraude en accesos financieros

Sistema experto basado en reglas (SI–ENTONCES con factor de certeza) que diagnostica sesiones de acceso
a sistemas de una entidad financiera. Python + PostgreSQL (Neon o local). Encadenamiento **hacia adelante**.
Proyecto final de Sistemas Expertos (USPG), inspirado en IDES de SRI.

## Cómo ejecutarlo
1. `pip install -r requirements.txt`
2. Copie `.env.example` a `.env` y ponga su `DATABASE_URL` (Neon: copie la cadena de conexión del panel).
3. `python inicializar.py` → crea las 6 tablas, carga 6 reglas y 56 sesiones de prueba (se puede repetir: borra y recrea).
4. `python main.py` → menú interactivo.

## Limitaciones
Datos simulados; umbrales fijos (causa de los casos límite); cada sesión se analiza de forma independiente.
Falta validar las reglas con datos reales y un experto.
