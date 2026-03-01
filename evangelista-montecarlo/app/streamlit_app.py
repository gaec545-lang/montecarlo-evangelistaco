import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any
import sys
import os

# Agregar path del proyecto para imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.configuration_manager import ConfigurationManager
from src.monte_carlo_engine import UniversalMonteCarloEngine

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
# FUNCIONES DE NEGOCIO (CACHEADAS)
# ═══════════════════════════════════════════════════════════════

@st.cache_resource
def load_engine():
    """
    Carga y configura el motor Monte Carlo (cached)
    Solo se ejecuta una vez por sesión de Streamlit
    """
    config = ConfigurationManager(
        template='templates/alimentos.yaml',
        client_config='clients/test_pasteleria_config.yaml'
    )
    
    engine = UniversalMonteCarloEngine(config)
    engine.load_historical_data()
    engine.setup_simulation()
    
    return engine, config


@st.cache_data
def run_simulation(_engine):
    """
    Ejecuta simulación Monte Carlo (cached)
    El underscore en _engine evita que Streamlit intente hashear el objeto
    """
    results = _engine.run()
    stats = _engine.get_statistics()
    sensitivity = _engine.sensitivity_analysis()
    triggers = _engine.evaluate_triggers(stats)
    
    return results, stats, sensitivity, triggers


# ═══════════════════════════════════════════════════════════════
# FUNCIONES DE VISUALIZACIÓN
# ═══════════════════════════════════════════════════════════════

def render_gauge(value: float, title: str, range_max: float, threshold: float = None):
    """
    Renderiza medidor tipo gauge usando Plotly
    
    Args:
        value: Valor actual
        title: Título del gauge
        range_max: Valor máximo del rango
        threshold: Línea de umbral (opcional)
    """
    # Determinar color según valor
    if threshold and value > threshold:
        color = "red"
    elif threshold and value > threshold * 0.7:
        color = "orange"
    else:
        color = "green"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value * 100 if value < 1 else value,  # Convertir a % si es prob
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
    """
    Renderiza Tornado Chart (análisis de sensibilidad)
    Solo visible para consultores
    """
    # Ordenar por importancia
    df = sensitivity_df.sort_values('importance', ascending=True)
    
    # Crear gráfico de barras horizontales
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
    fig.update_layout(
        height=400,
        showlegend=False,
        xaxis_title="Importancia (%)",
        yaxis_title="",
        font=dict(size=14)
    )
    
    return fig


def render_distribution_chart(results: pd.DataFrame, stats: Dict):
    """
    Renderiza histograma de distribución de resultados
    """
    fig = go.Figure()
    
    # Histograma
    fig.add_trace(go.Histogram(
        x=results['outcome'],
        nbinsx=50,
        name='Distribución',
        marker_color='lightblue',
        opacity=0.7
    ))
    
    # Líneas de percentiles
    fig.add_vline(x=stats['p50'], line_dash="dash", line_color="blue", 
                  annotation_text=f"P50: ${stats['p50']:,.0f}")
    fig.add_vline(x=stats['p10'], line_dash="dash", line_color="red", 
                  annotation_text=f"P10: ${stats['p10']:,.0f}")
    fig.add_vline(x=stats['p90'], line_dash="dash", line_color="green", 
                  annotation_text=f"P90: ${stats['p90']:,.0f}")
    
    # Sombrear área de pérdida
    fig.add_vrect(
        x0=results['outcome'].min(), x1=0,
        fillcolor="red", opacity=0.1,
        layer="below", line_width=0,
        annotation_text="Zona de Pérdida", annotation_position="top left"
    )
    
    fig.update_layout(
        title='Distribución de Resultados (10,000 Simulaciones)',
        xaxis_title='Resultado (MXN)',
        yaxis_title='Frecuencia',
        height=400,
        showlegend=False
    )
    
    return fig


# ═══════════════════════════════════════════════════════════════
# SISTEMA DE AUTENTICACIÓN
# ═══════════════════════════════════════════════════════════════

def login_page():
    with col2:
    st.image("assets/logoEvangelistaCo.png", use_container_width=True)
    
    st.markdown("<h2 style='text-align: center;'>Portal de Socios</h2>", unsafe_allow_html=True)
    # ... resto de la lógica de login
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("Autenticación")
        
        # Credenciales estáticas (PoC)
        # En producción: integrar con Auth0, Azure AD, etc.
        USUARIOS = {
            'ejecutivo': {'password': 'cliente123', 'role': 'Ejecutivo', 'nombre': 'Juan Pérez (CEO)'},
            'consultor': {'password': 'evangelista123', 'role': 'Consultor', 'nombre': 'Analista Evangelista'}
        }
        
        username = st.text_input("Usuario", placeholder="ejecutivo o consultor")
        password = st.text_input("Contraseña", type="password", placeholder="Ingrese contraseña")
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("🔓 Iniciar Sesión", use_container_width=True):
                if username in USUARIOS and password == USUARIOS[username]['password']:
                    st.session_state.authenticated = True
                    st.session_state.role = USUARIOS[username]['role']
                    st.session_state.username = USUARIOS[username]['nombre']
                    st.rerun()
                else:
                    st.error("❌ Credenciales inválidas")
        
        with col_btn2:
            if st.button("ℹ️ Ver Credenciales Demo", use_container_width=True):
                st.info("""
                    **Credenciales de Demo:**
                    
                    **Ejecutivo (Cliente):**
                    - Usuario: `ejecutivo`
                    - Contraseña: `cliente123`
                    
                    **Consultor (Evangelista & Co.):**
                    - Usuario: `consultor`
                    - Contraseña: `evangelista123`
                """)


# ═══════════════════════════════════════════════════════════════
# VISTA EJECUTIVO (CLIENTE)
# ═══════════════════════════════════════════════════════════════

def vista_ejecutivo(stats: Dict, triggers: List[Dict], results: pd.DataFrame, config):
    """
    Vista simplificada para ejecutivos del cliente
    
    Muestra:
    - KPIs principales (gauges)
    - Alertas sin recomendaciones profundas
    - NO muestra análisis de sensibilidad
    """
    st.markdown(f"""
        <h2 style='color: #1f77b4;'>
            📊 Dashboard Ejecutivo - {config.get('client.name', 'Cliente')}
        </h2>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # SECCIÓN 1: KPIs PRINCIPALES
    st.subheader("📈 Indicadores Clave de Riesgo")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Gauge: Probabilidad de Pérdida
        threshold_loss = config.get('thresholds.critical_loss_prob', 0.25)
        fig_loss = render_gauge(
            value=stats['prob_loss'],
            title="Probabilidad de Pérdida",
            range_max=1.0,
            threshold=threshold_loss
        )
        st.plotly_chart(fig_loss, use_container_width=True)
    
    with col2:
        # Gauge: Value at Risk (VaR 95%)
        fig_var = render_gauge(
            value=abs(stats['var_95']),
            title="VaR 95% (Pérdida Máxima Esperada)",
            range_max=abs(stats['var_95']) * 2,
            threshold=abs(stats['var_95']) * 0.8
        )
        st.plotly_chart(fig_var, use_container_width=True)
    
    with col3:
        # Gauge: P50 (Resultado Esperado)
        fig_p50 = render_gauge(
            value=stats['p50'],
            title="Resultado Esperado (P50)",
            range_max=stats['p90'],
            threshold=stats['mean'] * 0.5
        )
        st.plotly_chart(fig_p50, use_container_width=True)
    
    st.markdown("---")
    
    # SECCIÓN 2: RESUMEN DE EXPOSICIÓN
    st.subheader("💰 Resumen de Exposición Financiera")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            label="Ganancia Esperada (Mediana)",
            value=f"${stats['p50']:,.0f}",
            delta=f"Rango: ${stats['p25']:,.0f} - ${stats['p75']:,.0f}"
        )
        
        st.metric(
            label="Escenario Pesimista (P10)",
            value=f"${stats['p10']:,.0f}",
            delta="10% de probabilidad de caer aquí",
            delta_color="inverse"
        )
    
    with col2:
        st.metric(
            label="Escenario Optimista (P90)",
            value=f"${stats['p90']:,.0f}",
            delta="10% de probabilidad de superar esto",
            delta_color="normal"
        )
        
        st.metric(
            label="Riesgo de Pérdida",
            value=f"{stats['prob_loss']:.1%}",
            delta="Probabilidad de resultado negativo",
            delta_color="inverse"
        )
    
    st.markdown("---")
    
    # SECCIÓN 3: ALERTAS (SIN RECOMENDACIONES PROFUNDAS)
    st.subheader("🚨 Alertas Activas")
    
    if triggers:
        # Filtrar y simplificar alertas para ejecutivo
        for trigger in triggers:
            nivel = trigger['nivel']
            
            # Color según nivel
            if nivel == 'CRÍTICO':
                st.error(f"🔴 **{nivel}**: {trigger['mensaje']}")
            elif nivel == 'ALTO':
                st.warning(f"🟡 **{nivel}**: {trigger['mensaje']}")
            else:
                st.info(f"🟠 **{nivel}**: {trigger['mensaje']}")
            
            # Mostrar solo contexto básico (NO recomendaciones)
            st.caption(f"Métrica afectada: {trigger['metrica']}")
        
        st.markdown("---")
        st.info("""
            💡 **Nota**: Para un análisis detallado y estrategias de mitigación específicas, 
            contacte a su consultor de Evangelista & Co.
        """)
    else:
        st.success("✅ No hay alertas activas. Todos los indicadores dentro de parámetros normales.")
    
    st.markdown("---")
    
    # SECCIÓN 4: DISTRIBUCIÓN (SIMPLIFICADA)
    st.subheader("📊 Distribución de Resultados")
    fig_dist = render_distribution_chart(results, stats)
    st.plotly_chart(fig_dist, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# VISTA CONSULTOR (EVANGELISTA & CO.)
# ═══════════════════════════════════════════════════════════════

def vista_consultor(stats: Dict, triggers: List[Dict], sensitivity: pd.DataFrame, 
                    results: pd.DataFrame, config):
    """
    Vista completa para consultores de Evangelista & Co.
    
    Muestra:
    - Todos los KPIs de vista ejecutivo
    - Alertas CON recomendaciones completas
    - Análisis de sensibilidad (Tornado Chart)
    - Métricas avanzadas
    """
    st.markdown(f"""
        <h2 style='color: #d62728;'>
            🔬 Vista Consultor - Análisis Completo
        </h2>
        <h4 style='color: #666;'>
            Cliente: {config.get('client.name', 'N/A')} | Industria: {config.get('client.industry', 'N/A')}
        </h4>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # SECCIÓN 1: KPIs (IGUAL QUE EJECUTIVO)
    st.subheader("📈 Indicadores Clave de Riesgo")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        threshold_loss = config.get('thresholds.critical_loss_prob', 0.25)
        fig_loss = render_gauge(
            value=stats['prob_loss'],
            title="Probabilidad de Pérdida",
            range_max=1.0,
            threshold=threshold_loss
        )
        st.plotly_chart(fig_loss, use_container_width=True)
    
    with col2:
        fig_var = render_gauge(
            value=abs(stats['var_95']),
            title="VaR 95%",
            range_max=abs(stats['var_95']) * 2,
            threshold=abs(stats['var_95']) * 0.8
        )
        st.plotly_chart(fig_var, use_container_width=True)
    
    with col3:
        fig_p50 = render_gauge(
            value=stats['p50'],
            title="Resultado Esperado (P50)",
            range_max=stats['p90'],
            threshold=stats['mean'] * 0.5
        )
        st.plotly_chart(fig_p50, use_container_width=True)
    
    st.markdown("---")
    
    # SECCIÓN 2: ANÁLISIS DE SENSIBILIDAD (EXCLUSIVO CONSULTOR)
    st.subheader("🎯 Análisis de Sensibilidad - Diagnóstico Raíz")
    
    st.info("""
        **🔒 Sección Confidencial - Solo Evangelista & Co.**
        
        Este análisis identifica qué variables tienen mayor impacto en los resultados.
        Úsalo para formular estrategias de mitigación y propuestas de optimización.
    """)
    
    # Tornado Chart
    fig_tornado = render_tornado_chart(sensitivity)
    st.plotly_chart(fig_tornado, use_container_width=True)
    
    # Tabla de sensibilidad
    with st.expander("📋 Ver Datos de Sensibilidad"):
        st.dataframe(
            sensitivity.style.format({
                'correlation': '{:.3f}',
                'importance': '{:.1%}'
            }),
            use_container_width=True
        )
    
    st.markdown("---")
    
    # SECCIÓN 3: ALERTAS CON RECOMENDACIONES COMPLETAS
    st.subheader("🚨 Alertas y Estrategias de Mitigación")
    
    if triggers:
        for idx, trigger in enumerate(triggers, 1):
            nivel = trigger['nivel']
            
            # Contenedor expandible por alerta
            with st.expander(f"[{nivel}] Alerta #{idx}: {trigger['metrica']}", expanded=(nivel == 'CRÍTICO')):
                
                # Mensaje principal
                if nivel == 'CRÍTICO':
                    st.error(trigger['mensaje'])
                elif nivel == 'ALTO':
                    st.warning(trigger['mensaje'])
                else:
                    st.info(trigger['mensaje'])
                
                # Detalles técnicos
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Valor Actual", f"{trigger['valor_actual']:.1%}" if trigger['valor_actual'] < 1 else f"${trigger['valor_actual']:,.0f}")
                with col2:
                    st.metric("Umbral Permitido", f"{trigger['umbral_permitido']:.1%}" if trigger['umbral_permitido'] < 1 else f"${trigger['umbral_permitido']:,.0f}")
                
                # Recomendación estratégica
                st.markdown("**💡 Estrategia de Mitigación:**")
                st.success(trigger['recomendacion'])
                
                # Contexto adicional si existe
                if 'contexto' in trigger:
                    st.markdown("**📋 Contexto Adicional:**")
                    for key, value in trigger['contexto'].items():
                        if isinstance(value, float):
                            st.caption(f"• {key}: {value:,.2f}")
                        else:
                            st.caption(f"• {key}: {value}")
    else:
        st.success("✅ No hay triggers activados. Cliente en zona de operación saludable.")
    
    st.markdown("---")
    
    # SECCIÓN 4: MÉTRICAS AVANZADAS
    st.subheader("📊 Métricas Estadísticas Completas")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Media", f"${stats['mean']:,.0f}")
        st.metric("P25", f"${stats['p25']:,.0f}")
    
    with col2:
        st.metric("Mediana (P50)", f"${stats['p50']:,.0f}")
        st.metric("P75", f"${stats['p75']:,.0f}")
    
    with col3:
        st.metric("Desv. Estándar", f"${stats['std']:,.0f}")
        st.metric("Coef. Variación", f"{(stats['std']/stats['mean']):.1%}")
    
    with col4:
        st.metric("Mínimo", f"${stats['min']:,.0f}")
        st.metric("Máximo", f"${stats['max']:,.0f}")
    
    # Distribución
    st.markdown("---")
    st.subheader("📈 Distribución de Resultados")
    fig_dist = render_distribution_chart(results, stats)
    st.plotly_chart(fig_dist, use_container_width=True)
    
    # Datos raw (opcional)
    with st.expander("🗂️ Ver Datos Raw de Simulación"):
        st.dataframe(results.head(100), use_container_width=True)
        st.caption(f"Mostrando primeras 100 de {len(results):,} simulaciones")


# ═══════════════════════════════════════════════════════════════
# APLICACIÓN PRINCIPAL
# ═══════════════════════════════════════════════════════════════
def main():
    """Función principal de la aplicación con Branding de Evangelista & Co."""
    
    # 1. INYECCIÓN DE ESTILOS CORPORATIVOS
    st.markdown(f"""
        <style>
            .stApp {{ background-color: #F8F9FA; }}
            [data-testid="stSidebar"] {{ background-color: #11111f; color: #FFFFFF; }}
            [data-testid="stSidebar"] .stMarkdown p, [data-testid="stSidebar"] span {{ color: #FFFFFF !important; }}
            h1, h2, h3, h4 {{ color: #1A1A2E !important; font-weight: 800; }}
            .stButton>button {{
                background-color: #11111f;
                color: #D4AF37;
                border: 2px solid #D4AF37;
                border-radius: 5px;
            }}
        </style>
    """, unsafe_allow_html=True)
    
    # Inicializar session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'role' not in st.session_state:
        st.session_state.role = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    
    # Si no está autenticado, mostrar login
    if not st.session_state.authenticated:
        login_page()
        return
    
    # ═══════════════════════════════════════════════════════════
    # SIDEBAR (COMÚN PARA AMBOS ROLES)
    # ═══════════════════════════════════════════════════════════
    with st.sidebar:
        # Incorporación del logo en lugar del emoji
        st.image("assets/logoEvangelistaCo.png", use_container_width=True)
        st.markdown("<h3 style='text-align: center; color: #D4AF37;'>Sentinel</h3>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        role_emoji = "👔" if st.session_state.role == "Ejecutivo" else "🔬"
        st.info(f"**Usuario:** {st.session_state.username}\n**Rol:** {role_emoji} {st.session_state.role}")
        
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.role = None
            st.rerun()
        
        st.markdown("---")
        
        # Info de la simulación
        st.markdown("**⚙️ Configuración:**")
        st.caption("• Motor: Monte Carlo")
        st.caption("• Simulaciones: 10,000")
        st.caption("• Modelo: Alimentos")
        
        st.markdown("---")
        st.caption("© 2026 Evangelista & Co.")
    
    # ═══════════════════════════════════════════════════════════
    # CARGAR DATOS (CACHEADO)
    # ═══════════════════════════════════════════════════════════
    
    with st.spinner("⚙️ Inicializando motor de simulación..."):
        engine, config = load_engine()
    
    with st.spinner("🎲 Ejecutando 10,000 simulaciones Monte Carlo..."):
        results, stats, sensitivity, triggers = run_simulation(engine)
    
    # ═══════════════════════════════════════════════════════════
    # RENDERIZAR VISTA SEGÚN ROL
    # ═══════════════════════════════════════════════════════════
    
    if st.session_state.role == "Ejecutivo":
        vista_ejecutivo(stats, triggers, results, config)
    
    elif st.session_state.role == "Consultor":
        vista_consultor(stats, triggers, sensitivity, results, config)
    
    else:
        st.error("❌ Rol no reconocido")

# ═══════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    main()
