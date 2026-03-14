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
from src.report_generator import ReportGenerator

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
# EXPORTACIÓN DE REPORTES
# ═══════════════════════════════════════════════════════════════

def render_export_section(pipeline_results: dict, client_name: str, role: str):
    """Sección de exportación PDF/DOCX para Consultores."""
    st.markdown("---")
    st.subheader("📄 Exportar Reporte Corporativo")
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("📄 Generar PDF", use_container_width=True):
            with st.spinner("Generando PDF..."):
                try:
                    gen = ReportGenerator(client_name=client_name, results=pipeline_results)
                    pdf_path = gen.generate_pdf(f"/tmp/Sentinel_{client_name.replace(' ', '_')}.pdf")
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label="⬇️ Descargar PDF",
                            data=f,
                            file_name=f"Sentinel_{client_name}_{datetime.now().strftime('%Y%m%d')}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                        )
                except Exception as e:
                    st.error(f"Error generando PDF: {e}")

    with col2:
        if role in ["Consultor", "Admin"] and st.button("📝 Generar DOCX", use_container_width=True):
            with st.spinner("Generando DOCX..."):
                try:
                    gen = ReportGenerator(client_name=client_name, results=pipeline_results)
                    docx_path = gen.generate_docx(f"/tmp/Sentinel_{client_name.replace(' ', '_')}.docx")
                    with open(docx_path, "rb") as f:
                        st.download_button(
                            label="⬇️ Descargar DOCX",
                            data=f,
                            file_name=f"Sentinel_{client_name}_{datetime.now().strftime('%Y%m%d')}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True,
                        )
                except Exception as e:
                    st.error(f"Error generando DOCX: {e}")


# ═══════════════════════════════════════════════════════════════
# VISTA CONSULTOR V2 — 3 ESCUDOS
# ═══════════════════════════════════════════════════════════════

def vista_consultor_v2(pipeline_results: dict, config):
    """Vista técnica completa con los 3 Escudos y semáforo predictivo."""
    client_name = config.get('client.name', 'Cliente')

    st.markdown(f"""
        <h2 style='color:#d62728;'>🛡️ Decision Intelligence — 3 Escudos</h2>
        <h4 style='color:#666;'>Cliente: {client_name} | {config.get('client.industry','')}</h4>
    """, unsafe_allow_html=True)

    tab_resumen, tab_escudo1, tab_escudo2, tab_escudo3, tab_mc, tab_reportes = st.tabs([
        "🚦 Semáforo",
        "📊 Escudo 1: Proyecciones",
        "⚡ Escudo 2: Riesgo",
        "🎯 Escudo 3: Rescate",
        "🎲 Monte Carlo",
        "📄 Reportes",
    ])

    # ── TAB 1: SEMÁFORO ──────────────────────────────────────────────────────
    with tab_resumen:
        stress = pipeline_results.get('stress_results', {})
        prob   = stress.get('probabilidad_crisis', 0)
        mes_c  = stress.get('mes_critico')

        if prob > 0.30:
            st.error(f"🔴 **ALERTA DE CRISIS** — Probabilidad: {prob:.1%} | Mes crítico: {mes_c}")
        elif prob > 0.15:
            st.warning(f"🟡 **PRECAUCIÓN** — Probabilidad de crisis: {prob:.1%}")
        else:
            st.success(f"🟢 **SITUACIÓN SALUDABLE** — Probabilidad de crisis: {prob:.1%}")

        semaforo = stress.get('semaforo', {})
        if semaforo:
            st.subheader("Semáforo Predictivo — 12 Meses")
            cols = st.columns(12)
            for mes in range(1, 13):
                s = semaforo.get(mes, {})
                emoji = s.get('emoji', '🟢')
                estado = s.get('estado', 'OK')
                prob_m = s.get('prob', 0)
                with cols[mes - 1]:
                    st.metric(f"M{mes}", f"{emoji}", f"{prob_m:.0%}")

        # Métricas rápidas
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        stats = pipeline_results.get('statistics', {})
        col1.metric("P50 Monte Carlo", f"${stats.get('p50', 0):,.0f}")
        col2.metric("Prob. Pérdida",   f"{stats.get('prob_loss', 0):.1%}", delta_color="inverse")
        col3.metric("Prob. Crisis",    f"{prob:.1%}", delta_color="inverse")
        col4.metric("Mes Crítico",     f"Mes {mes_c}" if mes_c else "Ninguno")

    # ── TAB 2: ESCUDO 1 ──────────────────────────────────────────────────────
    with tab_escudo1:
        forecasting = pipeline_results.get('forecasting_results', {})
        if not forecasting or 'error' in forecasting:
            st.warning("Escudo 1 no disponible." + (f" Error: {forecasting.get('error','')}" if forecasting else ""))
        else:
            df_flujo = forecasting.get('flujo_libre_12m')
            if df_flujo is not None and not df_flujo.empty:
                c1, c2 = st.columns(2)
                with c1:
                    fig_i = px.line(
                        df_flujo, x='fecha', y='ingresos',
                        title="Ingresos Proyectados (MXN)",
                        labels={'ingresos': 'Ingresos', 'fecha': 'Fecha'},
                        color_discrete_sequence=['#1f77b4'],
                    )
                    st.plotly_chart(fig_i, use_container_width=True)
                with c2:
                    fig_c = px.line(
                        df_flujo, x='fecha', y='costos',
                        title="Costos Proyectados (MXN)",
                        labels={'costos': 'Costos', 'fecha': 'Fecha'},
                        color_discrete_sequence=['#d62728'],
                    )
                    st.plotly_chart(fig_c, use_container_width=True)

                fig_f = px.bar(
                    df_flujo, x='fecha', y='flujo_libre',
                    title="Flujo Libre Mensual (MXN)",
                    color='flujo_libre',
                    color_continuous_scale=['red', 'yellow', 'green'],
                )
                st.plotly_chart(fig_f, use_container_width=True)

                # Volatilidad TIIE
                df_vol = forecasting.get('volatilidad_tiie')
                if df_vol is not None and not df_vol.empty:
                    st.subheader("Volatilidad TIIE — GARCH(1,1)")
                    fig_v = px.line(
                        df_vol, x='fecha', y='volatilidad_proyectada',
                        title="Volatilidad Proyectada TIIE (%)",
                        color_discrete_sequence=['#ff7f0e'],
                    )
                    st.plotly_chart(fig_v, use_container_width=True)

            estacional = forecasting.get('estacionalidad_detectada', {})
            if estacional.get('detectada'):
                st.info(
                    f"📅 **Estacionalidad detectada** — "
                    f"Mes pico: **{estacional.get('mes_pico')}** | "
                    f"Mes valle: **{estacional.get('mes_valle')}**"
                )

    # ── TAB 3: ESCUDO 2 ──────────────────────────────────────────────────────
    with tab_escudo2:
        stress = pipeline_results.get('stress_results', {})
        if not stress or 'error' in stress:
            st.warning("Escudo 2 no disponible.")
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric("Prob. Quiebra Liquidez", f"{stress.get('probabilidad_crisis', 0):.1%}")
            col2.metric("Mes Crítico", f"Mes {stress.get('mes_critico', 'N/A')}")
            dp = stress.get('default_probability', {})
            col3.metric("Prob. Default Clientes", f"{dp.get('prob_default_media', 0):.1%}")

            st.markdown(f"**Evento Detonante:** {stress.get('evento_detonante', 'N/A')}")

            perc = stress.get('percentiles_caja', {})
            if perc:
                st.subheader("Distribución de Caja Proyectada")
                perc_df = pd.DataFrame([
                    {"Percentil": "P10 (Pesimista)", "Caja": perc.get('p10', 0)},
                    {"Percentil": "P25",              "Caja": perc.get('p25', 0)},
                    {"Percentil": "P50 (Base)",        "Caja": perc.get('p50', 0)},
                    {"Percentil": "P75",              "Caja": perc.get('p75', 0)},
                    {"Percentil": "P90 (Optimista)",  "Caja": perc.get('p90', 0)},
                ])
                fig_perc = px.bar(perc_df, x='Percentil', y='Caja',
                                  title="Escenarios de Caja al Final del Horizonte",
                                  color='Caja', color_continuous_scale='RdYlGn')
                st.plotly_chart(fig_perc, use_container_width=True)

            top = stress.get('top_escenarios_riesgo', [])
            if top:
                st.subheader("Top 5 Escenarios de Mayor Riesgo")
                st.dataframe(pd.DataFrame(top), use_container_width=True)

    # ── TAB 4: ESCUDO 3 ──────────────────────────────────────────────────────
    with tab_escudo3:
        opt = pipeline_results.get('optimization_results', {})
        if not opt or 'error' in opt:
            st.warning("Escudo 3 no disponible.")
        elif not opt.get('crisis_detectada'):
            st.success(f"✅ {opt.get('mensaje', 'No se requiere plan de rescate.')}")
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric("Capital Total a Liberar", f"${opt.get('capital_total_liberado', 0):,.0f} MXN")
            col2.metric("ROI del Plan", f"{opt.get('roi_estimado', 0)}x")
            col3.metric("Mes Crítico", f"Mes {opt.get('mes_critico', 'N/A')}")

            st.markdown(f"**Evento Detonante:** {opt.get('evento_detonante', 'N/A')}")
            st.markdown("---")

            for i, est in enumerate(opt.get('estrategias', []), 1):
                with st.expander(
                    f"Estrategia #{i}: {est.get('titulo', '')} — ${est.get('capital_liberado', 0):,.0f} MXN",
                    expanded=(i == 1)
                ):
                    col_a, col_b = st.columns([2, 1])
                    with col_a:
                        st.write(f"**Acción:** {est.get('accion', '')}")
                        st.write(est.get('descripcion', ''))
                    with col_b:
                        st.metric("Capital Liberado", f"${est.get('capital_liberado', 0):,.0f}")
                        st.caption(f"⏰ {est.get('deadline', '')}")

            oc = opt.get('optimizacion_conjunta', {})
            if oc and 'liquidez_total' in oc:
                st.markdown("---")
                st.subheader("Optimización Conjunta (CVXPY)")
                oc_df = pd.DataFrame([{
                    "OPEX Reducción":  f"{oc.get('opex_reduccion', 0):.1%}",
                    "Días Diferimiento": f"{oc.get('dias_diferimiento', 0):.0f}",
                    "Factoraje":       f"{oc.get('fraccion_factoraje', 0):.0%}",
                    "Liquidez Total":  f"${oc.get('liquidez_total', 0):,.0f}",
                    "Impacto Operativo": f"{oc.get('impacto_operativo', 0):.0%}",
                }])
                st.dataframe(oc_df, use_container_width=True)

    # ── TAB 5: MONTE CARLO (vista original) ──────────────────────────────────
    with tab_mc:
        stats       = pipeline_results.get('statistics', {})
        sensitivity = pipeline_results.get('sensitivity', pd.DataFrame())
        results_df  = pipeline_results.get('simulation_results', pd.DataFrame())
        narrative   = pipeline_results.get('business_narrative', {})
        recs        = pipeline_results.get('recommendations', [])

        if stats:
            col1, col2, col3 = st.columns(3)
            col1.plotly_chart(render_gauge(stats['prob_loss'], "Prob. Pérdida", 1.0,
                              config.get('thresholds.critical_loss_prob', 0.25)), use_container_width=True)
            col2.plotly_chart(render_gauge(abs(stats['var_95']), "VaR 95%",
                              abs(stats['var_95']) * 2, abs(stats['var_95']) * 0.8), use_container_width=True)
            col3.plotly_chart(render_gauge(stats['p50'], "P50",
                              stats['p90'], stats['mean'] * 0.5), use_container_width=True)

        if isinstance(narrative, dict) and narrative.get('executive_summary'):
            st.markdown("---")
            st.subheader("Traducción Ejecutiva")
            st.info(narrative.get('confidence_level', ''))
            st.markdown(narrative.get('executive_summary', ''))

        if not sensitivity.empty:
            st.markdown("---")
            st.plotly_chart(render_tornado_chart(sensitivity), use_container_width=True)

        if results_df is not None and not (isinstance(results_df, pd.DataFrame) and results_df.empty):
            st.markdown("---")
            st.plotly_chart(render_distribution_chart(results_df, stats), use_container_width=True)

        if recs:
            st.markdown("---")
            st.subheader("Inteligencia de Decisiones")
            for i, rec in enumerate(recs, 1):
                with st.expander(f"#{i} {rec['title']} (Prioridad {rec['priority']})", expanded=(rec['priority'] == 1)):
                    st.markdown(f"**Descripción:** {rec['description']}")
                    for act in rec.get('actions', []):
                        st.write(f"- Paso {act['step']}: {act['action']} *(Responsable: {act['responsible']})*")

    # ── TAB 6: REPORTES ──────────────────────────────────────────────────────
    with tab_reportes:
        render_export_section(pipeline_results, client_name, "Consultor")


def vista_ejecutivo_v2(pipeline_results: dict, config):
    """Vista ejecutiva simplificada: semáforo + alertas clave + exportar PDF."""
    client_name = config.get('client.name', 'Cliente')
    stats  = pipeline_results.get('statistics', {})
    stress = pipeline_results.get('stress_results', {})
    prob   = stress.get('probabilidad_crisis', 0)
    mes_c  = stress.get('mes_critico')

    st.markdown(f"<h2 style='color:#1f77b4;'>📊 Dashboard Ejecutivo — {client_name}</h2>",
                unsafe_allow_html=True)

    # Estado general
    if prob > 0.30:
        st.error(f"🔴 **ALERTA:** Crisis proyectada con {prob:.0%} de probabilidad en mes {mes_c}. Contacte a su consultor.")
    elif prob > 0.15:
        st.warning(f"🟡 **PRECAUCIÓN:** Señales de riesgo moderado ({prob:.0%}). Revisar con su equipo.")
    else:
        st.success("🟢 **TODO EN ORDEN:** No se detectan crisis en el horizonte de 12 meses.")

    # KPIs
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Resultado Esperado",  f"${stats.get('p50', 0):,.0f}", "Mediana (P50)")
    col2.metric("Escenario Optimista", f"${stats.get('p90', 0):,.0f}", "P90")
    col3.metric("Escenario Pesimista", f"${stats.get('p10', 0):,.0f}", "P10", delta_color="inverse")
    col4.metric("Riesgo de Pérdida",   f"{stats.get('prob_loss', 0):.1%}", delta_color="inverse")

    # Semáforo (solo primeros 6 meses para ejecutivo)
    semaforo = stress.get('semaforo', {})
    if semaforo:
        st.markdown("---")
        st.subheader("🚦 Semáforo — Próximos 6 Meses")
        cols = st.columns(6)
        for mes in range(1, 7):
            s = semaforo.get(mes, {})
            with cols[mes - 1]:
                st.metric(f"Mes {mes}", s.get('emoji', '🟢'), s.get('estado', 'OK'))

    # Distribución
    results_df = pipeline_results.get('simulation_results')
    if results_df is not None and stats:
        st.markdown("---")
        st.plotly_chart(render_distribution_chart(results_df, stats), use_container_width=True)

    # Exportar PDF (solo PDF para ejecutivo)
    st.markdown("---")
    render_export_section(pipeline_results, client_name, "Ejecutivo")


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
        st.markdown("**⚙️ Sentinel V2 — 3 Escudos:**")
        st.caption("🎯 Escudo 1: Proyecciones (Prophet)")
        st.caption("⚡ Escudo 2: Estrés (SimPy + PyMC)")
        st.caption("🔬 Escudo 3: Rescate (CVXPY)")
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
            vista_ejecutivo_v2(pipeline_results, config)
        elif st.session_state.role in ["Consultor", "Admin"]:
            vista_consultor_v2(pipeline_results, config)
        else:
            st.error("❌ Rol no reconocido")
            
    except FileNotFoundError as e:
        st.error(f"❌ Error Estructural: No se encontró el archivo físico del cliente. {str(e)}")
        st.info("Por favor, asegúrate de generar el YAML en el Panel de Administración.")

if __name__ == "__main__":
    main()