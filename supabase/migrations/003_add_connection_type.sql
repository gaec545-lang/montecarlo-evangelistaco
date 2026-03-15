-- ============================================================
-- MIGRACIÓN 003: Conexiones versátiles en saas_credenciales_bd
-- Evangelista & Co. | Sentinel Decision Intelligence V2
-- ============================================================
-- Ejecutar en Supabase SQL Editor (una sola vez)
-- ============================================================

-- Agregar tipo de conexión (tradicional SQL vs. API REST)
ALTER TABLE saas_credenciales_bd
    ADD COLUMN IF NOT EXISTS tipo_conexion VARCHAR(20) DEFAULT 'tradicional'
        CHECK (tipo_conexion IN ('tradicional', 'api'));

-- Columnas para conexión API
ALTER TABLE saas_credenciales_bd
    ADD COLUMN IF NOT EXISTS api_endpoint      TEXT,
    ADD COLUMN IF NOT EXISTS api_key_encrypted TEXT,
    ADD COLUMN IF NOT EXISTS auth_method       VARCHAR(50),   -- 'bearer' | 'api_key' | 'basic_auth'
    ADD COLUMN IF NOT EXISTS headers_json      TEXT;          -- JSON de headers adicionales

-- Índice para consultas por tipo
CREATE INDEX IF NOT EXISTS idx_credenciales_tipo
    ON saas_credenciales_bd (tipo_conexion);

COMMENT ON COLUMN saas_credenciales_bd.tipo_conexion IS
    'tradicional = SQL/PostgreSQL/MySQL | api = REST/GraphQL';
COMMENT ON COLUMN saas_credenciales_bd.auth_method IS
    'bearer | api_key | basic_auth';
COMMENT ON COLUMN saas_credenciales_bd.headers_json IS
    'Headers HTTP adicionales en formato JSON. Ej: {"X-Tenant": "abc"}';
