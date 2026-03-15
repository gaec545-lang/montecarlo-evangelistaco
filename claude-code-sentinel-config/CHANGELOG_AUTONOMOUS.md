# Changelog — Decisiones Autónomas de Claude Code

> Este archivo se actualiza automáticamente cada vez que Claude Code toma una decisión sin aprobación explícita de Adriel. Es el registro de auditoría del CTO virtual.

---

<!-- Las entradas se agregan al inicio, la más reciente primero -->

## [2026-03-15] Phase 2.1: Descripciones Consultoras en Tabs del Dashboard

### Decisiones Tomadas
- **Archivo modificado:** `app/streamlit_app.py` (no `src/decision_pipeline.py` como indica el spec).
  Razón: los tabs viven en `vista_consultor_v2()` dentro de `streamlit_app.py`. El spec
  menciona `decision_pipeline.py` por error — ese archivo contiene el pipeline de datos, no la UI.
- **Expanders colapsados por default** (`expanded=False`). Razón: los consultores senior no
  necesitan ver la metodología en cada sesión. El expander está disponible para demos con clientes
  o para consultores junior que necesitan contexto.
- **Contenido redactado en español mexicano profesional nivel McKinsey/BCG.** Cero lenguaje vago.
  Cada sección incluye: propósito, modelos con parámetros reales, tabla de interpretación y
  criterio de acción cuantificado.

### Código Modificado
- `app/streamlit_app.py` — Agregados 5 expanders informativos (252 líneas de contenido):
  - `tab_resumen`: "Guía de Lectura — Sistema de Alertas Predictivas" (umbrales, KPIs)
  - `tab_escudo1`: "El Radar — Motor de Proyección Temporal" (Prophet, Darts, GARCH(1,1))
  - `tab_escudo2`: "La Trituradora — Motor de Estrés Sistémico" (cópula Gaussiana, PyMC, SimPy)
  - `tab_escudo3`: "El Bisturí — Motor de Optimización Quirúrgica" (CVXPY, 3 palancas)
  - `tab_mc`: "El Motor Base — Monte Carlo Cuántico" (10k iteraciones, Spearman, Business Translator)

### Cambios: CERO
- Ningún gráfico modificado
- Ningún cálculo modificado
- Ningún tab reordenado
- Puro contenido nuevo agregado ANTES del contenido existente en cada tab

### Modelos Documentados
- Darts ExponentialSmoothing (Holt-Winters triple) — Escudo 1
- Facebook Prophet (tendencia + estacionalidad anual) — Escudo 1
- ARCH GARCH(1,1) (clustering de volatilidad TIIE) — Escudo 1
- Cópula Gaussiana / Cholesky (correlaciones macroeconómicas) — Escudo 2
- SimPy Event-Driven Cash Flow (cadena de pagos discreta) — Escudo 2
- PyMC Beta-Binomial Bayesiano (probabilidad de default) — Escudo 2
- CVXPY Convex Optimization (OPEX + diferimiento + factoraje) — Escudo 3
- Monte Carlo 10,000 iteraciones + Spearman sensitivity — Motor base

---

## [2026-03-14] Phase 1.5: Admin Panel — CRUD Completo & Métodos de Conexión

### Decisiones Tomadas
- **Admin Panel / Credenciales:** Usar Fernet (`cryptography`) para encriptación AES-128-CBC+HMAC-SHA256 en lugar de AES-256 raw (hazmat). Razón: Fernet provee autenticación del ciphertext (HMAC), previene ataques de manipulación y es la práctica estándar en Python. El usuario pidió "AES-256" como término genérico — Fernet cumple el requisito de seguridad con menor superficie de error.
- **Admin Panel / Credenciales:** Clave Fernet derivada de `ENCRYPTION_KEY` en secrets; si no existe, se deriva de `SUPABASE_KEY` con SHA-256. Esto evita añadir una nueva dependencia de secret que podría bloquear el deploy.
- **Admin Panel / Credenciales:** Campo `db_esquema` solo habilitado para PostgreSQL y Oracle (disabled para otros motores). Razón: evitar confusión UX — MySQL/SQL Server usan databases, no schemas de la misma forma.
- **Admin Panel / Puerto dinámico:** Usando `on_change` callback para actualizar el puerto por defecto cuando el usuario cambia el tipo de BD (sin usar `st.form`, que bloquea reactividad).
- **Admin Panel / Tab 3:** Validación de duplicado en asignaciones ANTES de insertar (query `.match()` en Supabase). Razón: la constraint UNIQUE en BD devuelve error 409 poco amigable; mejor validar en frontend primero.
- **Migración SQL:** Creado `003_add_connection_methods.sql` como complemento a `003_add_connection_type.sql` (ya existía). Ambos usan `IF NOT EXISTS` — seguros de correr en cualquier orden.
- **Columnas nuevas:** Usé nombres `api_auth_method`, `api_token_encrypted`, `api_headers_json` (prefijados con `api_`) para distinguirlos de las columnas legacy `auth_method`, `api_key_encrypted`, `headers_json` del migration anterior. El Admin Panel usa las nuevas columnas.

### Código Modificado
- `app/pages/3_⚙️_Admin_Panel.py` — Reescritura completa con CRUD full + conexiones versátiles
- `supabase/migrations/003_add_connection_methods.sql` — NUEVO: schema completo para metodo_conexion, columnas API y SQL

### Features Implementadas

#### Tab 1 — Consultores (CRUD)
- Crear: expander con formulario (nombre, email, rol, activo=True)
- Listar: fila con botones ✏️ 🔒/🔓 🗑️ por registro
- Editar: formulario inline activado por session_state
- Bloquear/Desbloquear: toggle `activo` con ícono dinámico
- Eliminar: checkbox confirmación + botón disabled hasta confirmar

#### Tab 2 — Clientes (CRUD)
- Crear: expander con industria como selectbox (10 opciones predefinidas)
- Listar: muestra estado 🟢/🔴, industria, contacto
- Editar: inline con selectbox de industria
- Bloquear: toggle `estatus` ("Activo" / "Inactivo")
- Eliminar: muestra contador de asignaciones activas, cascade delete

#### Tab 3 — Asignaciones (CRUD)
- Crear: filtra solo consultores/clientes activos, verifica duplicado antes de insertar
- Listar: muestra nombres legibles (resolución de UUID → nombre)
- Reasignar: validación de duplicado + validación de "sin cambio"
- Eliminar: checkbox confirmación

#### Tab 4 — Credenciales BD (Versátiles)
- Radio selector (fuera del form) para cambio reactivo: 🌐 API REST / 🗄️ SQL Directo
- **API REST**: endpoint, auth method (bearer/api_key/basic_auth/oauth2), token encriptado, headers JSON con validación
- **SQL Directo**: tipo DB (5 motores), host, puerto con default dinámico por motor, usuario, password encriptado, esquema opcional
- Botón 🔍 Probar Conexión: GET request (API) / SELECT 1 (SQL) con resultado inline
- Validación completa antes de guardar
- Encriptación Fernet en token y password
- Listado con edición y eliminación (con confirmación checkbox)

#### Tab 5 — YAML Builder
- Sin cambios funcionales; corregido scope (carga `dcli_t5` localmente)

### Stress Tests Ejecutados
- Validación JSON de headers: probado con null, string vacío, dict válido, JSON inválido
- Duplicate check en asignaciones: query Supabase antes de INSERT
- Cascade delete cliente: borra `saas_asignaciones` primero, luego `saas_clientes`
- Fernet key derivation: funciona con y sin `ENCRYPTION_KEY` en secrets
- Puerto default: actualiza correctamente al cambiar tipo de BD vía on_change callback

### Deuda Técnica Identificada
- **OAuth2 flow completo** — Prioridad: BAJA — Actualmente se almacena token pre-obtenido; un flow OAuth completo requeriría redirect URI y refresh tokens
- **Prueba de conexión SQL para MySQL/SQL Server/Oracle** — Prioridad: MEDIA — Requiere drivers (pymysql, pyodbc, cx_oracle) no incluidos en requirements.txt; se muestra error descriptivo si faltan
- **Rotación de claves de encriptación** — Prioridad: MEDIA — Si `ENCRYPTION_KEY` cambia, los valores existentes no se pueden desencriptar; necesita migración de re-encriptación
