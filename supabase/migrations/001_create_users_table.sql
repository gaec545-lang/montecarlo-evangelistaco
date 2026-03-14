-- ============================================================
-- MIGRACIÓN 001: Tabla de usuarios de Sentinel
-- Evangelista & Co. | Decision Intelligence SaaS
-- ============================================================
-- Ejecutar en Supabase SQL Editor (una sola vez)
-- ============================================================

-- Crear la tabla de usuarios del sistema
CREATE TABLE IF NOT EXISTS saas_users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username        VARCHAR(50)  UNIQUE NOT NULL,
    password_hash   TEXT         NOT NULL,
    role            VARCHAR(20)  NOT NULL,      -- 'Admin', 'Consultor', 'Ejecutivo'
    nombre_completo VARCHAR(100) NOT NULL,
    email           VARCHAR(100) UNIQUE NOT NULL,
    client_id       TEXT,                        -- ID del cliente asignado (solo Ejecutivos)
    is_active       BOOLEAN      DEFAULT TRUE,
    failed_attempts INT          DEFAULT 0,
    locked_until    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ  DEFAULT NOW(),
    created_by      TEXT,
    last_login      TIMESTAMPTZ
);

-- Índice para búsquedas por username (login frecuente)
CREATE INDEX IF NOT EXISTS idx_saas_users_username ON saas_users (username);

-- Índice para filtrar por client_id (aislamiento multi-tenant)
CREATE INDEX IF NOT EXISTS idx_saas_users_client_id ON saas_users (client_id);

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================

ALTER TABLE saas_users ENABLE ROW LEVEL SECURITY;

-- Admin y Consultores ven todos los usuarios.
-- Ejecutivos solo ven su propio perfil.
CREATE POLICY "users_tenant_isolation" ON saas_users
    USING (
        (role IN ('Admin', 'Consultor'))
        OR (username = current_setting('app.current_user', TRUE))
    );

-- ============================================================
-- COMENTARIOS
-- ============================================================

COMMENT ON TABLE saas_users IS 'Usuarios del SaaS Sentinel. Migrado desde configs/users.yaml en 2026-03.';
COMMENT ON COLUMN saas_users.role IS 'Admin | Consultor | Ejecutivo';
COMMENT ON COLUMN saas_users.client_id IS 'Solo para Ejecutivos: ID del cliente al que pertenecen.';
COMMENT ON COLUMN saas_users.failed_attempts IS 'Intentos fallidos consecutivos. Se resetea en login exitoso.';
COMMENT ON COLUMN saas_users.locked_until IS 'Cuenta bloqueada hasta esta fecha. NULL = no bloqueada.';
