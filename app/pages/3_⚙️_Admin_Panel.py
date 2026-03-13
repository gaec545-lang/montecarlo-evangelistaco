# ==============================================================================
# INYECCIÓN DE ENRUTAMIENTO (Bypass Estructural)
# ==============================================================================
import sys
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '../..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st
import pandas as pd
from supabase import create_client, Client

# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA (Debe ser el primer comando)
# ==============================================================================
st.set_page_config(page_title="Sentinel | Admin", page_icon="⚙️", layout="wide")

# Ocultar nav default y forzar el diseño de alto contraste Evangelista
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none !important;}
        .stButton>button { border: 1px solid #D4AF37; background-color: transparent; }
        .stButton>button:hover { border: 1px solid #1A1A2E; color: #1A1A2E; }
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, 
        [data-testid="stSidebar"] label, [data-testid="stSidebar"] h3, 
        [data-testid="stSidebar"] strong { color: #FFFFFF !important; }
        div[data-baseweb="base-input"], div[data-baseweb="select"] > div {
            background-color: #FFFFFF !important; border: 1px solid #D4AF37 !important; border-radius: 4px;
        }
        div[data-baseweb="base-input"] input, div[data-baseweb="select"] div {
            color: #1A1A2E !important; -webkit-text-fill-color: #1A1A2E !important;
        }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. BARRERA DE SEGURIDAD Y SIDEBAR UNIFICADO
# ==============================================================================
if not st.session_state.get('authenticated', False) or st.session_state.get('role') not in ["Consultor", "Admin"]:
    st.warning("⚠️ Acceso denegado. Esta área es exclusiva para la Dirección y Consultores Estratégicos.")
    st.page_link("streamlit_app.py", label="⬅️ Volver al Portal de Acceso", icon="🚪")
    st.stop()

with st.sidebar:
    st.image("assets/logoEvangelistaCo.png", width=180)
    st.markdown("<h3 style='text-align: center; color: #D4AF37;'>Sentinel</h3>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.info(f"**Usuario:** {st.session_state.get('username')}\n**Rol:** 🔬 {st.session_state.get('role')}")
    
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.role = None
        st.switch_page("streamlit_app.py")

    st.markdown("---")
    st.page_link("streamlit_app.py", label="⬅️ Volver al Dashboard", icon="📊")
    st.markdown("---")
    st.caption("© 2026 Evangelista & Co.")

# ==============================================================================
# 3. INICIALIZACIÓN DEL DATA MESH (SUPABASE)
# ==============================================================================
@st.cache_resource
def init_supabase():
    url = os.getenv("SUPABASE_URL") or (st.secrets.get("SUPABASE_URL") if hasattr(st, "secrets") else None)
    key = os.getenv("SUPABASE_KEY") or (st.secrets.get("SUPABASE_KEY") if hasattr(st, "secrets") else None)
    
    if not url or not key:
        return None
    try:
        return create_client(url, key)
    except Exception:
        return None

supabase = init_supabase()

# ==============================================================================
# 4. INTERFAZ DIRECTIVA
# ==============================================================================
st.title("⚙️ Panel de Control Institucional")
st.markdown("*Evangelista & Co. | Infraestructura de Decision Intelligence*")
st.markdown("---")

if not supabase:
    st.error("⛔ ALERTA ESTRUCTURAL: Faltan credenciales de Supabase en la bóveda de Streamlit.")
    st.info("💡 **Acción requerida:** Ve a tu panel de Streamlit Cloud > Settings > Secrets y añade SUPABASE_URL y SUPABASE_KEY.")
    st.stop()

# Pestañas operativas
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "👔 Consultores", 
    "🏢 Clientes", 
    "🔗 Asignaciones", 
    "🔐 Credenciales BD",
    "🧠 Cerebro Estocástico (YAML)"
])

with tab1:
    st.subheader("Gestión de Consultores")
    with st.form("form_consultor"):
        col1, col2, col3 = st.columns(3)
        nombre = col1.text_input("Nombre Completo")
        email = col2.text_input("Correo Corporativo")
        rol = col3.selectbox("Rol Operativo", ["Consultor Estratégico", "Admin", "Partner"])
        
        if st.form_submit_button("Registrar Consultor"):
            try:
                supabase.table("saas_consultores").insert({"nombre": nombre, "email": email, "rol": rol}).execute()
                st.success(f"✅ Consultor {nombre} inyectado al Data Mesh.")
            except Exception as e:
                st.error(f"Error al registrar: {e}")

    st.markdown("##### Consultores Activos")
    try:
        response = supabase.table("saas_consultores").select("*").execute()
        if response.data:
            st.dataframe(pd.DataFrame(response.data)[['nombre', 'email', 'rol', 'activo']], use_container_width=True)
    except:
        st.warning("No se pudo cargar la vista de consultores.")

with tab2:
    st.subheader("Portafolio de Clientes")
    with st.form("form_cliente"):
        col1, col2, col3 = st.columns(3)
        nombre_comercial = col1.text_input("Nombre Comercial (Ej. Cibrián Arquitectos)")
        rfc = col2.text_input("RFC")
        industria = col3.text_input("Industria (Ej. Construcción)")
        
        if st.form_submit_button("Dar de Alta Cliente"):
            try:
                supabase.table("saas_clientes").insert({"nombre_comercial": nombre_comercial, "rfc": rfc, "industria": industria}).execute()
                st.success(f"✅ Cliente {nombre_comercial} perfilado en el sistema.")
            except Exception as e:
                st.error(f"Error al registrar: {e}")

    st.markdown("##### Clientes en Portafolio")
    try:
        response = supabase.table("saas_clientes").select("*").execute()
        if response.data:
            st.dataframe(pd.DataFrame(response.data)[['nombre_comercial', 'rfc', 'industria', 'estatus']], use_container_width=True)
    except:
        pass

with tab3:
    st.subheader("Asignación Estratégica")
    st.markdown("Vincule un consultor a una cuenta corporativa.")
    try:
        consultores = supabase.table("saas_consultores").select("id, nombre").execute().data
        clientes = supabase.table("saas_clientes").select("id, nombre_comercial").execute().data
        
        if consultores and clientes:
            dict_cons = {c['nombre']: c['id'] for c in consultores}
            dict_cli = {c['nombre_comercial']: c['id'] for c in clientes}
            
            with st.form("form_asignacion"):
                sel_cons = st.selectbox("Seleccionar Consultor", list(dict_cons.keys()))
                sel_cli = st.selectbox("Seleccionar Cliente", list(dict_cli.keys()))
                
                if st.form_submit_button("Vincular Cuenta"):
                    try:
                        supabase.table("saas_asignaciones").insert({"consultor_id": dict_cons[sel_cons], "cliente_id": dict_cli[sel_cli]}).execute()
                        st.success("✅ Asignación sellada.")
                    except Exception as e:
                        st.error(f"La asignación ya existe o hubo un error: {e}")
        else:
            st.warning("Se requiere al menos 1 consultor y 1 cliente para hacer asignaciones.")
    except:
        st.error("Error de lectura en asignaciones.")

with tab4:
    st.subheader("Conexión al Data Mesh del Cliente")
    if 'dict_cli' in locals() and dict_cli:
        with st.form("form_credenciales"):
            cliente_cred = st.selectbox("Cliente", list(dict_cli.keys()))
            col1, col2 = st.columns(2)
            db_host = col1.text_input("Host (URL)")
            db_port = col2.number_input("Puerto", value=5432)
            col3, col4, col5 = st.columns(3)
            db_name = col3.text_input("Nombre de BD (Database)")
            db_user = col4.text_input("Usuario")
            db_password = col5.text_input("Contraseña", type="password")
            
            if st.form_submit_button("Guardar Credenciales Seguras"):
                try:
                    supabase.table("saas_credenciales").insert({
                        "cliente_id": dict_cli[cliente_cred], "db_host": db_host, "db_port": db_port,
                        "db_name": db_name, "db_user": db_user, "db_password": db_password
                    }).execute()
                    st.success(f"✅ Tubería conectada para {cliente_cred}.")
                except Exception as e:
                    st.error(f"Error (Posible credencial existente): {e}")
    else:
        st.info("Registre clientes primero.")

with tab5:
    st.subheader("Motor de Lógica Multivariada (YAML Architect)")
    if 'dict_cli' in locals() and dict_cli:
        cliente_yaml = st.selectbox("Seleccione Cliente a Modelar", list(dict_cli.keys()))
        cliente_id_seleccionado = dict_cli[cliente_yaml]
        
        st.markdown("#### 1. Inferencia Cognitiva (Llama 3)")
        contexto_operativo = st.text_area(
            "Contexto de Riesgo (Input para IA)",
            value=f"Genera el modelo estocástico para {cliente_yaml}. Tablas disponibles: 'fact_compras' (costos), 'fact_proyectos' (ingresos).",
            height=80
        )
        
        if st.button("🤖 Arquitectar Cerebro Estocástico (Llama 3)"):
            with st.spinner("Invocando a Llama 3..."):
                try:
                    groq_key = os.getenv("GROQ_API_KEY") or (st.secrets.get("GROQ_API_KEY") if hasattr(st, "secrets") else None)
                    if not groq_key:
                        st.error("⛔ No se encontró GROQ_API_KEY en secretos.")
                    else:
                        from src.ai_agent import AIFinancialAgent
                        agent = AIFinancialAgent(api_key=groq_key)
                        nuevo_yaml = agent.generate_config_from_prompt(prompt=contexto_operativo, industry="General")
                        st.session_state['yaml_editor'] = nuevo_yaml
                        st.success("✅ Arquitectura de Nivel 7 generada.")
                except Exception as e:
                    st.error(f"Fallo catastrófico en la inferencia: {e}")
        
        st.markdown("#### 2. Código Fuente Estocástico")
        try:
            res_yaml = supabase.table("saas_configuraciones_yaml").select("*").eq("cliente_id", cliente_id_seleccionado).order('created_at', desc=True).limit(1).execute()
            yaml_actual = res_yaml.data[0]['yaml_content'] if res_yaml.data else ""
        except:
            yaml_actual = ""
            
        if 'yaml_editor' not in st.session_state or st.session_state.get('last_cli') != cliente_id_seleccionado:
            st.session_state['yaml_editor'] = yaml_actual
            st.session_state['last_cli'] = cliente_id_seleccionado

        nuevo_yaml = st.text_area("Código Fuente del Cerebro (YAML)", value=st.session_state['yaml_editor'], height=400)
        
        if st.button("💾 Inyectar Modelo a Producción"):
            if nuevo_yaml:
                try:
                    supabase.table("saas_configuraciones_yaml").insert({
                        "cliente_id": cliente_id_seleccionado, "yaml_content": nuevo_yaml, "es_activo": True
                    }).execute()
                    st.success("✅ Modelo guardado en el Data Mesh.")
                    st.session_state['yaml_editor'] = nuevo_yaml
                except Exception as e:
                    st.error(f"Error al guardar: {e}")
    else:
        st.info("Registre clientes primero.")