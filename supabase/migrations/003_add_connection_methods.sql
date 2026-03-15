-- ============================================================
-- MIGRACIÓN 003b: Métodos de conexión completos en saas_credenciales_bd
-- Evangelista & Co. | Sentinel Decision Intelligence V2
-- ============================================================
-- Ejecutar en Supabase SQL Editor DESPUÉS de 003_add_connection_type.sql
-- Usa IF NOT EXISTS en todo — seguro de correr múltiples veces
-- ============================================================

-- Columna principal de método (sustituye/complementa tipo_conexion)
ALTER TABLE saas_credenciales_bd
    ADD COLUMN IF NOT EXISTS metodo_conexion VARCHAR(20) DEFAULT 'sql_directo'
        CHECK (metodo_conexion IN ('api_rest', 'sql_directo'));

-- ── API REST / GraphQL ────────────────────────────────────────────────────────
ALTER TABLE saas_credenciales_bd
    ADD COLUMN IF NOT EXISTS api_endpoint        TEXT,
    ADD COLUMN IF NOT EXISTS api_auth_method     VARCHAR(50),   -- bearer | api_key | basic_auth | oauth2
    ADD COLUMN IF NOT EXISTS api_token_encrypted TEXT,          -- Token / API Key encriptado (AES)
    ADD COLUMN IF NOT EXISTS api_headers_json    TEXT;          -- JSON de headers adicionales

-- ── Base de Datos SQL Directo ─────────────────────────────────────────────────
ALTER TABLE saas_credenciales_bd
    ADD COLUMN IF NOT EXISTS db_type               VARCHAR(20)
        CHECK (db_type IN ('postgresql', 'mysql', 'sqlserver', 'oracle', 'sqlite')),
    ADD COLUMN IF NOT EXISTS db_host               TEXT,
    ADD COLUMN IF NOT EXISTS db_port               INTEGER,
    ADD COLUMN IF NOT EXISTS db_usuario            TEXT,
    ADD COLUMN IF NOT EXISTS db_password_encrypted TEXT,        -- Contraseña encriptada (AES)
    ADD COLUMN IF NOT EXISTS db_nombre             TEXT,
    ADD COLUMN IF NOT EXISTS db_esquema            VARCHAR(100); -- Opcional, para PostgreSQL / Oracle

-- ── Índices ───────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_credenciales_metodo
    ON saas_credenciales_bd (metodo_conexion);

CREATE INDEX IF NOT EXISTS idx_credenciales_cliente_metodo
    ON saas_credenciales_bd (cliente_id, metodo_conexion);

-- ── Comentarios ───────────────────────────────────────────────────────────────
COMMENT ON COLUMN saas_credenciales_bd.metodo_conexion IS
    'Método de extracción: api_rest = API REST/GraphQL | sql_directo = SQL directo';
COMMENT ON COLUMN saas_credenciales_bd.api_auth_method IS
    'bearer | api_key | basic_auth | oauth2';
COMMENT ON COLUMN saas_credenciales_bd.api_token_encrypted IS
    'Token/API Key encriptado con Fernet (AES-128-CBC + HMAC-SHA256)';
COMMENT ON COLUMN saas_credenciales_bd.api_headers_json IS
    'Headers HTTP adicionales en formato JSON. Ej: {"X-Tenant": "abc"}';
COMMENT ON COLUMN saas_credenciales_bd.db_type IS
    'Motor de base de datos: postgresql | mysql | sqlserver | oracle | sqlite';
COMMENT ON COLUMN saas_credenciales_bd.db_password_encrypted IS
    'Contraseña encriptada con Fernet (AES-128-CBC + HMAC-SHA256)';
COMMENT ON COLUMN saas_credenciales_bd.db_esquema IS
    'Esquema SQL opcional (search_path en PostgreSQL, schema en Oracle)';
