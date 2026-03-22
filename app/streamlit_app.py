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

from supabase import create_client, Client

from src.user_manager import UserManager
from src.configuration_manager import ConfigurationManager
from src.decision_pipeline import DecisionPipeline
from src.report_generator import ReportGenerator

# ──────────────────────────────────────────────────────────────
# UI/UX Enhancement - Evangelista & Co
from app.config.custom_css import get_custom_css
from app.config.plotly_theme import get_evangelista_theme
# ──────────────────────────────────────────────────────────────

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE PÁGINA
# ═══════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Sentinel - Decision Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ──────────────────────────────────────────────────────────────
# Aplicar diseño Evangelista
st.markdown(get_custom_css(), unsafe_allow_html=True)
get_evangelista_theme()
# ──────────────────────────────────────────────────────────────

# Header con logo Evangelista
col1, col2 = st.columns([1, 4])
with col1:
    st.image("assets/logoEvangelistaCo.png", width=60)
with col2:
    st.markdown("<h1 style='margin-top: 0;'>Sentinel</h1>", unsafe_allow_html=True)
    st.caption("Decision Intelligence Platform • Evangelista & Co")

st.markdown("<br>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# FUNCIONES DE NEGOCIO (PIPELINE)
# ═══════════════════════════════════════════════════════════════

@st.cache_resource
def get_supabase_client() -> Client | None:
    """Conexión global al Data Mesh. Zero-crash: retorna None si faltan credenciales."""
    url = os.getenv("SUPABASE_URL") or (st.secrets.get("SUPABASE_URL") if hasattr(st, "secrets") else None)
    key = os.getenv("SUPABASE_KEY") or (st.secrets.get("SUPABASE_KEY") if hasattr(st, "secrets") else None)
    if url and key:
        try:
            return create_client(url, key)
        except Exception:
            return None
    return None


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
                st.session_state.user_login = username.strip().lower()  # FIX: store raw login for Supabase lookup
                st.session_state.user_email = user.email
                st.session_state.client_id = getattr(user, 'client_id', None)
                # FIX: user_manager.py lee 'cliente_id' pero la columna real es 'client_id'
                # Si client_id sigue vacío (bug del user_manager), hacemos lookup directo.
                if not st.session_state.client_id and user.role == "Ejecutivo":
                    try:
                        _sb = get_supabase_client()
                        if _sb:
                            _res = _sb.table("saas_users").select("client_id").eq("username", username.strip().lower()).execute()
                            if _res.data:
                                st.session_state.client_id = _res.data[0].get("client_id")
                    except Exception:
                        pass
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
        with st.expander("ℹ️ Guía de Lectura — Sistema de Alertas Predictivas", expanded=False):
            st.markdown("""
### 🎯 Propósito
Vista ejecutiva unificada: consolida los outputs de los 3 Escudos en un semáforo de
12 meses. Responde una pregunta: *¿en qué mes el negocio enfrenta riesgo crítico de
iliquidez y qué tan probable es?*

### 🔧 Metodología
El semáforo deriva su señal del **Escudo 2 (Stress Testing)**:
- Corre **10,000 escenarios de Montecarlo macroeconómico** con 6 variables correlacionadas
- Para cada mes $m$, calcula la fracción de escenarios donde `caja ≤ 0`
- Esa fracción es la `prob_crisis[m]`

**Umbrales institucionales:**
| Semáforo | Prob. de crisis | Interpretación |
|---|---|---|
| 🟢 Verde | < 15% | Operación saludable, sin acción urgente |
| 🟡 Amarillo | 15% – 30% | Señales de alerta, revisar con equipo |
| 🔴 Rojo | > 30% | Crisis proyectada, activar plan de rescate |

### 📊 Cómo interpretar los KPIs
- **P50 Monte Carlo:** Resultado más probable del negocio en el horizonte completo.
  Si es negativo, más del 50% de los escenarios simulados terminan en pérdida.
- **Prob. Pérdida:** Fracción de las 10,000 simulaciones con resultado neto < 0.
- **Mes Crítico:** Primer mes donde la probabilidad de caja = $0 supera el umbral rojo.

### 💡 Criterio de Acción
```
Prob. crisis < 15%  →  Monitoreo mensual estándar
Prob. crisis 15-30% →  Reunión de riesgo en 72 horas
Prob. crisis > 30%  →  Activar Escudo 3 (Bisturí) de inmediato
```
            """)
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
        with st.expander("ℹ️ El Radar — Motor de Proyección Temporal", expanded=False):
            st.markdown("""
### 🎯 Propósito
Proyecta ingresos, costos y flujo libre a **12 meses** usando series de tiempo.
El Radar responde: *¿hacia dónde va la empresa si continúa la tendencia actual?*

### 🔧 Modelos (en orden de preferencia)

**Ingresos y Costos — Selección automática:**
| Condición | Modelo seleccionado | Fortaleza |
|---|---|---|
| ≥ 12 meses de historia | **Facebook Prophet** | Captura tendencia + estacionalidad anual |
| < 12 meses de historia | **Darts ExponentialSmoothing** | Suavizado triple Holt-Winters, robusto a outliers |
| Datos insuficientes | **Darts NaiveDrift** | Proyección lineal de última tendencia |

**Volatilidad de TIIE — Siempre:**
- **ARCH GARCH(1,1):** Modelo de heterocedasticidad condicional. Captura que la
  volatilidad de tasas se agrupa en períodos (`clustering`). Parámetros: ω, α, β
  calibrados sobre los últimos 24 meses de datos BANXICO (serie SF43878).

### 📊 Cómo interpretar los gráficos

**Ingresos / Costos Proyectados:**
- La línea es el escenario base (P50 del modelo).
- Tendencia ascendente en costos sin correspondencia en ingresos → alerta de compresión de margen.

**Flujo Libre Mensual (barras):**
- 🟢 Verde = mes con flujo positivo (el negocio genera caja).
- 🔴 Rojo = mes con flujo negativo (el negocio consume caja).
- Un patrón alternado indica estacionalidad pronunciada → requiere línea de crédito revolvente.

**Volatilidad TIIE:**
- Valores > 0.5% diario indican ambiente de tasas turbulento.
- Impacta directamente el costo de deuda variable y los flujos descontados.

### 💡 Señales de Acción
```
Costos crecen > ingresos por 3+ meses  →  Revisión inmediata de estructura de costos
Flujo libre negativo en temporada alta →  El problema es estructural, no estacional
TIIE vol > 0.8%                         →  Considerar tasa fija en refinanciamiento
```

### ⚠️ Limitaciones
- Prophet requiere **≥ 12 observaciones** con estacionalidad detectable.
- Si la tabla `saas_variables_exogenas` está vacía, el modelo opera con datos dummy.
  Ejecuta `scripts/load_banxico_data.py` para cargar datos reales de BANXICO.
            """)
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
        with st.expander("ℹ️ La Trituradora — Motor de Estrés Sistémico", expanded=False):
            st.markdown("""
### 🎯 Propósito
Simula **10,000 escenarios de crisis macroeconómica simultánea** y mide cuántos
terminan en quiebra de liquidez. Responde: *¿qué tan vulnerable es este negocio
a un shock externo como el de 2008, 2020 o una devaluación del peso?*

### 🔧 Modelos

**1. Cópula Gaussiana (Riskfolio-Lib / Cholesky)**

Genera variables macroeconómicas correlacionadas entre sí, tal como ocurren en la
realidad. Las 6 variables simuladas son:

| Variable | Descripción | Fuente |
|---|---|---|
| `TIIE` | Tasa interbancaria 28 días | BANXICO SF43878 |
| `USD_MXN` | Tipo de cambio FIX | BANXICO SF43718 |
| `INPC` | Inflación general | BANXICO SP1 |
| `IGAE` | Actividad económica | INEGI |
| `SOBRECOSTO` | Sobre-costo en materiales | Histórico cliente |
| `RETRASO_COBRO` | Días promedio de cobro | CxC del cliente |

Mecanismo de correlación (por ejemplo, TIIE ↑ → USD ↑, correlación ρ = 0.7):
```
1. Generar u₁, u₂ ~ Uniforme(0,1)
2. Aplicar cópula Gaussiana con matriz Σ (Cholesky decomposition)
3. Invertir CDF normal → TIIE y USD_MXN correlacionados
Resultado: shocks realistas, no independientes
```

**2. Simulación SimPy (Event-Driven Cash Flow)**

Cadena de pagos discreta mes a mes:
```
Cobro de CxC → Pago a proveedores → Saldo de caja → ¿Caja ≤ 0? → Crisis
```
Detecta el *mes exacto* de quiebre de liquidez en cada uno de los 10,000 escenarios.

**3. PyMC — Probabilidad Bayesiana de Default**

Modelo Beta-Binomial: infiere la probabilidad de que un cliente no pague basándose
en los días promedio de retraso histórico. Muestrea 500 draws con 1 cadena MCMC.
Salida: distribución posterior de la tasa de default, no un número puntual.

### 📊 Cómo interpretar los resultados

**Prob. Quiebra de Liquidez:** Fracción de los 10,000 escenarios donde caja = $0.
Umbral de acción: >15% = precaución, >30% = activar Escudo 3.

**Distribución de Caja (barras P10-P90):** El rango P10–P90 indica la amplitud
del riesgo. Un rango estrecho = negocio predecible. Un rango amplio = alta incertidumbre.

**Top 5 Escenarios de Mayor Riesgo:** Los peores escenarios ordenados por caja final.
Úsalos para el stress test de gobernanza: *"¿puede el negocio sobrevivir este escenario?"*

### 💡 Criterio de Acción
```
Prob. default clientes > 20%  →  Revisar política de CxC, solicitar anticipos
Mes crítico ≤ 3               →  Crisis inminente, convocar Comité de Crisis
P10 caja < -$1M               →  Gestionar línea de crédito preventiva HOY
```
            """)
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
        with st.expander("ℹ️ El Bisturí — Motor de Optimización Quirúrgica", expanded=False):
            st.markdown("""
### 🎯 Propósito
Se activa **solo si el Escudo 2 detecta crisis** (prob > 15%). Prescribe el plan
de rescate óptimo minimizando impacto operativo. Responde: *¿cuál es la mínima
intervención quirúrgica necesaria para reestablecer la liquidez?*

### 🔧 Modelos — CVXPY (Optimización Convexa)

Tres palancas de capital independientes, cada una como problema de optimización:

| Palanca | Variable | Rango | Costo |
|---|---|---|---|
| **Reducción OPEX** | `x` ∈ [0%, 20%] | Recorte de costos fijos | Impacto operativo |
| **Diferimiento de pagos** | `d` ∈ [0, 45 días] | Negociación con proveedores | Relación comercial |
| **Factoraje de CxC** | `f` ∈ [0%, 60%] | Adelanto de cuentas por cobrar | 1.5%/mes de comisión |

**Optimización conjunta (Joint Optimization):**
```
Maximizar: capital_liberado(x, d, f)
Sujeto a:  impacto_operativo(x, d, f) ≤ 50%
           x ≤ 0.20, d ≤ 45, f ≤ 0.60
```
Solucionado con CVXPY usando solver SCS (cónico de segundo orden). Converge en < 100ms.

### 📊 Cómo interpretar los resultados

**Capital Total a Liberar:** Suma de caja liberada por las 3 palancas combinadas.
Debe superar el déficit proyectado por el Escudo 2.

**ROI del Plan:** `(ahorro_crisis_evitada) / (costo_implementación)`.
Un ROI > 3x justifica ejecución inmediata.

**Estrategias en orden:** Ordenadas de mayor a menor impacto con menor costo operativo.
Ejecutar en secuencia, no en paralelo, para evitar disrupciones simultáneas.

**Tabla de Optimización Conjunta:** El punto óptimo matemático entre las 3 palancas.
Si `impacto_operativo` > 40%, discutir con equipo directivo antes de ejecutar.

### ⚠️ Condición de Activación
```
Escudo 2: prob_crisis < 15%  →  Escudo 3 muestra "✅ Sin necesidad de rescate"
Escudo 2: prob_crisis ≥ 15%  →  Escudo 3 genera plan de intervención quirúrgica
```

### 💡 Protocolo de Ejecución
```
Semana 1:  Ejecutar reducción OPEX (acción interna, sin dependencia externa)
Semana 2:  Negociar diferimiento con top-3 proveedores por monto
Semana 3:  Activar línea de factoraje con institución bancaria
Semana 4:  Medir resultado: ¿caja proyectada ≥ $0 en mes crítico?
```
            """)
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
        with st.expander("ℹ️ El Motor Base — Monte Carlo Cuántico", expanded=False):
            st.markdown("""
### 🎯 Propósito
Núcleo matemático de Sentinel. Simula **10,000 trayectorias posibles del negocio**
usando las distribuciones de probabilidad calibradas en el YAML del cliente.
Responde: *¿cuál es la distribución completa de resultados posibles, no solo el promedio?*

### 🔧 Metodología

**Proceso de simulación (por iteración):**
```
Para i = 1 … 10,000:
  1. Muestrear variables según su distribución (YAML: media, desviación, tipo)
  2. Calcular resultado = modelo_dinamico(variables, parámetros)
  3. Almacenar resultado[i]
Resultado: distribución empírica de 10,000 outcomes
```

**Análisis de Sensibilidad (Tornado):**
- Método: **Correlación de Spearman** entre cada variable y el resultado final.
- Importancia = |ρ_Spearman|² → fracción de varianza explicada.
- La barra más larga = la variable que más mueve el resultado. Allí está el riesgo principal.

**Traducción Ejecutiva (Business Translator):**
Convierte estadísticas crudas en narrativa de negocios accionable usando reglas
de umbral: prob_loss, VaR 95%, rango intercuartil P25–P75.

### 📊 Cómo interpretar los indicadores

**Gauge: Probabilidad de Pérdida**
- < 10%: Negocio robusto. Sin acción requerida.
- 10–25%: Zona amarilla. Monitorear mensualmente.
- > 25%: Zona crítica. Revisar supuestos del YAML y estructura de costos.

**Gauge: VaR 95% (Pérdida Máxima)**
- Interpretación: *"En el 5% de los peores escenarios, la pérdida supera este monto."*
- Compara contra reservas de caja del cliente. Si VaR > reservas → riesgo de insolvencia.

**Histograma de Distribución:**
- Cola izquierda larga = riesgo asimétrico (pérdidas potencialmente ilimitadas).
- Distribución bimodal = el negocio tiene dos regímenes: ganancia o pérdida clara.
- Línea P50 muy a la derecha de la media = sesgo positivo, buenos escenarios posibles.

### 💡 Checklist de Sanidad del Modelo
```
✅ P50 es razonable para la industria
✅ P90 - P10 < 3x la media (no hay dispersión explosiva)
✅ Variable #1 en tornado corresponde al mayor riesgo operativo conocido
✅ Prob. pérdida < 50% (si > 50%, revisar supuestos del YAML)
```

### ⚠️ Si P50 es negativo pero P90 es positivo
El negocio tiene escenarios ganadores pero son minoría. Busca el "switch":
la variable donde un cambio del +10% convierte pérdida en ganancia. Ese es el
KPI de gestión prioritario para el cliente.
            """)
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
# VISTA CLIENTE (EJECUTIVO) — Semáforo + Reportes
# ═══════════════════════════════════════════════════════════════

def vista_cliente(pipeline_results: dict, config):
    """Vista restringida para usuarios Ejecutivo (clientes).
    Muestra únicamente: semáforo de 12 meses + exportación de reportes.
    Zero-Crash: maneja dict vacíos de cualquier escudo fallido."""
    client_name = config.get('client.name', 'Cliente')
    stats  = pipeline_results.get('statistics', {})
    stress = pipeline_results.get('stress_results', {})
    prob   = stress.get('probabilidad_crisis', 0)
    mes_c  = stress.get('mes_critico')

    st.markdown(
        f"<h2 style='color:#1A1A2E;'>🏢 Portal — {client_name}</h2>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    tab_sem, tab_rep = st.tabs(["🚦 Semáforo", "📄 Reportes"])

    # ── Tab 1: Semáforo ───────────────────────────────────────────────────────
    with tab_sem:
        st.subheader("🚦 Estado General del Negocio")

        # Banner de alerta ejecutiva
        if prob > 0.30:
            st.error(
                f"🔴 **ALERTA CRÍTICA:** Crisis proyectada con **{prob:.0%}** de probabilidad "
                f"en el mes {mes_c}. Contacte a su consultor estratégico de inmediato."
            )
        elif prob > 0.15:
            st.warning(
                f"🟡 **PRECAUCIÓN:** Señales de riesgo moderado (**{prob:.0%}**). "
                "Se recomienda revisar los indicadores con su equipo."
            )
        else:
            st.success("🟢 **TODO EN ORDEN:** No se detectan crisis en el horizonte de 12 meses.")

        # KPIs ejecutivos
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Resultado Esperado",  f"${stats.get('p50', 0):,.0f}", "Mediana P50")
        col2.metric("Escenario Optimista", f"${stats.get('p90', 0):,.0f}", "P90")
        col3.metric("Escenario Pesimista", f"${stats.get('p10', 0):,.0f}", "P10", delta_color="inverse")
        col4.metric("Riesgo de Pérdida",   f"{stats.get('prob_loss', 0):.1%}", delta_color="inverse")

        # Semáforo mensual (12 meses completos para cliente)
        semaforo = stress.get('semaforo', {})
        if semaforo:
            st.markdown("---")
            st.subheader("📅 Semáforo — Horizonte 12 Meses")
            cols_sem = st.columns(6)
            for mes in range(1, 7):
                s = semaforo.get(mes, {})
                with cols_sem[mes - 1]:
                    st.metric(f"Mes {mes}", s.get('emoji', '🟢'), s.get('estado', 'OK'))
            cols_sem2 = st.columns(6)
            for mes in range(7, 13):
                s = semaforo.get(mes, {})
                with cols_sem2[mes - 7]:
                    st.metric(f"Mes {mes}", s.get('emoji', '🟢'), s.get('estado', 'OK'))
        else:
            st.info("El semáforo estará disponible una vez que el consultor complete el análisis.")

        # Distribución de resultados (simplificada)
        results_df = pipeline_results.get('simulation_results')
        if results_df is not None and stats:
            st.markdown("---")
            st.subheader("📊 Distribución de Resultados")
            st.plotly_chart(render_distribution_chart(results_df, stats), use_container_width=True)

    # ── Tab 2: Reportes ───────────────────────────────────────────────────────
    with tab_rep:
        st.subheader("📄 Exportar Reportes")
        st.markdown(
            "Descarga el reporte ejecutivo de su empresa en formato PDF. "
            "El documento incluye el semáforo, KPIs y resumen de riesgos proyectados."
        )
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

            # ── PUENTE CLOUD-TO-LOCAL ─────────────────────────────────────────
            # Sincroniza YAMLs desde saas_configuraciones_yaml → configs/clients/
            _sb          = get_supabase_client()
            client_names: list[str] = []   # nombres comerciales para el selectbox
            file_map:     dict[str, str] = {}  # {nombre_comercial: "archivo.yaml"}

            if _sb:
                try:
                    res_yaml = (
                        _sb.table("saas_configuraciones_yaml")
                        .select("cliente_id, yaml_content")
                        .eq("es_activo", True)
                        .execute()
                    )
                    res_cli = (
                        _sb.table("saas_clientes")
                        .select("id, nombre_comercial")
                        .execute()
                    )

                    if res_yaml.data and res_cli.data:
                        id_to_nombre = {c["id"]: c["nombre_comercial"] for c in res_cli.data}

                        os.makedirs("configs/clients", exist_ok=True)

                        seen: set[str] = set()  # evita duplicados si hay varios YAMLs por cliente
                        for row in res_yaml.data:
                            cid          = row.get("cliente_id")
                            nombre       = id_to_nombre.get(cid)
                            yaml_content = row.get("yaml_content", "")

                            if not nombre or not yaml_content or cid in seen:
                                continue
                            seen.add(cid)

                            # Sanitización del nombre para nombre de archivo
                            sanitized = (
                                nombre.lower()
                                .replace(" ", "_")
                                .replace("/", "_")
                                .replace("\\", "_")
                                .replace(".", "_")
                                .replace(",", "_")
                            )
                            fname = f"{sanitized}.yaml"

                            with open(f"configs/clients/{fname}", "w", encoding="utf-8") as fout:
                                fout.write(yaml_content)

                            client_names.append(nombre)
                            file_map[nombre] = fname

                except Exception as _sync_err:
                    st.warning(f"⚠️ Sincronización Supabase falló: {_sync_err}")

            if client_names:
                selected_nombre      = st.selectbox("Seleccionar Auditoría:", client_names)
                selected_client_file = file_map[selected_nombre]
            else:
                selected_client_file = "SIN_CLIENTES"
                st.selectbox("Seleccionar Auditoría:", ["SIN_CLIENTES"], disabled=True)
        else:
            # ── EJECUTIVO: Carga el YAML del cliente asignado desde Supabase ────
            st.markdown("---")
            st.markdown("**🏢 Portal de Cliente:**")
            client_id = st.session_state.get('client_id')
            selected_client_file = "SIN_CLIENTES"

            if client_id:
                _sb_exec = get_supabase_client()
                if _sb_exec:
                    try:
                        res_ey = (
                            _sb_exec.table("saas_configuraciones_yaml")
                            .select("yaml_content")
                            .eq("cliente_id", client_id)
                            .eq("es_activo", True)
                            .limit(1)
                            .execute()
                        )
                        res_ec = (
                            _sb_exec.table("saas_clientes")
                            .select("nombre_comercial")
                            .eq("id", client_id)
                            .limit(1)
                            .execute()
                        )
                        if res_ey.data and res_ec.data:
                            yaml_content_exec = res_ey.data[0].get("yaml_content", "")
                            nombre_exec       = res_ec.data[0].get("nombre_comercial", "cliente")
                            sanitized_exec    = (
                                nombre_exec.lower()
                                .replace(" ", "_").replace("/", "_")
                                .replace("\\", "_").replace(".", "_").replace(",", "_")
                            )
                            fname_exec = f"{sanitized_exec}.yaml"
                            os.makedirs("configs/clients", exist_ok=True)
                            with open(f"configs/clients/{fname_exec}", "w", encoding="utf-8") as fout:
                                fout.write(yaml_content_exec)
                            selected_client_file = fname_exec
                            st.info(f"**{nombre_exec}**")
                        else:
                            st.warning("⚠️ Sin modelo activo. Contacte a su consultor.")
                    except Exception as _exec_err:
                        st.warning(f"⚠️ Error al cargar perfil: {_exec_err}")
                else:
                    st.warning("⚠️ Sin conexión a Supabase.")
            else:
                st.warning("⚠️ Sin cliente asignado. Contacte al administrador.")
            
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
        st.info(
            "El Data Mesh está en línea y conectado a Supabase, pero no se encontraron "
            "modelos estocásticos activos (`es_activo = True`) en `saas_configuraciones_yaml`. "
            "Genera el primer modelo desde el Panel de Administración → Cerebro Estocástico."
        )
        
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
            vista_cliente(pipeline_results, config)
        elif st.session_state.role in ["Consultor", "Admin"]:
            vista_consultor_v2(pipeline_results, config)
        else:
            st.error("❌ Rol no reconocido")
            
    except FileNotFoundError as e:
        st.error(f"❌ Error Estructural: No se encontró el archivo físico del cliente. {str(e)}")
        st.info("Por favor, asegúrate de generar el YAML en el Panel de Administración.")

if __name__ == "__main__":
    main()