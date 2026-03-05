import streamlit as st
import yaml
import os
import sys
from sqlalchemy import create_engine

# Conectar con el backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.connection_manager import ConnectionManager

st.set_page_config(page_title="Admin Panel", page_icon="⚙️", layout="wide")

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
# TAB 1: QUICK CONNECT
# ═══════════════════════════════════════════════════════════════
with tabs[0]:
    st.subheader("⚡ Quick Connect: Ingesta de Datos")
    st.markdown("Vincula la base de datos PostgreSQL/Supabase del cliente.")
    with st.form("quick_connect_form"):
        c_id = st.text_input("ID del Cliente (ej. pasteleria_puebla)")
        c_uri = st.text_input("URL de Conexión (URI)", type="password", placeholder="postgresql://...")
        
        if st.form_submit_button("Validar y Guardar Conexión", use_container_width=True):
            if not c_id or not c_uri:
                st.error("Campos incompletos.")
            else:
                try:
                    test_uri = c_uri.replace("postgres://", "postgresql://", 1)
                    test_engine = create_engine(test_uri, pool_pre_ping=True, connect_args={'connect_timeout': 5})
                    with test_engine.connect() as conn:
                        pass
                    
                    conn_manager = ConnectionManager()
                    conn_manager.save_connection(client_id=c_id, raw_uri=test_uri, username=st.session_state.username)
                    st.success(f"✅ Conexión blindada y guardada en producción para '{c_id}'.")
                except Exception as e:
                    st.error("❌ Fallo de conexión o credenciales inválidas.")
                    st.code(str(e))

# ═══════════════════════════════════════════════════════════════
# TAB 2: YAML BUILDER
# ═══════════════════════════════════════════════════════════════
with tabs[1]:
    st.subheader("📋 YAML Builder: Parametrización de Clientes")
    with st.form("yaml_builder_form"):
        col1, col2 = st.columns(2)
        with col1:
            client_id = st.text_input("ID Único del Cliente")
            client_name = st.text_input("Nombre Comercial")
        with col2:
            industry = st.selectbox("Sector", ["Alimentos", "Textil", "Construcción", "Retail"])
            simulations = st.number_input("Iteraciones", min_value=1000, value=10000, step=1000)

        v_name = st.text_input("Nombre de la Variable de Riesgo (ej. costo_materia_prima)")
        col_v1, col_v2, col_v3 = st.columns(3)
        with col_v1:
            v_dist = st.selectbox("Distribución", ["normal", "triangular", "uniform"])
        with col_v2:
            v_mean = st.number_input("Media (Valor Base)", value=0.0)
        with col_v3:
            v_std = st.number_input("Desviación (Volatilidad)", value=0.0)

        t_loss = st.slider("Umbral Crítico de Probabilidad de Pérdida (%)", 1, 100, 25) / 100.0

        if st.form_submit_button("💾 Compilar y Guardar Modelo", use_container_width=True):
            if not client_id or not v_name:
                st.error("❌ ID del Cliente y Variable son obligatorios.")
            else:
                config_dict = {
                    "client": {
                        "id": client_id,  # <--- INYECCIÓN CRÍTICA PARA EL EXTRACTOR (FASE 1)
                        "name": client_name, 
                        "industry": industry.lower()
                    },
                    "simulation": {"iterations": simulations},
                    "variables": {v_name: {"distribution": v_dist, "params": {"mean": v_mean, "std_dev": v_std}}},
                    "thresholds": {"critical_loss_prob": t_loss}
                }
                os.makedirs(os.path.join("configs", "clients"), exist_ok=True)
                file_path = os.path.join("configs", "clients", f"{client_id}_config.yaml")
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
                    st.success(f"✅ Modelo parametrizado exitosamente. Archivo guardado en: `{file_path}`")
                except Exception as e:
                    st.error(f"❌ Error crítico al escribir en el disco: {e}")
                    
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
                    # Si es consultor, no limitamos su vista (None). Si es ejecutivo, anclamos su ID.
                    cid = new_client_id if new_role == "Ejecutivo" else None
                    success = um.create_user(new_username, new_password, new_role, new_name, new_email, st.session_state.username, cid)
                    if success:
                        st.success(f"✅ Ejecutivo '{new_name}' autorizado. Modelo anclado: {cid}")
                    else:
                        st.error("❌ El usuario ya existe en la bóveda.")
                except ValueError as ve:
                    st.error(f"❌ {ve}")
