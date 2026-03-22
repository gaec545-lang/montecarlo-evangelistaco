"""
Plotly charts reusables para Sentinel.
Gráficas con theme Evangelista aplicado automáticamente.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd


def render_revenue_chart(df: pd.DataFrame = None):
    """Gráfica de evolución de ingresos con theme Evangelista."""

    if df is None:
        df = pd.DataFrame({
            "Mes": ["Ene", "Feb", "Mar", "Abr", "May", "Jun"],
            "Ingresos": [1.8, 2.1, 1.9, 2.3, 2.2, 2.4],
            "Objetivo": [2.0, 2.0, 2.0, 2.0, 2.0, 2.0]
        })

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["Mes"],
        y=df["Ingresos"],
        mode="lines+markers",
        name="Ingresos Reales",
        line=dict(color="#6B7B5E", width=3),
        marker=dict(size=10),
        fill="tozeroy",
        fillcolor="rgba(107, 123, 94, 0.1)"
    ))

    fig.add_trace(go.Scatter(
        x=df["Mes"],
        y=df["Objetivo"],
        mode="lines",
        name="Objetivo",
        line=dict(color="#FF9500", width=2, dash="dash")
    ))

    fig.update_layout(
        template="evangelista",
        height=350,
        margin=dict(l=20, r=20, t=40, b=20),
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)


def render_margin_chart(df: pd.DataFrame = None):
    """Gráfica de margen por proyecto."""

    if df is None:
        df = pd.DataFrame({
            "Proyecto": ["Proyecto A", "Proyecto B", "Proyecto C", "Proyecto D", "Proyecto E"],
            "Margen": [48.5, 35.2, 52.1, 41.3, 38.7]
        })

    fig = px.bar(
        df,
        x="Proyecto",
        y="Margen",
        text="Margen",
        color="Margen",
        color_continuous_scale=["#FF3B30", "#FF9500", "#34C759"]
    )

    fig.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside",
        marker_line_color="#FFFFFF",
        marker_line_width=2
    )

    fig.update_layout(
        template="evangelista",
        height=350,
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)
