# ==============================================================================
# INYECCIÓN DE ENRUTAMIENTO (Grado Militar - Bypass Estructural)
# Esto debe ir ANTES de importar cualquier módulo de 'src'
# ==============================================================================
import sys
import os

# 1. Detectamos la ubicación física exacta de este archivo (streamlit_app.py)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Forzamos a Python a subir exactamente un nivel para establecer la raíz del sistema
# Esto garantiza que la carpeta 'src' sea visible sin importar cómo Streamlit clone el repo
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..'))

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# --- A PARTIR DE AQUÍ VAN TUS IMPORTACIONES ORIGINALES ---
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any
from datetime import datetime, timedelta

from src.user_manager import UserManager
from src.configuration_manager import ConfigurationManager
from src.decision_pipeline import DecisionPipeline

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE PÁGINA
# ═══════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Sentinel - Decision Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════════
# FUNCIONES DE NEGOCIO (PIPELINE)
# ═══════════════════════════════════════════════════════════════

@st.cache_resource
def load_pipeline(client_file: str):
    config = ConfigurationManager(
        template='configs/templates/alimentos.yaml',
        client_config=f'configs/clients/{client_file}'
    )
    
    try:
        supabase_creds = {
            'host': 'aws-0-region.pooler.supabase.com',
            'database': 'postgres',
            'username': 'postgres',
            'password': 'password_placeholder',
            'port': 6543
        }
    except Exception:
        supabase_creds = None
        st.warning("⚠️ Operando sin conexión a Base de Datos.")
    
    pipeline = DecisionPipeline(config, supabase_creds)
    return pipeline, config
    
@st.cache_data
def run_pipeline(_pipeline):
    return _pipeline.execute()

# ═══════════════════════════════════════════════════════════════
# FUNCIONES DE VISUALIZACIÓN
# ═══════════════════════════════════════════════════════════════

def render_gauge(value: float, title: str, range_max: float, threshold: float = None):
    if threshold and value > threshold:
        color = "red"
    elif threshold and value > threshold * 0.7:
        color = "orange"
    else:
        color = "green"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value * 100 if value < 1 else value,
        title={'text': title, 'font': {'size': 20}},
        number={'suffix': '%' if value < 1 else '', 'font': {'size': 36}},
        gauge={
            'axis': {'range': [0, range_max * 100 if range_max < 1 else range_max]},
            'bar': {'color': color},
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': threshold * 100 if threshold and threshold < 1 else threshold
            } if threshold else None,
            'steps': [
                {'range': [0, (threshold * 100 if threshold and threshold < 1 else threshold) * 0.7], 'color': "lightgreen"},
                {'range': [(threshold * 100 if threshold and threshold < 1 else threshold) * 0.7, (threshold * 100 if threshold and threshold < 1 else threshold)], 'color': "yellow"},
                {'range': [(threshold * 100 if threshold and threshold < 1 else threshold), range_max * 100 if range_max < 1 else range_max], 'color': "lightcoral"}
            ] if threshold else None
        }
    ))
    fig.update_layout(height=250, margin=dict(l=10, r=10, t=50, b=10))
    return fig

def render_tornado_chart(sensitivity_df: pd.DataFrame):
    df = sensitivity_df.sort_values('importance', ascending=True)
    fig = px.bar(
        df,
        x='importance',
        y='variable',
        orientation='h',
        title='Análisis de Sensibilidad - Impacto de Variables',
        labels={'importance': 'Importancia (% de Varianza Explicada)', 'variable': 'Variable'},
        color='importance',
        color_continuous_scale='Reds',
        text=df['importance'].apply(lambda x: f'{x:.1%}')
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(height=400, showlegend=False, xaxis_title="Importancia (%)", yaxis_title="", font=dict(size=14))
    return fig

def render_distribution_chart(results: pd.DataFrame, stats: Dict):
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=results['outcome'], nbinsx=50, name='Distribución', marker_color='lightblue', opacity=0.7))
    fig.add_vline(x=stats['p50'], line_dash="dash", line_color="blue", annotation_text=f"P50: ${stats['p50']:,.0f}")
    fig.add_vline(x=stats['p10'], line_dash="dash", line_color="red", annotation_text=f"P10: ${stats['p10']:,.0f}")
    fig.add_vline(x=stats['p90'], line_dash="dash", line_color="green", annotation_text=f"P90: ${stats['p90']:,.0f}")
    fig.add_vrect(
        x0=results['outcome'].min(), x1=0,
        fillcolor="red", opacity=0.1, layer="below", line_width=0,
        annotation_text="Zona de Pérdida", annotation_position="top left"
    )
    fig.update_layout(title='Distribución de Resultados (10,000 Simulaciones)', xaxis_title='Resultado (MXN)', yaxis_title='Frecuencia', height=400, showlegend=False)
    return fig

# ═══════════════════════════════════════════════════════════════
# SISTEMA DE AUTENTICACIÓN
# ═══════════════════════════════════════════════════════════════

def login_page():
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.image("assets/logoEvangelistaCo.png", width=200) 
        st.markdown("<h2 style='text-align: center; color: #1A1A2E;'>Portal de Socios</h2>", unsafe_allow_html=True)
        st.markdown("---")
        st.subheader("Autenticación")
        
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        
        if st.button("🔓 Iniciar Sesión", use_container_width=True):
            if not username or not password:
                st.warning("Por favor ingresa usuario y contraseña.")
                return

            manager = UserManager()
            user = manager.authenticate(username, password, ip="streamlit_client")
            
            if user:
                st.session_state.authenticated = True
                st.session_state.role = user.role
                st.session_state.username = user.nombre_completo
                st.session_state.user_email = user.email
                st.session_state.client_id = getattr(user, 'client_id', None)
                st.session_state.last_activity = datetime.now().isoformat()
                st.rerun()
            else:
                st.error("❌ Credenciales inválidas o cuenta bloqueada temporalmente.")

# ═══════════════════════════════════════════════════════════════
# VISTAS (EJECUTIVO / CONSULTOR)
# ═══════════════════════════════════════════════════════════════

def vista_ejecutivo(stats: Dict, triggers: List[Dict], results: pd.DataFrame, config):
    st.markdown(f"<h2 style='color: #1f77b4;'>📊 Dashboard Ejecutivo - {config.get('client.name', 'Cliente')}</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.subheader("📈 Indicadores Clave de Riesgo")
    col1, col2, col3 = st.columns(3)
    with col1:
        threshold_loss = config.get('thresholds.critical_loss_prob', 0.25)
        st.plotly_chart(render_gauge(stats['prob_loss'], "Probabilidad de Pérdida", 1.0, threshold_loss), use_container_width=True)
    with col2:
        st.plotly_chart(render_gauge(abs(stats['var_95']), "VaR 95% (Pérdida Máxima)", abs(stats['var_95']) * 2, abs(stats['var_95']) * 0.8), use_container_width=True)
    with col3:
        st.plotly_chart(render_gauge(stats['p50'], "Resultado Esperado (P50)", stats['p90'], stats['mean'] * 0.5), use_container_width=True)
    
    st.markdown("---")
    st.subheader("💰 Resumen de Exposición Financiera")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Ganancia Esperada (Mediana)", f"${stats['p50']:,.0f}", f"Rango: ${stats['p25']:,.0f} - ${stats['p75']:,.0f}")
        st.metric("Escenario Pesimista (P10)", f"${stats['p10']:,.0f}", "10% de probabilidad de caer aquí", delta_color="inverse")
    with col2:
        st.metric("Escenario Optimista (P90)", f"${stats['p90']:,.0f}", "10% de probabilidad de superar esto", delta_color="normal")
        st.metric("Riesgo de Pérdida", f"{stats['prob_loss']:.1%}", "Probabilidad de resultado negativo", delta_color="inverse")
    
    st.markdown("---")
    st.subheader("🚨 Alertas Activas")
    if triggers:
        for trigger in triggers:
            nivel = trigger.get('nivel', 'INFO')
            if nivel == 'CRÍTICO': st.error(f"🔴 **{nivel}**: {trigger.get('mensaje', '')}")
            elif nivel == 'ALTO': st.warning(f"🟡 **{nivel}**: {trigger.get('mensaje', '')}")
            else: st.info(f"🟠 **{nivel}**: {trigger.get('mensaje', '')}")
        st.info("💡 **Nota**: Para un análisis detallado, contacte a su consultor de Evangelista & Co.")
    else:
        st.success("✅ No hay alertas activas. Todos los indicadores dentro de parámetros normales.")
        
    st.markdown("---")
    st.subheader("📊 Distribución de Resultados")
    st.plotly_chart(render_distribution_chart(results, stats), use_container_width=True)

def vista_consultor(stats: Dict, triggers: List[Dict], sensitivity: pd.DataFrame, results: pd.DataFrame, config, business_narrative: str, recommendations: List[Dict]):
    st.markdown(f"""
        <h2 style='color: #d62728;'>🔬 Vista Consultor - Análisis Completo</h2>
        <h4 style='color: #666;'>Cliente: {config.get('client.name', 'N/A')} | Industria: {config.get('client.industry', 'N/A')}</h4>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
    st.subheader("📈 Indicadores Clave de Riesgo")
    col1, col2, col3 = st.columns(3)
    with col1:
        threshold_loss = config.get('thresholds.critical_loss_prob', 0.25)
        st.plotly_chart(render_gauge(stats['prob_loss'], "Probabilidad de Pérdida", 1.0, threshold_loss), use_container_width=True)
    with col2:
        st.plotly_chart(render_gauge(abs(stats['var_95']), "VaR 95%", abs(stats['var_95']) * 2, abs(stats['var_95']) * 0.8), use_container_width=True)
    with col3:
        st.plotly_chart(render_gauge(stats['p50'], "Resultado Esperado (P50)", stats['p90'], stats['mean'] * 0.5), use_container_width=True)
    
    st.markdown("---")
    st.subheader("📝 Traducción Ejecutiva (Fase 3)")
    if isinstance(business_narrative, dict):
        st.info(business_narrative.get('confidence_level', ''))
        st.markdown(business_narrative.get('executive_summary', ''))
    
    st.markdown("---")
    st.subheader("🎯 Análisis de Sensibilidad - Diagnóstico Raíz")
    st.plotly_chart(render_tornado_chart(sensitivity), use_container_width=True)
    
    st.markdown("---")
    st.subheader("⚡ Inteligencia de Decisiones (Fase 4)")
    if recommendations:
        for idx, rec in enumerate(recommendations, 1):
            with st.expander(f"Estrategia #{idx}: {rec['title']} (Prioridad: {rec['priority']})", expanded=(rec['priority']==1)):
                st.markdown(f"**Descripción:** {rec['description']}")
                st.markdown("**Acciones Inmediatas:**")
                for act in rec['actions']:
                    st.write(f"- Paso {act['step']}: {act['action']} *(Responsable: {act['responsible']})*")
    else:
        st.success("✅ No hay recomendaciones de mitigación críticas por el momento.")
    
    st.markdown("---")
    st.subheader("📊 Distribución de Resultados")
    st.plotly_chart(render_distribution_chart(results, stats), use_container_width=True)

# ═══════════════════════════════════════════════════════════════
# APLICACIÓN PRINCIPAL
# ═══════════════════════════════════════════════════════════════

def main():
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
    
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'role' not in st.session_state:
        st.session_state.role = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    
    if not st.session_state.authenticated:
        login_page()
        return

    if 'last_activity' in st.session_state:
        last_activity = datetime.fromisoformat(st.session_state.last_activity)
        if datetime.now() - last_activity > timedelta(hours=8):
            st.warning("⚠️ Sesión expirada por inactividad. Por seguridad, vuelve a iniciar sesión.")
            st.session_state.authenticated = False
            st.session_state.clear()
            st.rerun()
        else:
            st.session_state.last_activity = datetime.now().isoformat()
            
    with st.sidebar:
        st.image("assets/logoEvangelistaCo.png", width=180)
        st.markdown("<h3 style='text-align: center; color: #D4AF37;'>Sentinel</h3>", unsafe_allow_html=True)
        st.markdown("---")
        
        role_emoji = "👔" if st.session_state.role == "Ejecutivo" else "🔬"
        st.info(f"**Usuario:** {st.session_state.username}\n**Rol:** {role_emoji} {st.session_state.role}")
        
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.role = None
            st.rerun()

        if st.session_state.role in ["Consultor", "Admin"]:
            st.markdown("---")
            st.page_link("pages/3_⚙️_Admin_Panel.py", label="Panel de Administración", icon="⚙️")
            st.markdown("---")
            
            st.markdown("**🏢 Portafolio de Clientes:**")
            
            # --- PROTECCIÓN CONTRA DIRECTORIOS VACÍOS ---
            client_files = []
            if os.path.exists('configs/clients'):
                client_files = [f for f in os.listdir('configs/clients') if f.endswith('.yaml')]
                
            if not client_files:
                client_files = ['SIN_CLIENTES']

            selected_client_file = st.selectbox("Seleccionar Auditoría:", client_files)
        else:
            st.markdown("---")
            st.markdown("**🏢 Panel de Cliente:**")
            client_id = st.session_state.get('client_id', 'Desconocido')
            st.info(f"ID: {client_id}")
            selected_client_file = f"{client_id}_config.yaml"
            
        st.markdown("---")
        st.markdown("**⚙️ Configuración:**")
        st.caption("• Pipeline: 4 Fases")
        st.caption("• Simulaciones: 10,000")
        st.caption("• Motor: Decision Intelligence")
        st.markdown("---")
        st.caption("© 2026 Evangelista & Co.")

    # ═════ LÓGICA DE PROTECCIÓN (ESTADO VACÍO) ═════
    if selected_client_file == 'SIN_CLIENTES':
        st.markdown("<h2 style='color: #1f77b4;'>🛡️ Sentinel Data Mesh en Línea</h2>", unsafe_allow_html=True)
        st.markdown("---")
        st.info("La infraestructura está operativa, pero no se detectaron Cerebros Estocásticos (YAMLs) activos en el almacenamiento local.")
        
        st.markdown("""
        ### Próximos Pasos Directivos:
        1. Dirígete al **Panel de Administración** utilizando el menú lateral izquierdo.
        2. Configura a tu primer cliente corporativo (Ej. Cibrián).
        3. Utiliza la Pestaña 5 para que el **Agente IA de Llama 3** genere el modelo matemático.
        """)
        return # Detiene la ejecución para no lanzar el Pipeline y evitar el FileNotFoundError

    # ═════ EJECUCIÓN DEL PIPELINE (SI HAY CLIENTES) ═════
    try:
        with st.spinner(f"⚙️ Inicializando Decision Pipeline para {selected_client_file}..."):
            pipeline, config = load_pipeline(selected_client_file)
        
        with st.spinner("🧠 Ejecutando Inteligencia de Decisiones (4 Fases)..."):
            pipeline_results = run_pipeline(pipeline)
            
            results = pipeline_results['simulation_results']
            stats = pipeline_results['statistics']
            sensitivity = pipeline_results['sensitivity']
            business_narrative = pipeline_results['business_narrative']
            recommendations = pipeline_results['recommendations']
            triggers = []
            
        if st.session_state.role == "Ejecutivo":
            vista_ejecutivo(stats, triggers, results, config)
        elif st.session_state.role == "Consultor":
            vista_consultor(stats, triggers, sensitivity, results, config, business_narrative, recommendations)
        else:
            st.error("❌ Rol no reconocido")
            
    except FileNotFoundError as e:
        st.error(f"❌ Error Estructural: No se encontró el archivo físico del cliente. {str(e)}")
        st.info("Por favor, asegúrate de generar el YAML en el Panel de Administración.")

if __name__ == "__main__":
    main()