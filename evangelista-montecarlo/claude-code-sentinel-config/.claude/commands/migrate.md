GENERA MIGRACIÓN DE SUPABASE para: $ARGUMENTS

## PROTOCOLO:

### 1. Diseño
- Define las tablas/columnas necesarias
- SIEMPRE incluir: `id UUID DEFAULT gen_random_uuid()`, `organization_id UUID NOT NULL`, `created_at TIMESTAMPTZ DEFAULT now()`, `updated_at TIMESTAMPTZ DEFAULT now()`
- Definir índices para columnas de búsqueda frecuente
- Definir foreign keys con ON DELETE apropiado

### 2. Migración SQL
Genera archivo en `supabase/migrations/[timestamp]_[descripcion].sql`:

```sql
-- Migration: [descripción]
-- Author: Claude Code (autónomo)
-- Date: [fecha]
-- Razón: [por qué se necesita]

BEGIN;

-- Tabla(s)
CREATE TABLE IF NOT EXISTS ...

-- Índices
CREATE INDEX IF NOT EXISTS ...

-- RLS (OBLIGATORIO para tablas con datos de cliente)
ALTER TABLE [tabla] ENABLE ROW LEVEL SECURITY;

CREATE POLICY "[tabla]_tenant_isolation" ON [tabla]
  USING (organization_id = current_setting('app.current_org_id')::uuid);

-- Función de updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_updated_at
  BEFORE UPDATE ON [tabla]
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

COMMIT;
```

### 3. Rollback
Genera también el archivo de rollback: `supabase/migrations/[timestamp]_[descripcion]_rollback.sql`

### 4. Validación
- Verifica que la migración es idempotente (IF NOT EXISTS en todo)
- Verifica que RLS está habilitado
- Verifica que organization_id tiene índice
- Genera test de integración que confirma la migración

⚠️ DETENTE y pídeme aprobación si la migración MODIFICA o ELIMINA columnas/tablas existentes.
Para tablas NUEVAS: ejecuta sin preguntar.
