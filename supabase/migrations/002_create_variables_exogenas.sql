-- ============================================================
-- MIGRACIÓN 002: Variables Exógenas Macroeconómicas
-- Evangelista & Co. | Sentinel Decision Intelligence V2
-- ============================================================
-- Tabla GLOBAL de Evangelista (NO por cliente).
-- Fuentes: BANXICO, INEGI, CNBV.
-- Ejecutar en Supabase SQL Editor.
-- ============================================================

CREATE TABLE IF NOT EXISTS saas_variables_exogenas (
    id        UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
    variable  VARCHAR(50)  NOT NULL,   -- 'TIIE', 'USD_MXN', 'INPC', 'CETES_28'
    fecha     DATE         NOT NULL,
    valor     NUMERIC(14, 6) NOT NULL,
    fuente    VARCHAR(100),            -- 'BANXICO', 'INEGI'
    serie_id  VARCHAR(20),             -- ID de serie en API de origen (ej: 'SF43718')
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (variable, fecha)
);

-- Índices para consultas por variable y rango de fechas
CREATE INDEX IF NOT EXISTS idx_saas_var_exog_variable ON saas_variables_exogenas (variable);
CREATE INDEX IF NOT EXISTS idx_saas_var_exog_fecha    ON saas_variables_exogenas (fecha DESC);

-- NO necesita RLS (es data pública macro)

COMMENT ON TABLE saas_variables_exogenas IS
    'Variables macroeconómicas para el Escudo 1 (Radar) y Escudo 2 (Trituradora). '
    'Actualizar periódicamente con scripts/load_banxico_data.py.';

COMMENT ON COLUMN saas_variables_exogenas.variable IS
    'TIIE | USD_MXN | INPC | CETES_28 | IGAE | etc.';

COMMENT ON COLUMN saas_variables_exogenas.serie_id IS
    'ID de la serie en la API de origen. BANXICO: SF43718 = TIIE 28d, etc.';
