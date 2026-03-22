"""
CSS custom para Sentinel - Overrides de Streamlit default.
Implementa paleta Evangelista & Co con glassmorphism y tipografía profesional.
"""


def get_custom_css() -> str:
    """Retorna CSS custom con paleta Evangelista."""

    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Cormorant+Garamond:wght@400;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

    :root {
        --primary: #6B7B5E;
        --primary-light: #8A9A7E;
        --primary-dark: #4A5A3E;
        --background: #F5F1E8;
        --surface: #FFFFFF;
        --text-primary: #1A1A1A;
        --text-secondary: #4A4A4A;
        --border: #E5E5EA;
        --success: #34C759;
        --warning: #FF9500;
        --danger: #FF3B30;
    }

    .main {
        background-color: var(--background) !important;
        font-family: 'Inter', -apple-system, sans-serif;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #6B7B5E 0%, #4A5A3E 100%);
        color: white;
    }

    [data-testid="stSidebar"] .css-1d391kg {
        color: rgba(255, 255, 255, 0.9);
    }

    h1, h2, h3 {
        font-family: 'Cormorant Garamond', Georgia, serif !important;
        color: var(--text-primary);
        font-weight: 700;
    }

    h1 {
        font-size: 2.5rem;
        letter-spacing: -0.5px;
        margin-bottom: 1rem;
    }

    h2 {
        font-size: 2rem;
        letter-spacing: -0.3px;
    }

    h3 {
        font-size: 1.5rem;
    }

    p, span, div {
        font-family: 'Inter', sans-serif;
        color: var(--text-secondary);
    }

    [data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2rem;
        font-weight: 700;
        color: var(--primary-dark);
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.875rem;
        color: var(--text-tertiary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .stButton > button {
        background: var(--primary);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.2s ease;
        box-shadow: 0 4px 12px rgba(107, 123, 94, 0.2);
    }

    .stButton > button:hover {
        background: var(--primary-dark);
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(107, 123, 94, 0.3);
    }

    .stButton > button:active {
        transform: translateY(0px);
    }

    .stTextInput > div > div > input,
    .stSelectbox > div > div > select,
    .stDateInput > div > div > input {
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 0.75rem 1rem;
        font-size: 1rem;
        background: var(--surface);
        transition: all 0.2s ease;
    }

    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus {
        border-color: var(--primary);
        box-shadow: 0 0 0 3px rgba(107, 123, 94, 0.1);
        outline: none;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background: transparent;
        border-bottom: 2px solid var(--border);
    }

    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        padding: 0 1.5rem;
        background: transparent;
        border-radius: 8px 8px 0 0;
        color: var(--text-secondary);
        font-weight: 500;
    }

    .stTabs [aria-selected="true"] {
        background: var(--surface);
        color: var(--primary);
        border-bottom: 3px solid var(--primary);
    }

    .dataframe {
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }

    .dataframe thead tr {
        background: var(--primary) !important;
        color: white !important;
    }

    .dataframe thead th {
        font-weight: 600;
        padding: 1rem !important;
        text-transform: uppercase;
        font-size: 0.875rem;
        letter-spacing: 0.5px;
    }

    .dataframe tbody tr:nth-child(even) {
        background: #FAFAF8;
    }

    .dataframe tbody td {
        padding: 0.75rem 1rem !important;
        border-bottom: 1px solid var(--border);
    }

    .streamlit-expanderHeader {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1rem;
        font-weight: 600;
        color: var(--text-primary);
    }

    .streamlit-expanderHeader:hover {
        background: var(--surface-hover);
        border-color: var(--primary);
    }

    [data-testid="stFileUploader"] {
        border: 2px dashed var(--border);
        border-radius: 12px;
        padding: 2rem;
        background: var(--surface);
        transition: all 0.2s ease;
    }

    [data-testid="stFileUploader"]:hover {
        border-color: var(--primary);
        background: rgba(107, 123, 94, 0.02);
    }

    .stSuccess {
        background: rgba(52, 199, 89, 0.1);
        border-left: 4px solid var(--success);
        border-radius: 8px;
        padding: 1rem;
    }

    .stWarning {
        background: rgba(255, 149, 0, 0.1);
        border-left: 4px solid var(--warning);
        border-radius: 8px;
        padding: 1rem;
    }

    .stError {
        background: rgba(255, 59, 48, 0.1);
        border-left: 4px solid var(--danger);
        border-radius: 8px;
        padding: 1rem;
    }

    .stSpinner > div {
        border-color: var(--primary) !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .glass-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(229, 229, 234, 0.5);
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
        transition: all 0.3s ease;
    }

    .glass-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12);
    }

    @media (max-width: 768px) {
        h1 { font-size: 2rem; }
        h2 { font-size: 1.5rem; }

        [data-testid="stMetricValue"] {
            font-size: 1.5rem;
        }
    }
    </style>
    """
