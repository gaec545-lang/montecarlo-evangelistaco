import pandas as pd
from typing import Dict, List
from src.configuration_manager import ConfigurationManager

class BusinessTranslator:
    """Traductor de estadísticas Monte Carlo a lenguaje ejecutivo"""
    
    def __init__(self, config: ConfigurationManager, extracted_data: Dict[str, pd.DataFrame] = None):
        self.config = config
        self.extracted_data = extracted_data or {}
        self.templates = self._load_narrative_templates()
    
    def _load_narrative_templates(self) -> dict:
        return {}
        
    def translate(self, stats: dict, sensitivity: pd.DataFrame) -> dict:
        primary_driver = sensitivity.iloc[0]['variable']
        primary_importance = sensitivity.iloc[0]['importance']
        
        return {
            'executive_summary': self._generate_executive_summary(stats, primary_driver, primary_importance),
            'risk_assessment': self._assess_risk_level(stats),
            'scenario_analysis': self._generate_scenario_analysis(stats),
            'key_findings': self._extract_key_findings(stats, sensitivity),
            'confidence_level': self._calculate_confidence_level(stats, sensitivity)
        }

    def _generate_executive_summary(self, stats: dict, primary_driver: str, importance: float) -> str:
        prob_loss, p50, p10 = stats['prob_loss'], stats['p50'], stats['p10']
        tone, action = ("crítica", "requiere intervención inmediata") if prob_loss > 0.30 else \
                       ("moderada", "requiere monitoreo cercano") if prob_loss > 0.15 else \
                       ("estable", "está dentro de parámetros aceptables")
                       
        return f"""Su operación presenta una situación {tone} basada en 10,000 simulaciones Monte Carlo.
**Resultado Esperado (P50):** ${p50:,.0f} MXN mensuales.
**Exposición al Riesgo:** Existe {prob_loss:.1%} de probabilidad de operar con pérdidas en un mes típico. Escenario pesimista (P10): ${p10:,.0f} MXN.
**Driver Principal de Riesgo:** {primary_driver} es responsable del {importance:.0%} de la variabilidad.
**Recomendación Estratégica:** Su situación {action}."""

    def _assess_risk_level(self, stats: dict) -> str:
        prob_loss = stats['prob_loss']
        cv = abs(stats['std'] / stats['mean']) if stats['mean'] != 0 else 0
        
        if prob_loss > 0.30 or cv > 0.50: level, color, exp = "CRÍTICO", "🔴", "Riesgo sistémico."
        elif prob_loss > 0.15 or cv > 0.35: level, color, exp = "ALTO", "🟡", "Requiere acciones correctivas."
        elif prob_loss > 0.05 or cv > 0.20: level, color, exp = "MODERADO", "🟠", "Riesgo manejable."
        else: level, color, exp = "BAJO", "🟢", "Operación estable."
        
        return f"{color} **NIVEL DE RIESGO: {level}**\n{exp}\nProbabilidad Pérdida: {prob_loss:.1%} | VaR 95%: ${abs(stats['var_95']):,.0f}"

    def _generate_scenario_analysis(self, stats: dict) -> str:
        return f"**P10 (Pesimista):** ${stats['p10']:,.0f}\n**P50 (Base):** ${stats['p50']:,.0f}\n**P90 (Optimista):** ${stats['p90']:,.0f}"

    def _extract_key_findings(self, stats: dict, sensitivity: pd.DataFrame) -> List[str]:
        primary = sensitivity.iloc[0]
        return [f"**Variable Crítica:** {primary['variable']} ({primary['importance']:.0%} varianza)."]

    def _calculate_confidence_level(self, stats: dict, sensitivity: pd.DataFrame) -> str:
        data_quality = len(self.extracted_data) > 0
        total_records = sum(len(df) for df in self.extracted_data.values()) if data_quality else 0
        primary_importance = sensitivity.iloc[0]['importance']
        
        if primary_importance > 0.60 and total_records > 100:
            return f"**Confianza:** ALTA\nProyecciones respaldadas por {total_records} registros."
        elif primary_importance > 0.40 and total_records > 30:
            return "**Confianza:** MEDIA\nProyecciones razonables con datos históricos limitados."
        return "**Confianza:** BAJA\nAlta incertidumbre debido a datos insuficientes."