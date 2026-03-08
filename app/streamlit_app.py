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

    groq_api_key = st.secrets.get("GROQ_API_KEY") if hasattr(st, "secrets") else None
    pipeline = DecisionPipeline(config, supabase_creds, groq_api_key=groq_api_key)
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

def vista_ejecutivo(stats: Dict, triggers: List[Dict], results: pd.DataFrame, config,
                    consultant_name: str = None, client_id: str = None,
                    strategic_analysis: Dict = None):
    from src.executive_dashboard_engine import ExecutiveDashboardEngine

    client_name = config.get('client.name', 'Cliente')
    st.markdown(f"<h2 style='color: #1f77b4;'>📊 Dashboard Ejecutivo - {client_name}</h2>",
                unsafe_allow_html=True)
    st.markdown("---")

    # ── BUSINESS HEALTH SCORE ─────────────────────────────────────────────
    mc_input = {'statistics': stats}
    engine = ExecutiveDashboardEngine(mc_input, strategic_analysis or {}, config)
    dashboard = engine.generate()

    score = dashboard['health_score']
    level = dashboard['health_level']
    briefing = dashboard['executive_briefing']
    exec_kpis = dashboard['executive_kpis']
    highlights = dashboard['strategic_highlights']

    col_score, col_brief = st.columns([1, 2])
    with col_score:
        st.markdown(
            f"""
            <div style='text-align:center; padding:20px; border-radius:12px;
                        background:{level["color"]}22; border:3px solid {level["color"]};'>
                <div style='font-size:64px; font-weight:bold; color:{level["color"]};'>{score}</div>
                <div style='font-size:18px; font-weight:bold; color:{level["color"]};'>{level["label"]}</div>
                <div style='font-size:12px; color:#666; margin-top:4px;'>Business Health Score</div>
                <div style='font-size:12px; color:#555; margin-top:8px;'>{level["message"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_brief:
        st.markdown("**Resumen Ejecutivo**")
        for i, point in enumerate(briefing, 1):
            st.markdown(f"{i}. {point}")

        if highlights:
            st.markdown("**Acciones Recomendadas**")
            for h in highlights:
                st.markdown(f"{h['icon']} {h['text']}")

    st.markdown("---")

    # ── EXECUTIVE KPIs CON SEMAFORO ───────────────────────────────────────
    st.subheader("📋 Indicadores Ejecutivos")

    STATUS_COLORS = {'green': '#27AE60', 'yellow': '#F39C12', 'red': '#E74C3C'}
    STATUS_ICONS  = {'green': '🟢', 'yellow': '🟡', 'red': '🔴'}

    kpi_cols = st.columns(3)
    for idx, kpi in enumerate(exec_kpis):
        col = kpi_cols[idx % 3]
        with col:
            color = STATUS_COLORS.get(kpi['status'], '#999')
            icon_s = STATUS_ICONS.get(kpi['status'], '⚪')
            st.markdown(
                f"""
                <div style='border-left:4px solid {color}; padding:10px 14px;
                            margin-bottom:10px; background:#F8F9FA; border-radius:4px;'>
                    <div style='font-size:13px; color:#555;'>{kpi["icon"]} {kpi["name"]} {icon_s}</div>
                    <div style='font-size:22px; font-weight:bold; color:{color};'>{kpi["value"]}</div>
                    <div style='font-size:11px; color:#888;'>{kpi["detail"]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

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
    st.info("""
**💡 Nota para Ejecutivos:**

Está visualizando el diagnóstico de riesgo de su operación basado en simulación Monte Carlo.

Para acceder al **plan de acción detallado** con estrategias de mitigación, análisis de ROI
y recomendaciones priorizadas, contacte a su consultor asignado.

**Su consultor tiene acceso a:**
- ✅ Recomendaciones prescriptivas con priorización
- ✅ Pasos de acción específicos
- ✅ Análisis de impacto financiero (ROI, payback)
- ✅ Análisis técnico de sensibilidad de variables
    """)
    if consultant_name:
        st.success(f"👤 **Consultor asignado:** {consultant_name}")
    else:
        st.warning("⚠️ No tiene consultor asignado. Contacte al administrador.")

    st.markdown("---")
    st.subheader("📊 Distribucion de Resultados")
    st.plotly_chart(render_distribution_chart(results, stats), use_container_width=True)


def vista_consultor(stats: Dict, triggers: List[Dict], sensitivity: pd.DataFrame,
                    results: pd.DataFrame, config, business_narrative: str,
                    recommendations: List[Dict], strategic_analysis: Dict = None):
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

    # ── STRATEGIC ADVISOR (FASE 5) ────────────────────────────────────────
    if strategic_analysis and 'error' not in strategic_analysis:
        st.markdown("---")
        st.subheader("🧠 Strategic Advisor — Analisis Estrategico (Fase 5)")

        summary = strategic_analysis.get('executive_summary', {})
        if summary:
            risk_colors = {
                'LOW': 'success', 'MODERATE': 'warning',
                'HIGH': 'error', 'CRITICAL': 'error'
            }
            risk_profile = summary.get('risk_profile', 'MODERATE')
            render_fn = getattr(st, risk_colors.get(risk_profile, 'info'))
            render_fn(f"**{risk_profile}** — {summary.get('headline', '')}")
            st.markdown(summary.get('key_message', ''))

        sa_tabs = st.tabs(["🎯 Recomendaciones", "⚠️ Riesgos", "💡 Oportunidades", "📅 Proximos Pasos"])

        with sa_tabs[0]:
            recs = strategic_analysis.get('strategic_recommendations', [])
            if recs:
                for rec in recs:
                    horizon = rec.get('implementation_horizon', '')
                    confidence = rec.get('confidence', '')
                    with st.expander(
                        f"#{rec.get('priority', '?')} — {rec.get('title', 'Sin titulo')} "
                        f"| {horizon} | Confianza: {confidence}",
                        expanded=(rec.get('priority') == 1)
                    ):
                        st.markdown(f"**Fundamento:** {rec.get('rationale', '')}")
                        st.markdown(f"**Impacto esperado:** {rec.get('expected_impact', '')}")
                        actions = rec.get('action_items', [])
                        if actions:
                            st.markdown("**Plan de accion:**")
                            for a in actions:
                                st.write(f"  • {a}")
            else:
                st.info("Sin recomendaciones estrategicas generadas.")

        with sa_tabs[1]:
            risk_analysis = strategic_analysis.get('risk_analysis', {})
            primary_risks = risk_analysis.get('primary_risks', [])
            if primary_risks:
                risk_data = []
                for r in primary_risks:
                    risk_data.append({
                        'Riesgo': r.get('risk', ''),
                        'Probabilidad': r.get('probability', ''),
                        'Impacto': r.get('impact', ''),
                        'Mitigacion': r.get('mitigation', ''),
                    })
                st.dataframe(pd.DataFrame(risk_data), use_container_width=True, hide_index=True)
            scenario = risk_analysis.get('scenario_analysis', {})
            if scenario:
                st.markdown("**Analisis de Escenarios:**")
                col1, col2, col3 = st.columns(3)
                col1.error(f"**Pesimista:**\n{scenario.get('bear_case', '')}")
                col2.info(f"**Base:**\n{scenario.get('base_case', '')}")
                col3.success(f"**Optimista:**\n{scenario.get('bull_case', '')}")

        with sa_tabs[2]:
            opps = strategic_analysis.get('opportunity_analysis', {})
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**Victorias rapidas (30d)**")
                for qw in opps.get('quick_wins', []):
                    st.write(f"  ✅ {qw}")
            with col2:
                st.markdown("**Apuestas estrategicas**")
                for sb in opps.get('strategic_bets', []):
                    st.write(f"  🎲 {sb}")
            with col3:
                st.markdown("**Movimientos defensivos**")
                for dm in opps.get('defensive_moves', []):
                    st.write(f"  🛡️ {dm}")

        with sa_tabs[3]:
            nxt = strategic_analysis.get('next_steps', {})
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**Esta semana**")
                for s in nxt.get('this_week', []):
                    st.write(f"  • {s}")
            with col2:
                st.markdown("**Este mes**")
                for s in nxt.get('this_month', []):
                    st.write(f"  • {s}")
            with col3:
                st.markdown("**Este trimestre**")
                for s in nxt.get('this_quarter', []):
                    st.write(f"  • {s}")

    elif strategic_analysis and 'error' in strategic_analysis:
        st.markdown("---")
        st.warning(f"⚠️ Strategic Advisor no disponible: {strategic_analysis['error']}")

    # ── KPIs POR METODOLOGÍA ──────────────────────────────────────────────
    st.markdown("---")
    try:
        from src.projection_engine import ProjectionEngine
        methodology = config.get('kpi_methodology', 'operational')
        proj = ProjectionEngine({'statistics': stats}, methodology=methodology)
        kpis = proj.generate_kpis_by_methodology(industry=industry)
        st.subheader(f"📐 KPIs — {kpis['methodology']}")

        if methodology == 'okr':
            for obj in kpis.get('objectives', []):
                st.markdown(f"**🎯 {obj['objective']}**")
                for kr in obj.get('key_results', []):
                    status_icon = '🟢' if kr['status'] == 'on_track' else '🔴'
                    col1, col2, col3 = st.columns(3)
                    col1.write(f"{status_icon} {kr['kr']}")
                    col2.metric("Actual", kr['current'])
                    col3.metric("Target", kr['target'])

        elif methodology == 'bsc':
            tabs_bsc = st.tabs([p['name'] for p in kpis['perspectives'].values()])
            for tab, perspective in zip(tabs_bsc, kpis['perspectives'].values()):
                with tab:
                    for kpi in perspective['kpis']:
                        col1, col2 = st.columns(2)
                        col1.metric(kpi['kpi'], kpi['value'])
                        col2.write(f"**Interpretación:** {kpi['interpretation']}")

        elif methodology == 'smart':
            for kpi in kpis.get('kpis', []):
                status_icon = '🟢' if kpi['status'] == 'on_track' else '🔴'
                with st.expander(f"{status_icon} {kpi['name']} — {kpi['current_value']}"):
                    st.write(f"**S — Específico:** {kpi['specific']}")
                    st.write(f"**M — Medible:** {kpi['measurable']}")
                    st.write(f"**A — Alcanzable:** {kpi['achievable']}")
                    st.write(f"**R — Relevante:** {kpi['relevant']}")
                    st.write(f"**T — Tiempo:** {kpi['time_bound']}")

        elif methodology == 'north_star':
            ns = kpis.get('north_star_metric', {})
            st.metric(f"⭐ {ns.get('name', '')}", ns.get('value', ''))
            st.caption(ns.get('definition', ''))
            st.markdown("**Input Metrics:**")
            for im in kpis.get('input_metrics', []):
                col1, col2 = st.columns(2)
                col1.metric(im['name'], im['value'], f"Impacto: {im['impact_on_north_star']}")
                col2.write(f"**Palanca:** {im['lever']}")

        else:  # operational
            for cat in kpis.get('categories', {}).values():
                st.markdown(f"**{cat['name']}**")
                rows = []
                for m in cat.get('metrics', []):
                    row = {'KPI': m['metric'], 'Valor': m['value']}
                    if 'interpretation' in m:
                        row['Interpretacion'] = m['interpretation']
                    if 'unit' in m:
                        row['Unidad'] = m['unit']
                    rows.append(row)
                if rows:
                    import pandas as _pd
                    st.dataframe(_pd.DataFrame(rows), use_container_width=True, hide_index=True)

    except Exception as e:
        st.warning(f"⚠️ No se pudieron generar KPIs: {e}")


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
        st.caption("• Pipeline: 5 Fases")
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

    with st.spinner("🧠 Ejecutando Inteligencia de Decisiones (5 Fases)..."):
        pipeline_results = run_pipeline(pipeline)

    results = pipeline_results['simulation_results']
    stats = pipeline_results['statistics']
    sensitivity = pipeline_results['sensitivity']
    business_narrative = pipeline_results['business_narrative']
    recommendations = pipeline_results['recommendations']
    strategic_analysis = pipeline_results.get('strategic_analysis', {})

    # Sanity check de escala antes de renderizar
    mean_val = stats.get('mean', 0)
    if abs(mean_val) > 1_000_000_000:
        st.error(
            f"⚠️ **Error de escala en el modelo:** El resultado esperado es "
            f"${mean_val:,.0f}, lo que indica un problema en el `business_model` del YAML. "
            "Probable causa: las variables representan totales mensuales pero el modelo "
            "las multiplica por un volumen (ej. `× 1000`). "
            "Ve al **Admin Panel → YAML Builder** y regenera la configuración del cliente."
        )

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
        consultant_name = user_mgr.get_consultant_for_client(selected_client_id)
        vista_ejecutivo(stats, triggers, results, config,
                        consultant_name=consultant_name, client_id=selected_client_id,
                        strategic_analysis=strategic_analysis)
    else:
        vista_consultor(stats, triggers, sensitivity, results, config,
                        business_narrative, recommendations, strategic_analysis)


if __name__ == "__main__":
    main()
