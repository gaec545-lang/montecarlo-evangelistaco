"""
Sistema de diseño Evangelista & Co para Sentinel.
Paleta de colores, tipografía, spacing, y constantes visuales.
"""

COLORS = {
    # Evangelista Brand
    "primary": "#6B7B5E",           # Olive green
    "primary_light": "#8A9A7E",
    "primary_dark": "#4A5A3E",
    "primary_alpha": "#6B7B5E1A",   # 10% opacity

    # Backgrounds
    "background": "#F5F1E8",        # Beige cream (main)
    "surface": "#FFFFFF",           # Cards, panels
    "surface_hover": "#FAFAF8",

    # Semantic colors (iOS-style)
    "success": "#34C759",
    "warning": "#FF9500",
    "danger": "#FF3B30",
    "info": "#007AFF",

    # Text
    "text_primary": "#1A1A1A",
    "text_secondary": "#4A4A4A",
    "text_tertiary": "#8E8E93",

    # Borders
    "border_light": "#E5E5EA",
    "border_medium": "#C7C7CC",
}

TYPOGRAPHY = {
    "font_family": "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    "font_family_display": "'Cormorant Garamond', Georgia, serif",
    "font_family_mono": "'JetBrains Mono', 'Courier New', monospace",
}

SPACING = {
    "xs": "0.5rem",   # 8px
    "sm": "1rem",     # 16px
    "md": "1.5rem",   # 24px
    "lg": "2rem",     # 32px
    "xl": "3rem",     # 48px
}

RADIUS = {
    "sm": "8px",
    "md": "12px",
    "lg": "16px",
    "xl": "20px",
}

SHADOWS = {
    "sm": "0 2px 8px rgba(0, 0, 0, 0.08)",
    "md": "0 4px 16px rgba(0, 0, 0, 0.12)",
    "lg": "0 8px 24px rgba(0, 0, 0, 0.16)",
}
