import streamlit as st
import yaml
import os
import sys
import pandas as pd
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.connection_manager import ConnectionManager
from src.client_manager import ClientManager
from src.user_manager import UserManager

st.set_page_config(page_title="Admin Panel", page_icon="⚙️", layout="wide")

st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none !important;}
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] div {
            color: #FFFFFF !important;
        }
        div[data-baseweb="base-input"],
        div[data-baseweb="select"] > div {
            background-color: #FFFFFF !important;
            border: 1px solid #D4AF37 !important;
            border-radius: 4px;
        }
        div[data-baseweb="base-input"] input,
        div[data-baseweb="select"] div {
            color: #1A1A2E !important;
            -webkit-text-fill-color: #1A1A2E !important;
        }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.page_link("streamlit_app.py", label="⬅️ Volver al Dashboard Master")

# Verificacion de seguridad
if not st.session_state.get('authenticated'):
    st.error("🔒 Acceso denegado. Inicia sesion en el portal principal.")
    st.stop()

if st.session_state.role not in ["Admin", "Consultor"]:
    st.error("🚫 Tu rol no tiene privilegios para acceder a este panel operativo.")
    st.stop()

st.markdown("<h1>⚙️ Panel de Administracion</h1>", unsafe_allow_html=True)
st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["🏢 Clientes", "🤖 YAML Builder", "👥 Usuarios", "📋 Audit Log"])

# ═══════════════════════════════════════════════════════════════
# TAB 1: GESTIÓN DE CLIENTES
# ═══════════════════════════════════════════════════════════════
with tab1:
    st.header("🏢 Gestion de Clientes")

    client_mgr = ClientManager()

    try:
        conn_mgr = ConnectionManager()
        boveda_disponible = True
    except Exception:
        boveda_disponible = False
        st.warning("⚠️ Boveda de credenciales no disponible (DATABASE_URL no configurada). Las credenciales Supabase no se podran guardar.")

    # --- Agregar Nuevo Cliente ---
    st.subheader("➕ Agregar Nuevo Cliente")

    with st.form("add_client_form"):
        col1, col2 = st.columns(2)

        with col1:
            new_client_id = st.text_input(
                "Client ID (slug unico)",
                placeholder="textiles_atoyac",
                help="Sin espacios, solo minusculas y guiones bajos"
            )
            new_client_name = st.text_input("Nombre del Cliente", placeholder="Textiles Atoyac SA")
            new_client_industry = st.selectbox(
                "Industria",
                ["alimentos", "textil", "construccion", "retail", "logistica",
                 "manufactura", "servicios", "otro"]
            )

        with col2:
            new_supabase_url = st.text_input(
                "Supabase Project URL",
                placeholder="https://xxxxx.supabase.co",
                type="password"
            )
            new_supabase_key = st.text_input(
                "Supabase API Key (service_role)",
                placeholder="eyJ...",
                type="password"
            )

        submit_client = st.form_submit_button("💾 Crear Cliente")

        if submit_client:
            if not new_client_id or not new_client_name:
                st.error("Client ID y Nombre son obligatorios.")
            elif not new_client_id.replace('_', '').isalnum():
                st.error("Client ID solo puede contener letras, numeros y guiones bajos.")
            else:
                if client_mgr.add_client(new_client_id, new_client_name, new_client_industry):
                    st.success(f"✅ Cliente '{new_client_name}' registrado")

                    if boveda_disponible and new_supabase_url and new_supabase_key:
                        st.info("💾 Guardando credenciales en bóveda...")
                        try:
                            save_result = conn_mgr.save_client_connection(
                                new_client_id, new_supabase_url, new_supabase_key,
                                st.session_state.username
                            )
                            if save_result:
                                st.success("✅ Credenciales guardadas")
                                st.info("🔍 Validando persistencia...")
                                test_creds = conn_mgr.get_client_connection(new_client_id)
                                if test_creds:
                                    st.success("✅ Credenciales verificadas y recuperables")
                                    with st.expander("🔍 Ver detalles (parcial)"):
                                        st.write(f"**URL guardada:** `{test_creds['url'][:50]}...`")
                                        st.write(f"**API Key guardada:** `{test_creds['key'][:30]}...`")
                                        checks = []
                                        if test_creds['url'].startswith('https://'):
                                            checks.append("✅ URL formato HTTPS")
                                        else:
                                            checks.append("⚠️ URL no tiene HTTPS")
                                        if 'supabase.co' in test_creds['url']:
                                            checks.append("✅ URL es de Supabase")
                                        else:
                                            checks.append("⚠️ URL no parece ser de Supabase")
                                        if test_creds['key'].startswith('eyJ'):
                                            checks.append("✅ API Key formato JWT")
                                        else:
                                            checks.append("⚠️ API Key no es JWT")
                                        for check in checks:
                                            st.write(check)
                                    with st.expander("📋 Paso opcional: Habilitar auto-discovery de tablas"):
                                        st.info("Ejecutar este SQL una sola vez en el proyecto Supabase del cliente:")
                                        st.code("""CREATE OR REPLACE FUNCTION get_user_tables()
RETURNS TABLE(table_name text, column_count bigint)
LANGUAGE sql SECURITY DEFINER AS $
  SELECT t.table_name::text, COUNT(c.column_name) as column_count
  FROM information_schema.tables t
  LEFT JOIN information_schema.columns c
    ON t.table_name = c.table_name AND t.table_schema = c.table_schema
  WHERE t.table_schema = 'public' AND t.table_type = 'BASE TABLE'
    AND t.table_name NOT LIKE 'pg_%' AND t.table_name NOT LIKE 'sql_%'
  GROUP BY t.table_name ORDER BY t.table_name;
$;
GRANT EXECUTE ON FUNCTION get_user_tables() TO anon, authenticated;""", language='sql')
                                        st.caption("Opcional. Sin esto el sistema usa detección por prueba directa (más lento).")
                                else:
                                    st.error("❌ PROBLEMA CRÍTICO: Credenciales guardadas pero no recuperables")
                            else:
                                st.error("❌ No se pudieron guardar las credenciales")
                        except Exception as e:
                            st.error(f"❌ Error guardando credenciales: {str(e)[:200]}")
                            import traceback
                            with st.expander("🔍 Ver error técnico"):
                                st.code(traceback.format_exc())

                    st.rerun()
                else:
                    st.error("Ya existe un cliente con ese ID.")

    st.markdown("---")

    # --- Lista de Clientes ---
    st.subheader("📋 Clientes Registrados")

    all_clients = client_mgr.get_all_clients()
    user_mgr = UserManager()

    if not all_clients:
        st.info("No hay clientes registrados. Agrega el primero arriba.")
    else:
        for client in all_clients:
            assigned_consultant = user_mgr.get_consultant_for_client(client.client_id)
            status_emoji = "🟢" if client.status == "active" else ("🟡" if client.status == "inactive" else "🔴")

            with st.expander(f"{status_emoji} **{client.name}** ({client.client_id}) — {client.industry}"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.write(f"**ID:** `{client.client_id}`")
                    st.write(f"**Industria:** {client.industry}")
                    st.write(f"**Estado:** {client.status}")
                    st.write(f"**Creado:** {client.created_at}")
                    st.write(f"**Archivo Config:** `{client.config_file}`")
                    config_exists = Path(client.config_file).exists()
                    if config_exists:
                        st.success("✅ Archivo de config presente")
                    else:
                        st.warning("⚠️ Sin archivo de config. Usa el YAML Builder.")
                    st.write(f"**Consultor asignado:** {assigned_consultant or '⚠️ Sin asignar'}")

                    if boveda_disponible:
                        creds = conn_mgr.get_client_connection(client.client_id)
                        if creds:
                            st.success("✅ Credenciales Supabase configuradas")
                        else:
                            st.warning("⚠️ Sin credenciales Supabase")

                with col2:
                    # Probar conexion
                    if boveda_disponible:
                        if st.button("🔗 Probar Conexion", key=f"test_{client.client_id}"):
                            creds = conn_mgr.get_client_connection(client.client_id)
                            if creds:
                                try:
                                    from supabase import create_client
                                    supabase = create_client(creds['url'], creds['key'])
                                    supabase.table("_sentinel_ping").select("*").limit(1).execute()
                                    st.success("✅ Conexion exitosa")
                                except Exception as e:
                                    msg = str(e)
                                    # Error de tabla inexistente = conexion OK
                                    if "relation" in msg.lower() or "does not exist" in msg.lower() or "404" in msg:
                                        st.success("✅ Conexion exitosa (Supabase responde)")
                                    else:
                                        st.error(f"❌ {msg[:120]}")
                            else:
                                st.error("No hay credenciales guardadas.")

                    # Cambiar estado
                    new_status = st.selectbox(
                        "Estado",
                        ["active", "inactive", "suspended"],
                        index=["active", "inactive", "suspended"].index(client.status),
                        key=f"status_{client.client_id}"
                    )
                    if st.button("💾 Actualizar Estado", key=f"update_{client.client_id}"):
                        client_mgr.update_client(client.client_id, status=new_status)
                        st.success("Estado actualizado.")
                        st.rerun()

                    # Eliminar cliente
                    if st.button("🗑️ Eliminar Cliente", key=f"delete_{client.client_id}"):
                        all_users = user_mgr.get_all_users()
                        users_with_client = [u for u in all_users if u.get('client_id') == client.client_id]
                        if users_with_client:
                            st.error(f"No se puede eliminar: tiene {len(users_with_client)} usuario(s) asignado(s).")
                        else:
                            if boveda_disponible:
                                conn_mgr.delete_client_connection(client.client_id)
                            client_mgr.delete_client(client.client_id)
                            st.warning(f"Cliente '{client.name}' eliminado.")
                            st.rerun()

# ═══════════════════════════════════════════════════════════════
# TAB 2: YAML BUILDER CON IA
# ═══════════════════════════════════════════════════════════════
with tab2:
    st.header("🤖 YAML Builder con IA")

    client_mgr2 = ClientManager()
    all_clients2 = client_mgr2.get_all_clients()

    if not all_clients2:
        st.warning("No hay clientes registrados. Crea uno en el Tab 1 primero.")
    else:
        try:
            conn_mgr2 = ConnectionManager()
            boveda2 = True
        except Exception:
            boveda2 = False

        client_options = {c.client_id: f"{c.name} ({c.client_id})" for c in all_clients2}
        selected_client_id = st.selectbox(
            "Selecciona el cliente a configurar",
            options=list(client_options.keys()),
            format_func=lambda x: client_options[x]
        )
        selected_client = client_mgr2.get_client(selected_client_id)

        st.info(f"**Cliente:** {selected_client.name} | **Industria:** {selected_client.industry}")

        # ── TABLAS POR INDUSTRIA + COMUNES ──────────────────────────────
        _industry_tables = {
            'textil':       ['produccion_textil', 'materia_prima', 'telas', 'rollos'],
            'alimentos':    ['recetas', 'ingredientes', 'lotes', 'caducidad'],
            'construccion': ['proyectos', 'materiales', 'obras', 'contratos'],
            'retail':       ['tiendas', 'pos', 'promociones', 'descuentos'],
            'manufactura':  ['maquinas', 'turnos', 'produccion', 'mantenimiento'],
        }
        _common_tables = [
            'ventas', 'compras', 'inventario', 'productos', 'clientes',
            'gastos', 'ingresos', 'ordenes', 'pedidos', 'facturas',
            'fact_ventas', 'fact_compras', 'fact_inventario', 'fact_produccion', 'fact_costos',
            'historico_ventas', 'historico_precios', 'historico_stock',
            'dim_productos', 'dim_clientes', 'dim_tiempo',
            'venta', 'compra', 'producto', 'cliente', 'factura', 'orden', 'pedido', 'gasto', 'ingreso',
        ]
        _industry = selected_client.industry
        _probe_list = _industry_tables.get(_industry, []) + _common_tables

        # ── FILTRO DE SEGURIDAD ──────────────────────────────────────────
        _SYSTEM_BLACKLIST = {
            'client_connections', 'audit_logs', 'sys_users',
            'auth', 'storage', 'realtime', 'supabase_functions',
            'supabase_migrations', 'pg_stat_statements',
            'schema_migrations', 'ar_internal_metadata', 'information_schema',
        }
        _SYSTEM_PREFIXES = ('pg_', 'sql_', 'supabase_', 'auth.', 'storage.', '_')

        def _is_safe_table(name: str) -> bool:
            n = name.lower()
            return n not in _SYSTEM_BLACKLIST and not any(n.startswith(p) for p in _SYSTEM_PREFIXES)

        # ── AUTO-DETECCIÓN ───────────────────────────────────────────────
        _session_key = f'detected_tables_{selected_client_id}'

        col_auto, col_clear = st.columns([2, 1])
        with col_auto:
            if st.button("🔍 Auto-detectar tablas", help="Conecta a Supabase y detecta tablas automáticamente"):
                if not boveda2:
                    st.error("Bóveda no disponible.")
                else:
                    _creds_auto = conn_mgr2.get_client_connection(selected_client_id)
                    if not _creds_auto:
                        st.error("Sin credenciales Supabase. Configúralas en Tab 1.")
                    else:
                        from supabase import create_client as _create_client
                        _sb = _create_client(_creds_auto['url'], _creds_auto['key'])
                        _detected = []

                        # Método 1: RPC get_user_tables()
                        try:
                            _rpc = _sb.rpc('get_user_tables').execute()
                            if _rpc.data:
                                _detected = [r['table_name'] for r in _rpc.data]
                                st.success(f"✅ {len(_detected)} tablas via RPC")
                        except Exception:
                            pass

                        # Método 2: Prueba directa con lista inteligente
                        if not _detected:
                            if _industry in _industry_tables:
                                st.info(f"🎯 Priorizando tablas de industria: {_industry}")
                            _pb = st.progress(0)
                            _st = st.empty()
                            _mc1, _mc2 = st.columns(2)
                            _found_slot = _mc1.empty()
                            _tested_slot = _mc2.empty()
                            for _i, _tbl in enumerate(_probe_list):
                                _tested_slot.metric("Probadas", f"{_i+1}/{len(_probe_list)}")
                                _found_slot.metric("Encontradas", len(_detected))
                                _st.text(f"Probando: {_tbl}...")
                                try:
                                    _sb.table(_tbl).select("*").limit(1).execute()
                                    _detected.append(_tbl)
                                except Exception:
                                    pass
                                _pb.progress((_i + 1) / len(_probe_list))
                            _st.empty()
                            _pb.empty()

                        # Aplicar filtro de seguridad a tablas detectadas
                        _detected_raw = _detected
                        _detected = [t for t in _detected_raw if _is_safe_table(t)]
                        _filtered = len(_detected_raw) - len(_detected)
                        if _filtered > 0:
                            st.info(f"🔒 {_filtered} tablas del sistema excluidas por seguridad")

                        if _detected:
                            st.session_state[_session_key] = '\n'.join(_detected)
                            st.success(f"✅ {len(_detected)} tablas detectadas")
                        else:
                            st.warning("No se detectaron tablas. Introdúcelas manualmente.")
                        st.rerun()
        with col_clear:
            if st.button("🗑️ Limpiar", help="Limpiar lista de tablas"):
                st.session_state.pop(_session_key, None)
                st.rerun()

        # ── INPUT DE TABLAS (manual o pre-llenado por auto-detección) ────
        if _session_key not in st.session_state:
            st.session_state[_session_key] = ''

        table_input = st.text_area(
            "Tablas disponibles (una por linea)",
            key=_session_key,
            placeholder="ventas\ncompras\ninventario\nproductos\nclientes",
            height=180,
            help="Auto-detectadas o escríbelas manualmente. Ignora tablas de sistema: auth, storage, realtime"
        )

        if not table_input:
            st.warning("Introduce las tablas o usa Auto-detectar.")
        else:
            all_tables_raw = [t.strip() for t in table_input.split('\n') if t.strip()]

            # ── FILTRO DE SEGURIDAD ──────────────────────────────────────
            all_tables = [t for t in all_tables_raw if _is_safe_table(t)]
            _manual_filtered = len(all_tables_raw) - len(all_tables)
            if _manual_filtered > 0:
                st.info(f"🔒 Filtro de seguridad: {_manual_filtered} tablas del sistema excluidas")

            if not all_tables:
                st.error("No hay tablas validas para analizar.")
            else:
                st.success(f"✅ {len(all_tables)} tablas seguras para analizar")
                with st.expander("Ver tablas"):
                    for idx, table in enumerate(all_tables, 1):
                        st.write(f"{idx}. `{table}`")

                # ── BOTÓN PRINCIPAL ──────────────────────────────────────────────
                if st.button("🤖 Generar Configuracion con IA", type="primary"):
                    if not boveda2:
                        st.error("Boveda no disponible (DATABASE_URL requerida).")
                        st.stop()

                    creds = conn_mgr2.get_client_connection(selected_client_id)
                    if not creds:
                        st.error("Cliente sin credenciales Supabase. Configuralas en Tab 1.")
                        st.stop()

                    # Double-check de seguridad antes de enviar a IA
                    unsafe = [t for t in all_tables if not _is_safe_table(t)]
                    if unsafe:
                        st.error(f"🚨 ERROR DE SEGURIDAD: Tablas del sistema detectadas: {unsafe}")
                        st.stop()

                    schemas = {}

                    # ── EXTRACCION LIGERA: solo 3 filas por tabla ────────────────
                    with st.spinner("Conectando a Supabase y extrayendo esquemas..."):
                        try:
                            from supabase import create_client
                            import json

                            supabase = create_client(creds['url'], creds['key'])
                            progress_bar = st.progress(0)
                            status_text = st.empty()

                            for idx, table in enumerate(all_tables):
                                status_text.text(f"Analizando {table}... ({idx + 1}/{len(all_tables)})")
                                try:
                                    result = supabase.table(table).select("*").limit(3).execute()
                                    if result.data:
                                        df = pd.DataFrame(result.data)
                                        schemas[table] = {
                                            'columns': df.columns.tolist(),
                                            'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
                                            'sample_count': len(result.data),
                                            'first_row': result.data[0]
                                        }
                                    else:
                                        st.warning(f"Tabla `{table}` esta vacia.")
                                except Exception as e:
                                    st.warning(f"No se pudo acceder a `{table}`: {str(e)[:100]}")
                                progress_bar.progress((idx + 1) / len(all_tables))

                            status_text.empty()
                            progress_bar.empty()

                        except Exception as e:
                            st.error(f"Error de conexion: {e}")
                            st.stop()

                    if not schemas:
                        st.error("No se pudo extraer datos de ninguna tabla.")
                        st.stop()

                    st.success(f"✅ Esquemas extraidos de {len(schemas)} tablas.")

                    # ── LLAMADA A IA CON PROMPT COMPACTO ────────────────────────
                    with st.spinner("Analizando con IA (30-60 segundos)..."):
                        from src.ai_agent import AIFinancialAgent
                        from datetime import date

                        industry_fn = selected_client.industry.replace('-', '_').replace(' ', '_')

                        ai_prompt = f"""Eres un experto en analisis de riesgo financiero y simulacion Monte Carlo.

CONTEXTO DEL CLIENTE:
- Industria: {selected_client.industry}
- Nombre: {selected_client.name}
- Client ID: {selected_client_id}

ESTRUCTURA DE DATOS DISPONIBLE:
{json.dumps(schemas, indent=2, ensure_ascii=False)}

TAREA: Identifica las 2-4 variables de riesgo MAS CRITICAS para esta industria.

CRITERIOS:
1. Variables con ALTO impacto financiero (revenue o cost drivers)
2. Columnas de fecha/timestamp claramente identificables en el schema
3. Valores numericos con variabilidad significativa
4. Solo tablas y columnas que EXISTEN en el schema proporcionado
5. ESCALA: los params (mean, min, mode, max, std_dev) deben ser TOTALES MENSUALES
   reales del negocio, NO valores por unidad ni multiplicados por volumen
6. El business_model debe operar directamente con esos totales (sin multiplicar por volumen)

Segun la industria {selected_client.industry}, recomienda una metodologia de KPIs:
- okr: Tech, startups, crecimiento acelerado
- bsc: Empresas establecidas, estrategia corporativa
- smart: PyMEs, claridad operativa
- north_star: Product-driven businesses
- operational: Operaciones dia a dia sin framework formal

REGLAS CRITICAS PARA PARAMETROS DE DISTRIBUCIONES:

DISTRIBUCION NORMAL — requiere EXACTAMENTE estos 2 parametros (ambos obligatorios):
  params:
    mean: 50000.0     # Promedio mensual real calculado del schema (NUNCA omitir)
    std_dev: 7500.0   # Desviacion estandar (NUNCA 0, NUNCA omitir; usar 10-20% del mean)

DISTRIBUCION TRIANGULAR — requiere EXACTAMENTE estos 3 parametros (todos obligatorios):
  params:
    min: 35000.0      # Valor mensual minimo observado (NUNCA omitir)
    mode: 50000.0     # Valor mensual mas frecuente (NUNCA omitir, min <= mode <= max)
    max: 70000.0      # Valor mensual maximo observado (NUNCA omitir)

CALCULO DE PARAMETROS DESDE EL SCHEMA:
- Usa los sample_data del schema para estimar valores reales
- Para NORMAL: mean = promedio de los valores; std_dev = 15% del mean
- Para TRIANGULAR: min = valor mas bajo; mode = mediana; max = valor mas alto
- Si el schema no tiene datos: estima valores coherentes con la industria {selected_client.industry}
- NUNCA dejes un param en None, null o vacio

ESTRUCTURA OBLIGATORIA - incluir TODAS estas secciones:
client, variables, business_model, decision_rules, simulation, kpi_methodology, metadata

RETORNA SOLO EL YAML (sin markdown, sin explicaciones):

client:
  id: "{selected_client_id}"
  name: "{selected_client.name}"
  industry: "{selected_client.industry}"

variables:
  nombre_variable_1:
    description: "Descripcion del impacto financiero"
    sql_table: "tabla_exacta_del_schema"
    date_column: "columna_fecha_exacta"
    value_column: "columna_valor_exacta"
    distribution: "normal"
    params:
      mean: 50000.0    # OBLIGATORIO: promedio mensual real
      std_dev: 7500.0  # OBLIGATORIO: nunca 0, tipicamente 10-20% del mean
  nombre_variable_2:
    description: "Descripcion"
    sql_table: "tabla_exacta"
    date_column: "columna_fecha"
    value_column: "columna_valor"
    distribution: "triangular"
    params:
      min: 35000.0     # OBLIGATORIO: minimo mensual observado
      mode: 50000.0    # OBLIGATORIO: valor mas frecuente (min <= mode <= max)
      max: 70000.0     # OBLIGATORIO: maximo mensual observado

business_model: |
  def modelo_{industry_fn}(variables, params):
      # IMPORTANTE: las variables ya representan TOTALES MENSUALES
      # NO multipliques por volumen si las variables son totales
      ingresos_totales = variables.get('nombre_variable_1', 0)
      costos_totales   = variables.get('nombre_variable_2', 0)
      return ingresos_totales - costos_totales

decision_rules:
  - title: "Riesgo alto de perdida detectado"
    condition: "prob_loss > 0.20"
    priority: "Alta"
    actions:
      - "Revisar estructura de costos inmediatamente"
      - "Analizar principales drivers de riesgo"
      - "Implementar controles de contingencia preventivos"
      - "Considerar estrategias de cobertura o hedging"
  - title: "Volatilidad operativa excesiva"
    condition: "cv > 0.30"
    priority: "Media"
    actions:
      - "Evaluar estrategias de diversificacion de riesgo"
      - "Analizar estabilizacion de variables clave"
      - "Considerar contratos de precio fijo con proveedores"
  - title: "Value at Risk significativo"
    condition: "abs(var_95) > abs(expected_value) * 0.25"
    priority: "Alta"
    actions:
      - "Establecer reservas de contingencia adecuadas"
      - "Revisar politicas de gestion de riesgo financiero"

simulation:
  iterations: 10000
  confidence_level: 0.95

kpi_methodology: "operational"  # okr, bsc, smart, north_star, operational

metadata:
  generated_by: "AI Agent v1.0"
  generated_at: "{date.today()}"
  reasoning: "Explicacion breve de por que se seleccionaron estas variables"
"""

                        try:
                            agent = AIFinancialAgent()
                            generated_yaml = agent.generate_config_from_prompt(ai_prompt, selected_client.industry)

                            st.success("✅ Configuracion generada por IA")

                            # ── VALIDACIÓN ROBUSTA DE ESTRUCTURA ─────────────
                            st.info("🔍 Validando estructura del YAML...")
                            try:
                                parsed_yaml = yaml.safe_load(generated_yaml)
                                validations = []

                                for section in ['client', 'variables', 'business_model', 'decision_rules', 'simulation']:
                                    if section in parsed_yaml:
                                        validations.append(f"✅ Seccion '{section}' presente")
                                    else:
                                        validations.append(f"❌ FALTA seccion '{section}'")

                                if 'variables' in parsed_yaml:
                                    for var_name, var_cfg in parsed_yaml['variables'].items():
                                        if var_cfg and var_cfg.get('params'):
                                            validations.append(f"✅ Variable '{var_name}' tiene parametros")
                                        else:
                                            validations.append(f"❌ Variable '{var_name}' SIN parametros")

                                if 'decision_rules' in parsed_yaml:
                                    rule_count = len(parsed_yaml['decision_rules'] or [])
                                    if rule_count >= 2:
                                        validations.append(f"✅ {rule_count} decision_rules definidas")
                                    else:
                                        validations.append(f"⚠️ Solo {rule_count} decision_rule(s), se recomiendan 2+")

                                if parsed_yaml.get('business_model'):
                                    if 'def modelo_' in str(parsed_yaml['business_model']):
                                        validations.append("✅ Business model tiene funcion Python")
                                    else:
                                        validations.append("⚠️ Business model sin 'def modelo_'")

                                with st.expander("🔍 Resultados de Validacion"):
                                    for v in validations:
                                        if '❌' in v:
                                            st.error(v)
                                        elif '⚠️' in v:
                                            st.warning(v)
                                        else:
                                            st.success(v)

                                critical_errors = [v for v in validations if '❌' in v]
                                if critical_errors:
                                    st.error("❌ YAML con errores criticos. Intenta regenerar.")
                                else:
                                    st.success("✅ YAML valido y completo")

                            except yaml.YAMLError as e:
                                st.error(f"❌ YAML mal formado: {e}")

                            st.subheader("📄 YAML Generado")
                            st.code(generated_yaml, language='yaml')

                            # Persistir en session_state para sobrevivir reruns
                            st.session_state['yaml_to_save'] = generated_yaml
                            st.session_state['yaml_client_id'] = selected_client_id
                            st.session_state['yaml_filename'] = f"{selected_client_id}_config.yaml"

                        except Exception as e:
                            st.error(f"Error en IA: {e}")
                            import traceback
                            with st.expander("Ver error completo"):
                                st.code(traceback.format_exc())

        # ── GUARDAR (persiste fuera del bloque del boton) ────────────────
        if (st.session_state.get('yaml_to_save')
                and st.session_state.get('yaml_client_id') == selected_client_id):

            st.markdown("---")
            col_a, col_b = st.columns([3, 1])
            with col_a:
                filename = st.text_input(
                    "Nombre del archivo",
                    value=st.session_state.get('yaml_filename', f"{selected_client_id}_config.yaml")
                )
            with col_b:
                st.write("")
                st.write("")
                if st.button("💾 Guardar en Disco", type="primary"):
                    output_path = f"configs/clients/{filename}"
                    Path("configs/clients").mkdir(parents=True, exist_ok=True)
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(st.session_state['yaml_to_save'])
                    client_mgr2.update_client(selected_client_id, config_file=output_path)
                    st.success(f"✅ Guardado en `{output_path}`")
                    st.balloons()
                    st.session_state.pop('yaml_to_save', None)

        st.markdown("---")
        st.subheader("📁 Modelos Compilados")
        try:
            Path('configs/clients').mkdir(parents=True, exist_ok=True)
            client_files = [f for f in os.listdir('configs/clients') if f.endswith('.yaml')]
            yaml_data = []
            for f in client_files:
                with open(os.path.join('configs/clients', f), 'r') as file:
                    data = yaml.safe_load(file)
                    yaml_data.append({
                        "Archivo": f,
                        "Client ID": data.get('client', {}).get('id', 'N/A'),
                        "Sector": data.get('client', {}).get('industry', 'N/A'),
                        "Variables": ', '.join(list(data.get('variables', {}).keys())) if data.get('variables') else 'N/A'
                    })
            if yaml_data:
                st.dataframe(pd.DataFrame(yaml_data), use_container_width=True, hide_index=True)
            else:
                st.info("No hay modelos parametrizados.")
        except Exception as e:
            st.error(f"Error al leer directorio: {e}")

# ═══════════════════════════════════════════════════════════════
# TAB 3: USUARIOS
# ═══════════════════════════════════════════════════════════════
with tab3:
    st.subheader("👥 Alta de Clientes y Ejecutivos")
    st.markdown("Asigna credenciales a tus clientes y vincudalos a sus modelos financieros.")

    with st.form("create_user_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_username = st.text_input("Usuario (ej. director_hotel)")
            new_password = st.text_input("Contraseña", type="password",
                                         help="Minimo 8 caracteres, 1 mayuscula, 1 minuscula, 1 numero")
            new_name = st.text_input("Nombre Completo")
        with col2:
            new_email = st.text_input("Correo Corporativo")
            new_role = st.selectbox("Rol", ["Ejecutivo", "Consultor"])
            new_client_id = st.text_input(
                "ID de Cliente (para Ejecutivos)",
                placeholder="ej. test_pasteleria",
                help="Debe coincidir con el Client ID registrado"
            )

        if st.form_submit_button("🛡️ Crear Cuenta Segura"):
            if not new_username or not new_password or not new_name:
                st.error("Campos basicos incompletos.")
            elif new_role == "Ejecutivo" and not new_client_id:
                st.error("❌ Un Ejecutivo debe estar vinculado a un Client ID.")
            else:
                um_create = UserManager()
                try:
                    cid = new_client_id if new_role == "Ejecutivo" else None
                    success = um_create.create_user(
                        new_username, new_password, new_role,
                        new_name, new_email, st.session_state.username, cid
                    )
                    if success:
                        st.success(f"✅ Usuario '{new_name}' creado con rol {new_role}.")
                    else:
                        st.error("❌ El usuario ya existe.")
                except ValueError as ve:
                    st.error(f"❌ {ve}")

    st.markdown("---")
    st.subheader("🔗 Asignar Clientes a Consultores")

    um_assign = UserManager()
    all_users_data = um_assign.get_all_users()
    consultores = [u['username'] for u in all_users_data if u.get('role') in ('Consultor', 'Admin')]
    client_mgr_tab3 = ClientManager()
    all_clients_tab3 = client_mgr_tab3.get_all_clients()

    if consultores and all_clients_tab3:
        col_a, col_b = st.columns(2)
        with col_a:
            consultor_sel = st.selectbox("Consultor", consultores, key="assign_consultor")
            client_sel = st.selectbox(
                "Cliente a asignar",
                [c.client_id for c in all_clients_tab3],
                format_func=lambda x: next((c.name for c in all_clients_tab3 if c.client_id == x), x),
                key="assign_client"
            )
            if st.button("➕ Asignar"):
                if um_assign.assign_client_to_consultant(
                        consultor_sel, client_sel, st.session_state.username):
                    st.success(f"✅ '{client_sel}' asignado a '{consultor_sel}'.")
                else:
                    st.error("Esa asignacion ya existe.")

        with col_b:
            consultor_view = st.selectbox("Ver asignaciones de:", consultores, key="view_consultor")
            assigned = um_assign.get_clients_for_consultant(consultor_view)
            if assigned:
                st.write("**Clientes asignados:**")
                for cid in assigned:
                    client_obj = client_mgr_tab3.get_client(cid)
                    name = client_obj.name if client_obj else cid
                    col_x, col_y = st.columns([3, 1])
                    col_x.write(f"• {name} (`{cid}`)")
                    if col_y.button("✖️", key=f"unassign_{consultor_view}_{cid}"):
                        um_assign.unassign_client(consultor_view, cid)
                        st.rerun()
            else:
                st.info("Sin clientes asignados.")
    else:
        st.info("No hay consultores o clientes registrados.")

    st.markdown("---")
    st.subheader("🗃️ Directorio y Control de Accesos")

    um_dir = UserManager()
    users = um_dir.get_all_users()

    if users:
        df_users = pd.DataFrame(users)
        expected_cols = ['username', 'nombre_completo', 'role', 'client_id', 'is_active', 'created_at']
        for col in expected_cols:
            if col not in df_users.columns:
                df_users[col] = "N/A"
        df_visual = df_users[expected_cols].copy()
        df_visual['is_active'] = df_visual['is_active'].apply(
            lambda x: "🟢 Activo" if x is True else ("🔴 Bloqueado" if x is False else "⚠️ Indefinido")
        )
        st.dataframe(df_visual, use_container_width=True, hide_index=True)

        st.markdown("**⚡ Acciones Ejecutivas**")
        col_act1, col_act2 = st.columns(2)
        other_users = [u['username'] for u in users if u['username'] != st.session_state.username]
        with col_act1:
            user_to_toggle = st.selectbox("Bloquear/Desbloquear:", other_users, key="toggle_sel")
            if st.button("🔄 Cambiar Status"):
                um_dir.toggle_user_status(user_to_toggle)
                st.success("Status actualizado.")
                st.rerun()
        with col_act2:
            user_to_delete = st.selectbox("Eliminar usuario:", other_users, key="delete_sel")
            if st.button("🗑️ Eliminar Definitivamente"):
                um_dir.delete_user(user_to_delete)
                st.success(f"Usuario '{user_to_delete}' eliminado.")
                st.rerun()

with tab4:
    st.subheader("📋 Audit Log — Actividad del Sistema")

    from src.audit_logger import read_logs, get_summary_stats, EventType

    # Filtros
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        hours_filter = st.selectbox("Periodo", [6, 24, 48, 168], index=1,
                                    format_func=lambda x: f"Ultimas {x}h" if x < 48 else
                                    ("Ultimas 48h" if x == 48 else "Ultima semana"))
    with col_f2:
        event_options = {
            "Todos": None,
            "Autenticacion": EventType.AUTH_SUCCESS,
            "Login fallido": EventType.AUTH_FAILURE,
            "Pipeline": EventType.PIPELINE_RUN,
            "Error pipeline": EventType.PIPELINE_ERROR,
            "PDF descargado": EventType.PDF_DOWNLOAD,
            "YAML generado": EventType.YAML_GENERATE,
        }
        event_label = st.selectbox("Tipo de evento", list(event_options.keys()))
        event_filter = event_options[event_label]
    with col_f3:
        try:
            all_users_audit = list({e.get('username') for e in read_logs(limit=1000)
                                     if e.get('username')})
        except Exception:
            all_users_audit = []
        user_filter_audit = st.selectbox("Usuario", ["Todos"] + sorted(all_users_audit))
        user_filter_audit = None if user_filter_audit == "Todos" else user_filter_audit
    with col_f4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Refrescar", use_container_width=True):
            st.rerun()

    # Estadisticas resumidas
    summary = get_summary_stats(since_hours=hours_filter)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total eventos", summary['total_events'])
    m2.metric("Logins fallidos", summary['auth_failures'],
              delta=f"-{summary['auth_failures']}" if summary['auth_failures'] else None,
              delta_color="inverse")
    m3.metric("Errores de pipeline", summary['pipeline_errors'],
              delta_color="inverse")
    m4.metric("Duracion promedio", f"{summary['avg_pipeline_ms']:,} ms"
              if summary['avg_pipeline_ms'] else "N/A")

    st.markdown("---")

    # Tabla de logs
    logs = read_logs(
        limit=300,
        event_type=event_filter,
        username=user_filter_audit,
        since_hours=hours_filter,
    )

    if not logs:
        st.info("No hay eventos en el periodo seleccionado.")
    else:
        # Preparar DataFrame
        rows = []
        for e in reversed(logs):  # mas reciente primero
            icon_map = {
                EventType.AUTH_SUCCESS:   "🟢",
                EventType.AUTH_FAILURE:   "🔴",
                EventType.AUTH_LOGOUT:    "🔵",
                EventType.PIPELINE_RUN:   "⚙️",
                EventType.PIPELINE_ERROR: "❌",
                EventType.PDF_DOWNLOAD:   "📄",
                EventType.YAML_GENERATE:  "🤖",
                EventType.ADMIN_ACTION:   "👤",
            }
            ev = e.get('event', '')
            details = e.get('details') or {}
            detail_str = ""
            if ev == EventType.PIPELINE_RUN:
                hs = details.get('health_score')
                ph = details.get('phases_completed', 0)
                detail_str = f"Score: {hs} | Fases: {ph}/5" if hs else f"Fases: {ph}/5"
            elif ev == EventType.PIPELINE_ERROR:
                detail_str = (details.get('error') or '')[:60]
            elif details:
                detail_str = str(details)[:60]

            ts_raw = e.get('ts', '')
            try:
                from datetime import datetime, timezone
                ts_dt = datetime.fromisoformat(ts_raw)
                ts_str = ts_dt.strftime('%d/%m %H:%M:%S')
            except Exception:
                ts_str = ts_raw[:19]

            rows.append({
                '': icon_map.get(ev, '•'),
                'Timestamp': ts_str,
                'Evento': ev,
                'Usuario': e.get('username', ''),
                'Cliente': e.get('client_id', ''),
                'Rol': e.get('role', ''),
                'Duracion': f"{e['duration_ms']} ms" if e.get('duration_ms') else '',
                'Detalle': detail_str,
            })

        df_audit = pd.DataFrame(rows)
        st.dataframe(df_audit, use_container_width=True, hide_index=True,
                     column_config={
                         '': st.column_config.TextColumn(width="small"),
                         'Timestamp': st.column_config.TextColumn(width="small"),
                         'Evento': st.column_config.TextColumn(width="medium"),
                     })
        st.caption(f"Mostrando {len(logs)} eventos recientes.")
