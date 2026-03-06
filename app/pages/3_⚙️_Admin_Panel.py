import streamlit as st
import yaml
import os
import sys
from sqlalchemy import create_engine
import pandas as pd

# Conectar con el backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.connection_manager import ConnectionManager

st.set_page_config(page_title="Admin Panel", page_icon="⚙️", layout="wide")

# Ocultar menú nativo y forzar alto contraste en el panel lateral
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none !important;}
        
        /* INYECCIÓN DE ALTO CONTRASTE PARA EL PANEL LATERAL */
        [data-testid="stSidebar"] p, 
        [data-testid="stSidebar"] span, 
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] div { 
            color: #FFFFFF !important; 
        }

        /* CORRECCIÓN DE CAJAS DE TEXTO (Forzar Blanco y Texto Oscuro) */
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

# Verificación estricta de seguridad
if not st.session_state.get('authenticated'):
    st.error("🔒 Acceso denegado. Inicia sesión en el portal principal.")
    st.stop()

if st.session_state.role not in ["Admin", "Consultor"]:
    st.error("🚫 Tu rol no tiene privilegios para acceder a este panel operativo.")
    st.stop()

st.markdown("<h1>⚙️ Panel de Administración</h1>", unsafe_allow_html=True)
st.markdown("---")

tabs = st.tabs(["🔌 Quick Connect (Ingesta)", "📋 YAML Builder", "👥 Usuarios"])

# ═══════════════════════════════════════════════════════════════
# TAB 1: QUICK CONNECT (MODO API)
# ═══════════════════════════════════════════════════════════════
with tabs[0]:
    st.subheader("⚡ Quick Connect: Ingesta Segura (API)")
    st.markdown("Vincula la base de datos Supabase del cliente sin riesgo de bloqueos de red.")
    with st.form("quick_connect_form"):
        c_id = st.text_input("ID del Cliente (ej. hotel_quinta)")
        c_url = st.text_input("URL del Proyecto", placeholder="https://xyz...supabase.co")
        c_key = st.text_input("API Key (service_role)", type="password", placeholder="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
        
        if st.form_submit_button("Validar y Guardar Conexión API", use_container_width=True):
            if not c_id or not c_url or not c_key:
                st.error("❌ Campos incompletos.")
            elif not c_url.startswith("http"):
                st.error("❌ La URL debe comenzar con https://")
            else:
                try:
                    # Prueba de fuego: Validamos la estructura del cliente Supabase
                    from supabase import create_client, Client
                    test_client: Client = create_client(c_url, c_key)
                    
                    # Guardamos la dupla (URL + KEY) encriptada
                    conn_manager = ConnectionManager()
                    conn_manager.save_api_connection(client_id=c_id, project_url=c_url, api_key=c_key, username=st.session_state.username)
                    st.success(f"✅ Llave de grado 'service_role' blindada en producción para '{c_id}'.")
                except Exception as e:
                    st.error(f"❌ Fallo al instanciar el cliente o guardar credenciales: {e}")
                    
    st.markdown("---")
    st.subheader("🗄️ Conexiones Activas (Bóveda)")
    try:
        conn_mgr = ConnectionManager()
        conns = conn_mgr.get_all_connections()
        if conns:
            st.dataframe(pd.DataFrame(conns), use_container_width=True, hide_index=True)
        else:
            st.info("No hay conexiones registradas en la bóveda central.")
    except Exception as e:
        st.warning(f"Bóveda no inicializada o inaccesible: {e}")
# ═══════════════════════════════════════════════════════════════
# TAB 2: YAML BUILDER (POTENCIADO POR IA - GROQ)
# ═══════════════════════════════════════════════════════════════
with tabs[1]:
    st.subheader("🤖 YAML Builder: Auditoría Forense Autónoma")
    st.markdown("Deja que el Socio Cuantitativo (Llama 3) analice la base de datos y escriba la matemática del riesgo.")
    
    with st.form("ai_yaml_builder_form"):
        col1, col2 = st.columns(2)
        with col1:
            client_id = st.text_input("ID Único del Cliente", placeholder="ej. cibrian_arquitectos")
            client_name = st.text_input("Nombre Comercial")
            target_table = st.text_input("Tabla a Auditar en Supabase", placeholder="ej. fact_proyectos")
        with col2:
            industry = st.selectbox("Sector", ["Construcción", "Retail", "Alimentos", "Textil", "Logística"])
            simulations = st.number_input("Iteraciones Monte Carlo", min_value=1000, value=10000, step=1000)
            t_loss = st.slider("Umbral Crítico de Probabilidad de Pérdida (%)", 1, 100, 20) / 100.0

        if st.form_submit_button("🧠 Extraer Columnas y Autogenerar Modelo (IA)", use_container_width=True):
            if not client_id or not target_table:
                st.error("❌ ID del Cliente y Tabla son obligatorios para conectar con Supabase.")
            else:
                try:
                    with st.spinner("1️⃣ Conectando a Bóveda y extrayendo esquema de Supabase..."):
                        # 1. Recuperamos credenciales y extraemos datos
                        conn_manager = ConnectionManager()
                        creds = conn_manager.get_api_connection(client_id)
                        
                        from src.data_extraction_engine import DataExtractionEngine
                        # Creamos un config temporal solo para inicializar el extractor
                        temp_config = {"client": {"id": client_id}} 
                        extractor = DataExtractionEngine(creds, temp_config)
                        
                        df = extractor.extract_data(target_table)
                        columnas_disponibles = df.columns.tolist()
                        st.success(f"Esquema extraído: {len(columnas_disponibles)} columnas detectadas.")

                    with st.spinner("2️⃣ Llama 3 analizando vectores de riesgo y escribiendo Python..."):
                        # 2. Despertamos al Agente IA
                        from src.ai_agent import AIFinancialAgent
                        agent = AIFinancialAgent()
                        ai_decision = agent.analyze_schema_and_build_model(industry, columnas_disponibles)
                        
                        # 3. Construimos el YAML definitivo con la mente de la IA
                        config_dict = {
                            "client": {
                                "id": client_id,
                                "name": client_name, 
                                "industry": industry.lower()
                            },
                            "simulation": {"iterations": simulations},
                            "variables": {
                                ai_decision["variable_riesgo"]: {
                                    "distribution": ai_decision["distribucion"], 
                                    "params": {
                                        "mean": ai_decision["media"], 
                                        "std_dev": ai_decision["desviacion"]
                                    }
                                }
                            },
                            "thresholds": {"critical_loss_prob": t_loss},
                            "business_parameters": {
                                "presupuesto_base": ai_decision["presupuesto_base"]
                            },
                            "business_model": ai_decision["python_code"]
                        }
                        
                        # 4. Guardamos en el disco
                        os.makedirs(os.path.join("configs", "clients"), exist_ok=True)
                        file_path = os.path.join("configs", "clients", f"{client_id}_config.yaml")
                        with open(file_path, 'w', encoding='utf-8') as f:
                            yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
                        
                        st.success(f"✅ Arquitectura matemática completada. Archivo blindado en: `{file_path}`")
                        
                        # Mostramos el razonamiento del CFO Autónomo
                        with st.expander("👁️ Ver Razonamiento del CFO (Chain of Thought)", expanded=True):
                            st.info(ai_decision.get("_razonamiento_cuantitativo", "Análisis completado sin comentarios adicionales."))
                            st.code(ai_decision["python_code"], language="python")

                except Exception as e:
                    st.error(f"❌ Fallo en la matriz de ejecución: {e}")

    st.markdown("---")
    st.subheader("📁 Modelos Financieros Compilados")
    try:
        os.makedirs('configs/clients', exist_ok=True)
        client_files = [f for f in os.listdir('configs/clients') if f.endswith('.yaml')]
        yaml_data = []
        for f in client_files:
            with open(os.path.join('configs/clients', f), 'r') as file:
                data = yaml.safe_load(file)
                yaml_data.append({
                    "Archivo": f,
                    "Client ID": data.get('client', {}).get('id', 'N/A'),
                    "Sector": data.get('client', {}).get('industry', 'N/A'),
                    "Variable Riesgo": list(data.get('variables', {}).keys())[0] if data.get('variables') else 'N/A'
                })
        if yaml_data:
            st.dataframe(pd.DataFrame(yaml_data), use_container_width=True, hide_index=True)
        else:
            st.info("No hay modelos parametrizados en el directorio.")
    except Exception as e:
        st.error(f"Error al leer el directorio de clientes: {e}")
# ═══════════════════════════════════════════════════════════════
# TAB 3: USUARIOS
# ═══════════════════════════════════════════════════════════════
with tabs[2]:
    st.subheader("👥 Alta de Clientes y Ejecutivos")
    st.markdown("Asigna credenciales a tus clientes y vincúlalos a sus modelos financieros.")
    
    with st.form("create_user_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_username = st.text_input("Usuario (ej. director_hotel)")
            new_password = st.text_input("Contraseña", type="password", help="Mínimo 8 caracteres, 1 mayúscula, 1 minúscula, 1 número")
            new_name = st.text_input("Nombre Completo")
        with col2:
            new_email = st.text_input("Correo Corporativo")
            new_role = st.selectbox("Rol", ["Ejecutivo", "Consultor"])
            new_client_id = st.text_input("ID de Cliente (Debe coincidir con el YAML Builder)", placeholder="ej. la_quinta_alhondiga")
        
        if st.form_submit_button("🛡️ Crear Cuenta Segura", use_container_width=True):
            if not new_username or not new_password or not new_name:
                st.error("Campos básicos incompletos.")
            elif new_role == "Ejecutivo" and not new_client_id:
                st.error("❌ CRÍTICO: Un Ejecutivo necesita estar atado a un ID de Cliente para ver su Dashboard.")
            else:
                from src.user_manager import UserManager
                try:
                    um = UserManager()
                    cid = new_client_id if new_role == "Ejecutivo" else None
                    success = um.create_user(new_username, new_password, new_role, new_name, new_email, st.session_state.username, cid)
                    if success:
                        st.success(f"✅ Ejecutivo '{new_name}' autorizado. Modelo anclado: {cid}")
                    else:
                        st.error("❌ El usuario ya existe en la bóveda.")
                except ValueError as ve:
                    st.error(f"❌ {ve}")
    
    st.markdown("---")
    st.subheader("🗃️ Directorio y Control de Accesos")
    from src.user_manager import UserManager
    um = UserManager()
    users = um.get_all_users()
    
    if users:
        df_users = pd.DataFrame(users)
        
        # --- ESCUDO DE INMUNIDAD PARA DATOS LEGACY ---
        expected_cols = ['username', 'nombre_completo', 'role', 'client_id', 'is_active', 'created_at']
        for col in expected_cols:
            if col not in df_users.columns:
                df_users[col] = "N/A"
                
        df_visual = df_users[expected_cols].copy()
        
        # Formateo seguro para booleanos y textos nulos
        df_visual['is_active'] = df_visual['is_active'].apply(
            lambda x: "🟢 Activo" if x is True else ("🔴 Bloqueado" if x is False else "⚠️ Indefinido")
        )
        
        st.dataframe(df_visual, use_container_width=True, hide_index=True)
        
        st.markdown("**⚡ Acciones Ejecutivas**")
        col_act1, col_act2 = st.columns(2)
        with col_act1:
            user_to_toggle = st.selectbox("Seleccionar usuario para Bloquear/Desbloquear:", [u['username'] for u in users if u['username'] != st.session_state.username])
            if st.button("🔄 Cambiar Status (Switch)"):
                new_status = um.toggle_user_status(user_to_toggle)
                st.success(f"✅ Status actualizado.")
                st.rerun()
        with col_act2:
            user_to_delete = st.selectbox("Seleccionar usuario a Eliminar:", [u['username'] for u in users if u['username'] != st.session_state.username])
            if st.button("🗑️ Eliminar Definitivamente"):
                um.delete_user(user_to_delete)
                st.success(f"✅ Usuario {user_to_delete} purgado del sistema.")
                st.rerun()
