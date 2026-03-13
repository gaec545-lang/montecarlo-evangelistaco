AUDITORÍA TÉCNICA COMPLETA de: $ARGUMENTS

## ESCANEO:

### 1. Deuda Técnica
- Funciones >30 líneas sin docstring
- TODOs y FIXMEs sin resolver
- Código duplicado (>10 líneas idénticas en 2+ lugares)
- Imports no utilizados
- Variables/funciones sin type hints

### 2. Seguridad
- Secrets hardcodeados (regex: API keys, tokens, passwords)
- Queries no parametrizadas
- Inputs sin validar
- Endpoints sin autenticación
- Datos sin filtrar por tenant

### 3. Performance
- Queries sin índice (EXPLAIN ANALYZE las top 10 más ejecutadas)
- N+1 queries
- Datos cargados en memoria sin paginación
- Cálculos que podrían cachearse

### 4. Cobertura de Tests
- Módulos sin tests unitarios
- Features sin tests de integración
- Edge cases documentados pero no testeados

## OUTPUT:
Genera un reporte priorizado:
- 🔴 CRÍTICO — Arreglar ahora (seguridad, data leaks)
- 🟡 ALTO — Arreglar esta semana (bugs, performance)
- 🔵 MEDIO — Arreglar este sprint (deuda técnica)
- ⚪ BAJO — Backlog (mejoras cosméticas)

Para los items CRÍTICOS y ALTOS: NO solo reportes. CORRÍGELOS inmediatamente.
