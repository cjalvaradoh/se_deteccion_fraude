-- Se ejecuta con: python inicializar.py   (recrea todas las tablas)

DROP TABLE IF EXISTS alertas CASCADE;
DROP TABLE IF EXISTS eventos CASCADE;
DROP TABLE IF EXISTS sesiones CASCADE;
DROP TABLE IF EXISTS reglas CASCADE;
DROP TABLE IF EXISTS archivos_sensibles CASCADE;
DROP TABLE IF EXISTS usuarios CASCADE;

-- Datos de referencia
CREATE TABLE usuarios (
  usuario      TEXT PRIMARY KEY,
  host_habitual TEXT NOT NULL,
  es_admin     BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE archivos_sensibles (
  ruta TEXT PRIMARY KEY
);

-- BASE DE HECHOS: sesiones y los eventos que ocurrieron en cada una
CREATE TABLE sesiones (
  id            SERIAL PRIMARY KEY,
  usuario       TEXT NOT NULL REFERENCES usuarios(usuario),
  hora_inicio   INT  NOT NULL,                 -- 0 a 23
  etiqueta_real TEXT NOT NULL DEFAULT 'normal',-- normal / fuerza_bruta / ... / sin_etiqueta (solo para validar)
  nota          TEXT
);

CREATE TABLE eventos (
  id          SERIAL PRIMARY KEY,
  sesion_id   INT  NOT NULL REFERENCES sesiones(id),
  accion      TEXT NOT NULL,                   -- login, leer_archivo, usar_sudo
  objeto      TEXT,
  host_origen TEXT NOT NULL,
  resultado   TEXT NOT NULL DEFAULT 'exito'    -- exito / fallo
);

-- BASE DE CONOCIMIENTOS: las reglas SI-ENTONCES
CREATE TABLE reglas (
  id          TEXT PRIMARY KEY,                -- R1, R2...
  descripcion TEXT NOT NULL,
  condicion   JSONB NOT NULL,                  -- [["fallos_login", ">=", 5], ...]
  conclusion  TEXT NOT NULL,
  severidad   TEXT NOT NULL,                   -- baja / media / alta
  certeza     NUMERIC(3,2) NOT NULL,
  activa      BOOLEAN NOT NULL DEFAULT TRUE
);

-- MÓDULO DE EXPLICACIÓN: qué regla se disparó y por qué
CREATE TABLE alertas (
  id          SERIAL PRIMARY KEY,
  sesion_id   INT  NOT NULL REFERENCES sesiones(id),
  regla_id    TEXT NOT NULL REFERENCES reglas(id),
  conclusion  TEXT NOT NULL,
  severidad   TEXT NOT NULL,
  certeza     NUMERIC(3,2) NOT NULL,
  explicacion TEXT NOT NULL
);

CREATE INDEX idx_eventos_sesion ON eventos (sesion_id);
