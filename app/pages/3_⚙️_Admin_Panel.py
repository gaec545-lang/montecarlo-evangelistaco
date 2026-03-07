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

tab1, tab2, tab3 = st.tabs(["🏢 Clientes", "🤖 YAML Builder", "👥 Usuarios"])

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
                    if boveda_disponible and new_supabase_url and new_supabase_key:
                        conn_mgr.save_client_connection(
                            new_client_id, new_supabase_url, new_supabase_key,
                            st.session_state.username
                        )
                    st.success(f"✅ Cliente '{new_client_name}' creado exitosamente.")
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
    st.markdown("El Agente IA analiza la base de datos del cliente y genera la configuracion matematica completa.")

    client_mgr2 = ClientManager()
    all_clients2 = client_mgr2.get_all_clients()

    if not all_clients2:
        st.warning("No hay clientes registrados. Crea uno en el Tab 1 primero.")
        st.stop()

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

    st.info(f"""
    **Cliente:** {selected_client.name}
    **Industria:** {selected_client.industry}
    **Config actual:** `{selected_client.config_file}`
    """)

    # --- Extraccion de tablas y generacion de YAML ---
    if st.button("🔍 Analizar Base de Datos y Generar Config", type="primary"):
        if not boveda2:
            st.error("La boveda de credenciales no esta disponible (DATABASE_URL requerida).")
            st.stop()

        creds = conn_mgr2.get_client_connection(selected_client_id)
        if not creds:
            st.error("Este cliente no tiene credenciales Supabase. Configuralas en el Tab 1.")
            st.stop()

        schemas = {}

        with st.spinner("Conectando a Supabase del cliente..."):
            try:
                from supabase import create_client
                import json
                from datetime import date

                supabase = create_client(creds['url'], creds['key'])

                # Listar tablas via RPC o fallback manual
                all_tables = []
                try:
                    tables_result = supabase.rpc('get_all_tables').execute()
                    all_tables = [t['table_name'] for t in tables_result.data]
                except Exception:
                    pass

                if all_tables:
                    st.success(f"✅ {len(all_tables)} tablas detectadas automaticamente.")
                else:
                    st.warning("No se pudo listar tablas automaticamente.")
                    table_input = st.text_area(
                        "Introduce las tablas disponibles (una por linea):",
                        placeholder="fact_costos\nfact_ventas\nhistorico_inventario",
                        height=120
                    )
                    if table_input:
                        all_tables = [t.strip() for t in table_input.split('\n') if t.strip()]
                    else:
                        st.stop()

            except Exception as e:
                st.error(f"Error conectando a Supabase: {e}")
                st.stop()

        with st.spinner(f"Extrayendo esquema de {len(all_tables)} tablas..."):
            progress = st.progress(0)
            for idx, table in enumerate(all_tables):
                try:
                    result = supabase.table(table).select("*").limit(100).execute()
                    if result.data:
                        df = pd.DataFrame(result.data)
                        schemas[table] = {
                            'columns': df.columns.tolist(),
                            'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
                            'sample_rows': len(result.data),
                            'sample_data': df.head(3).to_dict('records')
                        }
                except Exception as e:
                    st.warning(f"No se pudo acceder a `{table}`: {str(e)[:80]}")
                progress.progress((idx + 1) / len(all_tables))

        if not schemas:
            st.error("No se pudo extraer datos de ninguna tabla.")
            st.stop()

        st.success(f"✅ Esquemas extraidos de {len(schemas)} tablas.")

        with st.spinner("Llama 3.3 analizando vectores de riesgo..."):
            from src.ai_agent import AIFinancialAgent
            from datetime import date

            ai_prompt = f"""
Industria del cliente: {selected_client.industry}
Cliente ID: {selected_client_id}
Nombre: {selected_client.name}

Esquema completo de la base de datos:
{json.dumps(schemas, indent=2, ensure_ascii=False)}

TAREA: Genera un archivo YAML de configuracion para el sistema Sentinel de Decision Intelligence.

El YAML debe tener esta estructura exacta (respeta los nombres de claves):

client:
  id: "{selected_client_id}"
  name: "{selected_client.name}"
  industry: "{selected_client.industry}"

simulation:
  iterations: 10000

variables:
  nombre_variable_1:
    description: "Descripcion clara"
    distribution: "normal"
    params:
      mean: 0.0
      std: 0.0

  nombre_variable_2:
    description: "..."
    distribution: "triangular"
    params:
      min: 0.0
      mode: 0.0
      max: 0.0

business_model: |
  def modelo_{selected_client.industry.replace('-', '_').replace(' ', '_')}(variables, config):
      resultado = 0.0
      # Combinar variables para calcular resultado financiero
      return resultado

thresholds:
  critical_loss_prob: 0.20
  high_volatility: 0.35
  margin_protection: 0.05

metadata:
  reasoning: "Explicacion de la seleccion de variables"
  generated_by: "Sentinel AI Agent"
  generated_at: "{date.today()}"

IMPORTANTE: Solo YAML puro. Sin markdown. Sin explicaciones adicionales.
"""

            try:
                agent = AIFinancialAgent()
                generated_yaml = agent.generate_config_from_prompt(ai_prompt, selected_client.industry)

                st.success("✅ Configuracion generada por IA.")
                st.subheader("📄 YAML Generado")
                st.code(generated_yaml, language='yaml')

                try:
                    yaml.safe_load(generated_yaml)
                    st.success("✅ YAML valido.")
                except Exception as e:
                    st.error(f"❌ YAML invalido: {e}")

                # Guardar
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    filename = st.text_input(
                        "Nombre del archivo",
                        value=f"{selected_client_id}_config.yaml"
                    )

                # Guardado via session_state para evitar re-run al escribir el text_input
                if 'yaml_to_save' not in st.session_state:
                    st.session_state.yaml_to_save = None
                st.session_state.yaml_to_save = generated_yaml
                st.session_state.yaml_filename = filename
                st.session_state.yaml_client_id = selected_client_id

            except Exception as e:
                st.error(f"Error en el agente IA: {e}")
                import traceback
                with st.expander("Detalle del error"):
                    st.code(traceback.format_exc())

    # Boton de guardado (fuera del bloque condicional para persistir)
    if st.session_state.get('yaml_to_save') and st.session_state.get('yaml_client_id') == selected_client_id:
        if st.button("💾 Guardar Config en Disco", type="primary"):
            output_path = f"configs/clients/{st.session_state.yaml_filename}"
            Path("configs/clients").mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(st.session_state.yaml_to_save)
            client_mgr2.update_client(selected_client_id, config_file=output_path)
            st.success(f"✅ Guardado en `{output_path}`")
            st.session_state.yaml_to_save = None

    st.markdown("---")
    st.subheader("📁 Modelos Financieros Compilados")
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
        st.error(f"Error al leer directorio de clientes: {e}")

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
