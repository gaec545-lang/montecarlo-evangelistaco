"""
Theme de Plotly con paleta Evangelista & Co.
Se aplica globalmente a todas las gráficas Plotly en Sentinel.
"""

import plotly.graph_objects as go
import plotly.io as pio


def get_evangelista_theme():
    """Configura y registra el theme de Plotly con paleta Evangelista."""

    evangelista_theme = {
        "layout": {
            "font": {
                "family": "'Inter', -apple-system, sans-serif",
                "size": 14,
                "color": "#1A1A1A"
            },
            "title": {
                "font": {
                    "family": "'Cormorant Garamond', Georgia, serif",
                    "size": 24,
                    "color": "#1A1A1A"
                },
                "x": 0.5,
                "xanchor": "center"
            },
            "paper_bgcolor": "#F5F1E8",
            "plot_bgcolor": "#FFFFFF",
            "colorway": [
                "#6B7B5E",  # Primary (olive green)
                "#34C759",  # Success
                "#FF9500",  # Warning
                "#007AFF",  # Info
                "#FF3B30",  # Danger
                "#8A9A7E",  # Primary light
                "#4ECDC4",  # Teal
                "#FFA07A",  # Coral
            ],
            "xaxis": {
                "gridcolor": "#E5E5EA",
                "linecolor": "#C7C7CC",
                "zerolinecolor": "#C7C7CC",
                "title": {"font": {"size": 13, "color": "#4A4A4A"}},
                "tickfont": {"size": 12, "color": "#8E8E93"}
            },
            "yaxis": {
                "gridcolor": "#E5E5EA",
                "linecolor": "#C7C7CC",
                "zerolinecolor": "#C7C7CC",
                "title": {"font": {"size": 13, "color": "#4A4A4A"}},
                "tickfont": {"size": 12, "color": "#8E8E93"}
            },
            "legend": {
                "bgcolor": "rgba(255, 255, 255, 0.9)",
                "bordercolor": "#E5E5EA",
                "borderwidth": 1,
                "font": {"size": 12}
            },
            "hovermode": "x unified",
            "hoverlabel": {
                "bgcolor": "#FFFFFF",
                "bordercolor": "#6B7B5E",
                "font": {"family": "'JetBrains Mono', monospace", "size": 12}
            }
        }
    }

    # Registrar theme
    pio.templates["evangelista"] = go.layout.Template(evangelista_theme)
    pio.templates.default = "evangelista"
