import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.user_manager import UserManager
from src.configuration_manager import ConfigurationManager
from src.decision_pipeline import DecisionPipeline
from src.client_manager import ClientManager

# ═══════════════════════════════════════════════════════════════
# CONFIGURACION DE PAGINA
# ═══════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Sentinel - Decision Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════════
# PIPELINE
# ═══════════════════════════════════════════════════════════════

@st.cache_resource
def load_pipeline(client_id: str, config_file: str):
    """Carga config y pipeline para un cliente. Usa modo single-file."""
    config = ConfigurationManager(config_file)

    supabase_creds = None
    try:
        from src.connection_manager import ConnectionManager
        conn_mgr = ConnectionManager()
        supabase_creds = conn_mgr.get_client_connection(client_id)
    except Exception:
        pass  # Sin boveda disponible → opera sin DB

    pipeline = DecisionPipeline(config, supabase_creds)
    return pipeline, config


@st.cache_data
def run_pipeline(_pipeline):
    return _pipeline.execute()


# ═══════════════════════════════════════════════════════════════
# VISUALIZACION
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
                {'range': [0, (threshold * 100 if threshold and threshold < 1 else threshold) * 0.7],
                 'color': "lightgreen"},
                {'range': [(threshold * 100 if threshold and threshold < 1 else threshold) * 0.7,
                           (threshold * 100 if threshold and threshold < 1 else threshold)],
                 'color': "yellow"},
                {'range': [(threshold * 100 if threshold and threshold < 1 else threshold),
                           range_max * 100 if range_max < 1 else range_max],
                 'color': "lightcoral"}
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
        title='Analisis de Sensibilidad - Impacto de Variables',
        labels={'importance': 'Importancia (% de Varianza Explicada)', 'variable': 'Variable'},
        color='importance',
        color_continuous_scale='Reds',
        text=df['importance'].apply(lambda x: f'{x:.1%}')
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(height=400, showlegend=False, xaxis_title="Importancia (%)",
                      yaxis_title="", font=dict(size=14))
    return fig


def render_distribution_chart(results: pd.DataFrame, stats: Dict):
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=results['outcome'], nbinsx=50, name='Distribucion',
        marker_color='lightblue', opacity=0.7
    ))
    fig.add_vline(x=stats['p50'], line_dash="dash", line_color="blue",
                  annotation_text=f"P50: ${stats['p50']:,.0f}")
    fig.add_vline(x=stats['p10'], line_dash="dash", line_color="red",
                  annotation_text=f"P10: ${stats['p10']:,.0f}")
    fig.add_vline(x=stats['p90'], line_dash="dash", line_color="green",
                  annotation_text=f"P90: ${stats['p90']:,.0f}")
    fig.add_vrect(
        x0=results['outcome'].min(), x1=0,
        fillcolor="red", opacity=0.1, layer="below", line_width=0,
        annotation_text="Zona de Perdida", annotation_position="top left"
    )
    fig.update_layout(
        title='Distribucion de Resultados (Simulaciones Monte Carlo)',
        xaxis_title='Resultado (MXN)', yaxis_title='Frecuencia',
        height=400, showlegend=False
    )
    return fig


# ═══════════════════════════════════════════════════════════════
# AUTENTICACION
# ═══════════════════════════════════════════════════════════════

def login_page():
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        try:
            st.image("assets/logoEvangelistaCo.png", width=200)
        except Exception:
            st.markdown("### Evangelista & Co.")
        st.markdown("<h2 style='text-align: center; color: #1A1A2E;'>Portal de Socios</h2>",
                    unsafe_allow_html=True)
        st.markdown("---")
        st.subheader("Autenticacion")

        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")

        if st.button("🔓 Iniciar Sesion", use_container_width=True):
            if not username or not password:
                st.warning("Por favor ingresa usuario y contraseña.")
                return

            manager = UserManager()
            user = manager.authenticate(username, password, ip="streamlit_client")

            if user:
                st.session_state.authenticated = True
                st.session_state.role = user.role
                st.session_state.username = user.nombre_completo
                st.session_state.raw_username = username
                st.session_state.user_email = user.email
                st.session_state.client_id = getattr(user, 'client_id', None)
                st.session_state.last_activity = datetime.now().isoformat()
                st.rerun()
            else:
                st.error("❌ Credenciales invalidas o cuenta bloqueada temporalmente.")


# ═══════════════════════════════════════════════════════════════
# VISTAS
# ═══════════════════════════════════════════════════════════════

def vista_ejecutivo(stats: Dict, triggers: List[Dict], results: pd.DataFrame, config):
    client_name = config.get('client.name', 'Cliente')
    st.markdown(f"<h2 style='color: #1f77b4;'>📊 Dashboard Ejecutivo - {client_name}</h2>",
                unsafe_allow_html=True)
    st.markdown("---")

    st.subheader("📈 Indicadores Clave de Riesgo")
    col1, col2, col3 = st.columns(3)

    with col1:
        threshold_loss = config.get('thresholds.critical_loss_prob', 0.25)
        st.plotly_chart(render_gauge(stats['prob_loss'], "Probabilidad de Perdida", 1.0, threshold_loss),
                        use_container_width=True)
    with col2:
        st.plotly_chart(render_gauge(abs(stats['var_95']), "VaR 95% (Perdida Maxima)",
                                     abs(stats['var_95']) * 2, abs(stats['var_95']) * 0.8),
                        use_container_width=True)
    with col3:
        st.plotly_chart(render_gauge(stats['p50'], "Resultado Esperado (P50)",
                                     stats['p90'], stats['mean'] * 0.5),
                        use_container_width=True)

    st.markdown("---")
    st.subheader("💰 Resumen de Exposicion Financiera")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Ganancia Esperada (Mediana)", f"${stats['p50']:,.0f}",
                  f"Rango: ${stats['p25']:,.0f} - ${stats['p75']:,.0f}")
        st.metric("Escenario Pesimista (P10)", f"${stats['p10']:,.0f}",
                  "10% de probabilidad de caer aqui", delta_color="inverse")
    with col2:
        st.metric("Escenario Optimista (P90)", f"${stats['p90']:,.0f}",
                  "10% de probabilidad de superar esto", delta_color="normal")
        st.metric("Riesgo de Perdida", f"{stats['prob_loss']:.1%}",
                  "Probabilidad de resultado negativo", delta_color="inverse")

    st.markdown("---")
    st.subheader("🚨 Alertas Activas")
    if triggers:
        for trigger in triggers:
            nivel = trigger.get('nivel', 'INFO')
            if nivel == 'CRITICO':
                st.error(f"🔴 **{nivel}**: {trigger.get('mensaje', '')}")
            elif nivel == 'ALTO':
                st.warning(f"🟡 **{nivel}**: {trigger.get('mensaje', '')}")
            else:
                st.info(f"🟠 **{nivel}**: {trigger.get('mensaje', '')}")
            st.caption(f"Metrica afectada: {trigger.get('metrica', 'General')}")
        st.info("💡 Para un analisis detallado, contacta a tu consultor de Evangelista & Co.")
    else:
        st.success("✅ No hay alertas activas. Todos los indicadores dentro de parametros normales.")

    st.markdown("---")
    st.subheader("📊 Distribucion de Resultados")
    st.plotly_chart(render_distribution_chart(results, stats), use_container_width=True)


def vista_consultor(stats: Dict, triggers: List[Dict], sensitivity: pd.DataFrame,
                    results: pd.DataFrame, config, business_narrative: str,
                    recommendations: List[Dict]):
    client_name = config.get('client.name', 'N/A')
    industry = config.get('client.industry', 'N/A')
    st.markdown(f"""
        <h2 style='color: #d62728;'>🔬 Vista Consultor - Analisis Completo</h2>
        <h4 style='color: #666;'>Cliente: {client_name} | Industria: {industry}</h4>
    """, unsafe_allow_html=True)
    st.markdown("---")

    st.subheader("📈 Indicadores Clave de Riesgo")
    col1, col2, col3 = st.columns(3)
    with col1:
        threshold_loss = config.get('thresholds.critical_loss_prob', 0.25)
        st.plotly_chart(render_gauge(stats['prob_loss'], "Probabilidad de Perdida", 1.0, threshold_loss),
                        use_container_width=True)
    with col2:
        st.plotly_chart(render_gauge(abs(stats['var_95']), "VaR 95%",
                                     abs(stats['var_95']) * 2, abs(stats['var_95']) * 0.8),
                        use_container_width=True)
    with col3:
        st.plotly_chart(render_gauge(stats['p50'], "Resultado Esperado (P50)",
                                     stats['p90'], stats['mean'] * 0.5),
                        use_container_width=True)

    st.markdown("---")
    st.subheader("📝 Traduccion Ejecutiva (Fase 3)")
    if isinstance(business_narrative, dict):
        st.info(business_narrative.get('confidence_level', ''))
        st.markdown(business_narrative.get('executive_summary', ''))
    else:
        st.markdown(str(business_narrative))

    st.markdown("---")
    st.subheader("🎯 Analisis de Sensibilidad - Diagnostico Raiz")
    if sensitivity is not None and not sensitivity.empty:
        st.plotly_chart(render_tornado_chart(sensitivity), use_container_width=True)

    st.markdown("---")
    st.subheader("⚡ Inteligencia de Decisiones (Fase 4)")
    if recommendations:
        for idx, rec in enumerate(recommendations, 1):
            with st.expander(
                f"Estrategia #{idx}: {rec['title']} (Prioridad: {rec['priority']})",
                expanded=(rec['priority'] == 1)
            ):
                st.markdown(f"**Descripcion:** {rec['description']}")
                st.markdown("**Acciones Inmediatas:**")
                for act in rec.get('actions', []):
                    st.write(f"- Paso {act['step']}: {act['action']} *(Responsable: {act['responsible']})*")
    else:
        st.success("✅ No hay recomendaciones de mitigacion criticas por el momento.")

    st.markdown("---")
    st.subheader("📊 Distribucion de Resultados")
    st.plotly_chart(render_distribution_chart(results, stats), use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# APLICACION PRINCIPAL
# ═══════════════════════════════════════════════════════════════

def main():
    st.markdown("""
        <style>
            [data-testid="stSidebarNav"] {display: none !important;}
            .stButton>button { border: 1px solid #D4AF37; background-color: transparent; }
            .stButton>button:hover { border: 1px solid #1A1A2E; color: #1A1A2E; }
            [data-testid="stSidebar"] p,
            [data-testid="stSidebar"] span,
            [data-testid="stSidebar"] label,
            [data-testid="stSidebar"] h3,
            [data-testid="stSidebar"] strong {
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

    # Init session state
    for key, default in [('authenticated', False), ('role', None),
                          ('username', None), ('raw_username', None), ('client_id', None)]:
        if key not in st.session_state:
            st.session_state[key] = default

    if not st.session_state.authenticated:
        login_page()
        return

    # Timeout de sesion (8 horas)
    if 'last_activity' in st.session_state:
        last_activity = datetime.fromisoformat(st.session_state.last_activity)
        if datetime.now() - last_activity > timedelta(hours=8):
            st.warning("⚠️ Sesion expirada por inactividad.")
            st.session_state.clear()
            st.rerun()
        else:
            st.session_state.last_activity = datetime.now().isoformat()

    client_mgr = ClientManager()
    user_mgr = UserManager()
    role = st.session_state.role

    # ═══ SIDEBAR ═══
    with st.sidebar:
        try:
            st.image("assets/logoEvangelistaCo.png", width=180)
        except Exception:
            pass
        st.markdown("<h3 style='text-align: center; color: #D4AF37;'>Sentinel</h3>",
                    unsafe_allow_html=True)
        st.markdown("---")

        role_emoji = {"Ejecutivo": "👔", "Consultor": "🔬", "Admin": "⚙️"}.get(role, "👤")
        st.info(f"**Usuario:** {st.session_state.username}\n**Rol:** {role_emoji} {role}")

        if st.button("🚪 Cerrar Sesion", use_container_width=True):
            st.session_state.clear()
            st.rerun()

        if role in ["Consultor", "Admin"]:
            st.markdown("---")
            st.page_link("pages/3_⚙️_Admin_Panel.py", label="Panel de Administracion", icon="⚙️")
            st.markdown("---")

        st.markdown("---")
        st.caption("• Pipeline: 4 Fases")
        st.caption("• Motor: Decision Intelligence")
        st.markdown("---")
        st.caption("© 2026 Evangelista & Co.")

    # ═══ SELECTOR DE CLIENTE SEGUN ROL ═══
    selected_client_id = None

    if role == "Ejecutivo":
        selected_client_id = st.session_state.get('client_id')
        if not selected_client_id:
            st.error("Tu usuario no tiene un client_id asignado. Contacta al administrador.")
            st.stop()

    elif role == "Consultor":
        raw_username = st.session_state.get('raw_username', '')
        assigned_clients = user_mgr.get_clients_for_consultant(raw_username)

        if not assigned_clients:
            st.warning("No tienes clientes asignados. Solicita al Admin que te asigne uno.")
            st.stop()

        client_details = {}
        for cid in assigned_clients:
            client = client_mgr.get_client(cid)
            client_details[cid] = f"{client.name} ({cid})" if client else cid

        with st.sidebar:
            selected_client_id = st.selectbox(
                "🏢 Portafolio de Clientes",
                options=list(client_details.keys()),
                format_func=lambda x: client_details.get(x, x)
            )

    elif role == "Admin":
        all_clients = client_mgr.get_all_clients()

        if not all_clients:
            st.warning("No hay clientes registrados. Ve al Admin Panel para crear uno.")
            st.stop()

        client_options = {c.client_id: f"{c.name} ({c.client_id})" for c in all_clients}

        with st.sidebar:
            selected_client_id = st.selectbox(
                "🏢 Seleccionar Cliente",
                options=list(client_options.keys()),
                format_func=lambda x: client_options.get(x, x)
            )
    else:
        st.error("❌ Rol no reconocido.")
        st.stop()

    if not selected_client_id:
        st.error("No se pudo determinar el cliente.")
        st.stop()

    # ═══ VERIFICAR CONFIG DEL CLIENTE ═══
    selected_client = client_mgr.get_client(selected_client_id)

    if not selected_client:
        st.error(f"Cliente '{selected_client_id}' no encontrado en el registro.")
        st.stop()

    if not Path(selected_client.config_file).exists():
        st.error(f"No se encontro el archivo de configuracion: `{selected_client.config_file}`")
        st.info("Ve al Admin Panel > YAML Builder para generar la configuracion de este cliente.")
        st.stop()

    # ═══ CARGAR Y EJECUTAR PIPELINE ═══
    with st.spinner(f"⚙️ Inicializando Decision Pipeline para {selected_client.name}..."):
        pipeline, config = load_pipeline(selected_client_id, selected_client.config_file)

    with st.spinner("🧠 Ejecutando Inteligencia de Decisiones (4 Fases)..."):
        pipeline_results = run_pipeline(pipeline)

    results = pipeline_results['simulation_results']
    stats = pipeline_results['statistics']
    sensitivity = pipeline_results['sensitivity']
    business_narrative = pipeline_results['business_narrative']
    recommendations = pipeline_results['recommendations']

    # Evaluar triggers
    try:
        triggers = pipeline.mc_engine.evaluate_triggers(stats)
    except Exception:
        triggers = []

    # ═══ RENDERIZAR VISTA SEGUN ROL ═══
    with st.sidebar:
        n_sims = config.get('simulation.iterations',
                            config.get('simulation.n_simulations', 10000))
        st.caption(f"• Simulaciones: {n_sims:,}")

    if role == "Ejecutivo":
        vista_ejecutivo(stats, triggers, results, config)
    else:
        vista_consultor(stats, triggers, sensitivity, results, config,
                        business_narrative, recommendations)


if __name__ == "__main__":
    main()
