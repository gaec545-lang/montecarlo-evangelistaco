# ==============================================================================
# INYECCIÓN DE ENRUTAMIENTO (Bypass de Subcarpetas en Streamlit Cloud)
# Esto debe ir ANTES de importar cualquier módulo de 'src'
# ==============================================================================
import sys
import os

# Forzamos a Python a reconocer la carpeta 'evangelista-montecarlo' como la raíz
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
import streamlit as st
import pandas as pd
import os
from supabase import create_client, Client

# ==============================================================================
# 1. INICIALIZACIÓN DE LA CONEXIÓN A SUPABASE (DATA MESH)
# ==============================================================================
# Usamos st.cache_resource para no agotar el pool de conexiones de la base de datos
@st.cache_resource
def init_supabase() -> Client:
    url = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")
    
    if not url or not key:
        st.error("⛔ ALERTA ESTRUCTURAL: Faltan credenciales de Supabase en los secretos.")
        st.stop()
        
    return create_client(url, key)

supabase = init_supabase()

# ==============================================================================
# 2. INTERFAZ DIRECTIVA
# ==============================================================================
st.set_page_config(page_title="Sentinel | Admin", page_icon="⚙️", layout="wide")

st.title("⚙️ Panel de Control Institucional")
st.markdown("*Evangelista & Co. | Infraestructura de Decision Intelligence*")
st.markdown("---")

# Pestañas operativas mapeadas a tu esquema SQL
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "👔 Consultores", 
    "🏢 Clientes", 
    "🔗 Asignaciones", 
    "🔐 Credenciales BD",
    "🧠 Cerebro Estocástico (YAML)"
])

# ==============================================================================
# PESTAÑA 1: CONSULTORES
# ==============================================================================
with tab1:
    st.subheader("Gestión de Consultores")
    
    with st.form("form_consultor"):
        col1, col2, col3 = st.columns(3)
        nombre = col1.text_input("Nombre Completo")
        email = col2.text_input("Correo Corporativo")
        rol = col3.selectbox("Rol Operativo", ["Consultor Estratégico", "Admin", "Partner"])
        
        if st.form_submit_button("Registrar Consultor"):
            try:
                data = {"nombre": nombre, "email": email, "rol": rol}
                supabase.table("saas_consultores").insert(data).execute()
                st.success(f"✅ Consultor {nombre} inyectado al Data Mesh.")
            except Exception as e:
                st.error(f"Error al registrar: {e}")

    # Mostrar tabla viva de Supabase
    st.markdown("##### Consultores Activos")
    try:
        response = supabase.table("saas_consultores").select("*").execute()
        if response.data:
            df_cons = pd.DataFrame(response.data)
            st.dataframe(df_cons[['nombre', 'email', 'rol', 'activo']], use_container_width=True)
        else:
            st.info("No hay consultores registrados.")
    except Exception as e:
        st.warning("No se pudo cargar la vista de consultores.")

# ==============================================================================
# PESTAÑA 2: CLIENTES
# ==============================================================================
with tab2:
    st.subheader("Portafolio de Clientes")
    
    with st.form("form_cliente"):
        col1, col2, col3 = st.columns(3)
        nombre_comercial = col1.text_input("Nombre Comercial (Ej. Cibrián Arquitectos)")
        rfc = col2.text_input("RFC")
        industria = col3.text_input("Industria (Ej. Construcción)")
        
        if st.form_submit_button("Dar de Alta Cliente"):
            try:
                data = {"nombre_comercial": nombre_comercial, "rfc": rfc, "industria": industria}
                supabase.table("saas_clientes").insert(data).execute()
                st.success(f"✅ Cliente {nombre_comercial} perfilado en el sistema.")
            except Exception as e:
                st.error(f"Error al registrar: {e}")

    st.markdown("##### Clientes en Portafolio")
    try:
        response = supabase.table("saas_clientes").select("*").execute()
        if response.data:
            df_cli = pd.DataFrame(response.data)
            st.dataframe(df_cli[['nombre_comercial', 'rfc', 'industria', 'estatus']], use_container_width=True)
    except:
        pass

# ==============================================================================
# PESTAÑA 3: ASIGNACIONES (El Matrimonio Operativo)
# ==============================================================================
with tab3:
    st.subheader("Asignación Estratégica")
    st.markdown("Vincule un consultor a una cuenta corporativa para aislar la confidencialidad.")
    
    # Cargar listas para selects
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
                    data = {
                        "consultor_id": dict_cons[sel_cons],
                        "cliente_id": dict_cli[sel_cli]
                    }
                    try:
                        supabase.table("saas_asignaciones").insert(data).execute()
                        st.success("✅ Asignación sellada.")
                    except Exception as e:
                        st.error(f"La asignación ya existe o hubo un error: {e}")
        else:
            st.warning("Se requiere al menos 1 consultor y 1 cliente para hacer asignaciones.")
    except Exception as e:
        st.error(f"Error de lectura: {e}")

# ==============================================================================
# PESTAÑA 4: CREDENCIALES BD
# ==============================================================================
with tab4:
    st.subheader("Conexión al Data Mesh del Cliente")
    st.markdown("Inyecte las credenciales del lago de datos del cliente (Supabase/Postgres).")
    
    if 'dict_cli' in locals() and dict_cli:
        with st.form("form_credenciales"):
            cliente_cred = st.selectbox("Cliente", list(dict_cli.keys()), key="cred_cli")
            
            col1, col2 = st.columns(2)
            db_host = col1.text_input("Host (URL)")
            db_port = col2.number_input("Puerto", value=5432)
            
            col3, col4, col5 = st.columns(3)
            db_name = col3.text_input("Nombre de BD (Database)")
            db_user = col4.text_input("Usuario")
            db_password = col5.text_input("Contraseña", type="password")
            
            if st.form_submit_button("Guardar Credenciales Seguras"):
                data = {
                    "cliente_id": dict_cli[cliente_cred],
                    "db_host": db_host, "db_port": db_port,
                    "db_name": db_name, "db_user": db_user, 
                    "db_password": db_password # En producción futura, envolver en encriptador
                }
                try:
                    supabase.table("saas_credenciales").insert(data).execute()
                    st.success(f"✅ Tubería de datos conectada para {cliente_cred}.")
                except Exception as e:
                    st.error(f"Error (Posiblemente este cliente ya tiene credenciales): {e}")
    else:
        st.info("Registre clientes primero.")

# ==============================================================================
# PESTAÑA 5: CEREBRO ESTOCÁSTICO (YAML & IA)
# ==============================================================================
with tab5:
    st.subheader("Motor de Lógica Multivariada (YAML Architect)")
    st.markdown("Gestione la inteligencia artificial de los modelos predictivos de cada cliente.")
    
    if 'dict_cli' in locals() and dict_cli:
        cliente_yaml = st.selectbox("Seleccione Cliente a Modelar", list(dict_cli.keys()), key="yaml_cli")
        cliente_id_seleccionado = dict_cli[cliente_yaml]
        
        # 1. Autodetección de esquema vía IA (Marcador para tu código de ai_agent)
        if st.button("🤖 Autodetectar Tablas y Generar YAML Base (Llama 3)"):
            st.info("Conectando con Llama 3 para inferencia de esquema... (Aquí se invocará tu AI Agent)")
            # Aquí inyectarás la llamada a src.ai_agent.py cuando lo integremos.
            # Por ahora, generamos un YAML de plantilla.
            plantilla_yaml = f"""client:\n  id: "{cliente_yaml.lower().replace(' ', '_')}"\n  name: "{cliente_yaml}"\n  industry: "Detectando..."\n# Llama 3 inyectará las Cópulas y el Modelo aquí..."""
            st.session_state['yaml_editor'] = plantilla_yaml
        
        # 2. Recuperar el YAML actual de la BD
        try:
            res_yaml = supabase.table("saas_configuraciones_yaml").select("*").eq("cliente_id", cliente_id_seleccionado).order('created_at', desc=True).limit(1).execute()
            yaml_actual = res_yaml.data[0]['yaml_content'] if res_yaml.data else ""
        except:
            yaml_actual = ""
            
        if 'yaml_editor' not in st.session_state or st.session_state.get('last_cli') != cliente_id_seleccionado:
            st.session_state['yaml_editor'] = yaml_actual
            st.session_state['last_cli'] = cliente_id_seleccionado

        # 3. Editor de Texto Interactivo
        nuevo_yaml = st.text_area("Código Fuente del Cerebro (YAML)", value=st.session_state['yaml_editor'], height=400)
        
        # 4. Botón de Guardado en Supabase
        if st.button("💾 Inyectar Modelo a Producción (Guardar)"):
            if nuevo_yaml:
                data = {
                    "cliente_id": cliente_id_seleccionado,
                    "yaml_content": nuevo_yaml,
                    "es_activo": True
                }
                try:
                    supabase.table("saas_configuraciones_yaml").insert(data).execute()
                    st.success("✅ Modelo YAML guardado e Inyectado en el Data Mesh.")
                    st.session_state['yaml_editor'] = nuevo_yaml
                except Exception as e:
                    st.error(f"Error al guardar: {e}")
            else:
                st.warning("El YAML está vacío.")
    else:
        st.info("Registre clientes primero.")