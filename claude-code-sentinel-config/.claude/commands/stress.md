Ejecuta el PROTOCOLO DE STRESS TEST completo sobre: $ARGUMENTS

## EJECUCIÓN:

### Nivel 1 — Funcional
- Identifica todos los inputs del módulo/feature
- Prueba: happy path, inputs vacíos, inputs extremos, caracteres especiales, concurrencia
- Documenta cada caso probado y resultado

### Nivel 2 — Datos  
- Prueba con 0, 1 y 10,000+ registros
- Ejecuta EXPLAIN ANALYZE en cada query nueva
- Verifica aislamiento multi-tenant
- Detecta N+1 queries

### Nivel 3 — Seguridad
- Escanea secrets hardcodeados
- Prueba SQL injection en todos los inputs
- Verifica que RLS funciona entre tenants
- Verifica permisos por rol

### Nivel 4 — Resiliencia
- Simula timeout de Supabase
- Simula restart del container
- Verifica idempotencia
- Prueba refresh a mitad de proceso

## OUTPUT:
Genera el Stress Test Report formateado según Sección 3 del CLAUDE.md.
Si algo FALLA: corrígelo inmediatamente y re-testea. No solo reportes — ARREGLA.
