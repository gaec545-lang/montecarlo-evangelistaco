"""
Projection Engine con soporte para múltiples metodologías de KPIs
"""
from typing import Dict
from enum import Enum


class KPIMethodology(Enum):
    OKR = "okr"
    BSC = "bsc"
    SMART = "smart"
    NORTH_STAR = "north_star"
    OPERATIONAL = "operational"


class ProjectionEngine:
    """Genera KPIs adaptados a la metodología elegida."""

    def __init__(self, monte_carlo_results: Dict, methodology: str = "operational"):
        self.statistics = monte_carlo_results.get('statistics', {})
        try:
            self.methodology = KPIMethodology(methodology)
        except ValueError:
            self.methodology = KPIMethodology.OPERATIONAL

        # Campos derivados que no están en get_statistics()
        mean = self.statistics.get('mean', 0)
        std = self.statistics.get('std', 0)
        self.statistics.setdefault('expected_value', mean)
        self.statistics['cv'] = abs(std / mean) if mean != 0 else 0

    def generate_kpis_by_methodology(self, industry: str = None) -> Dict:
        dispatch = {
            KPIMethodology.OKR:          self._generate_okrs,
            KPIMethodology.BSC:          self._generate_balanced_scorecard,
            KPIMethodology.SMART:        self._generate_smart_kpis,
            KPIMethodology.NORTH_STAR:   self._generate_north_star,
            KPIMethodology.OPERATIONAL:  self._generate_operational_kpis,
        }
        return dispatch[self.methodology]()

    # ── OKRs ──────────────────────────────────────────────────────────────
    def _generate_okrs(self) -> Dict:
        s = self.statistics
        p50, p90, prob_loss = s.get('p50', 0), s.get('p90', 0), s.get('prob_loss', 0)
        return {
            'methodology': 'OKRs',
            'objectives': [
                {
                    'objective': 'Maximizar estabilidad financiera operativa',
                    'key_results': [
                        {
                            'kr': 'Mantener probabilidad de pérdida < 15%',
                            'current': f"{prob_loss * 100:.1f}%",
                            'target': '< 15%',
                            'status': 'on_track' if prob_loss < 0.15 else 'at_risk',
                        },
                        {
                            'kr': 'Resultado mensual base ≥ P50 simulado',
                            'current': f"${p50:,.0f}",
                            'target': f"${p50 * 1.1:,.0f}",
                            'status': 'on_track',
                        },
                        {
                            'kr': 'Capturar escenario optimista (P90)',
                            'current': f"${p90:,.0f}",
                            'target': f"${p90 * 0.9:,.0f}",
                            'status': 'on_track',
                        },
                    ],
                }
            ],
        }

    # ── Balanced Scorecard ─────────────────────────────────────────────────
    def _generate_balanced_scorecard(self) -> Dict:
        s = self.statistics
        expected = s.get('expected_value', 0)
        cv = s.get('cv', 0)
        prob_loss = s.get('prob_loss', 0)
        return {
            'methodology': 'Balanced Scorecard',
            'perspectives': {
                'financial': {
                    'name': 'Perspectiva Financiera',
                    'kpis': [
                        {'kpi': 'Resultado Esperado Mensual', 'value': f"${expected:,.0f}",
                         'interpretation': 'Promedio de simulaciones',
                         'trend': 'positive' if expected > 0 else 'negative'},
                        {'kpi': 'Margen de Seguridad', 'value': f"{(1 - prob_loss) * 100:.1f}%",
                         'interpretation': 'Confianza en resultados positivos',
                         'trend': 'positive' if prob_loss < 0.2 else 'negative'},
                    ],
                },
                'customer': {
                    'name': 'Perspectiva del Cliente',
                    'kpis': [
                        {'kpi': 'Capacidad de Cumplimiento', 'value': f"{(1 - prob_loss) * 100:.0f}%",
                         'interpretation': 'Probabilidad de cumplir expectativas', 'trend': 'stable'},
                    ],
                },
                'internal_processes': {
                    'name': 'Procesos Internos',
                    'kpis': [
                        {'kpi': 'Volatilidad Operativa', 'value': f"{cv * 100:.1f}%",
                         'interpretation': 'Coeficiente de variación',
                         'trend': 'negative' if cv > 0.3 else 'positive'},
                    ],
                },
                'learning_growth': {
                    'name': 'Aprendizaje y Crecimiento',
                    'kpis': [
                        {'kpi': 'Madurez en Gestión de Riesgo', 'value': 'Medio',
                         'interpretation': 'Análisis Monte Carlo implementado', 'trend': 'positive'},
                    ],
                },
            },
        }

    # ── SMART KPIs ─────────────────────────────────────────────────────────
    def _generate_smart_kpis(self) -> Dict:
        s = self.statistics
        p50, prob_loss = s.get('p50', 0), s.get('prob_loss', 0)
        return {
            'methodology': 'SMART KPIs',
            'kpis': [
                {
                    'name': 'Resultado Financiero Mensual',
                    'specific': f"Alcanzar resultado mediano de ${p50:,.0f} mensuales",
                    'measurable': 'Medido mensualmente via simulación Monte Carlo',
                    'achievable': 'Basado en datos históricos del negocio',
                    'relevant': 'Impacta directamente flujo de caja operativo',
                    'time_bound': 'Revisión mensual, meta trimestral',
                    'current_value': f"${p50:,.0f}",
                    'status': 'on_track',
                },
                {
                    'name': 'Reducción de Riesgo de Pérdida',
                    'specific': 'Mantener probabilidad de pérdida bajo 15%',
                    'measurable': f"Actualmente en {prob_loss * 100:.1f}%",
                    'achievable': 'Mediante gestión de variables clave identificadas',
                    'relevant': 'Protege capital y operación continua',
                    'time_bound': 'Evaluación mensual',
                    'current_value': f"{prob_loss * 100:.1f}%",
                    'status': 'at_risk' if prob_loss > 0.15 else 'on_track',
                },
            ],
        }

    # ── North Star ─────────────────────────────────────────────────────────
    def _generate_north_star(self) -> Dict:
        s = self.statistics
        expected = s.get('expected_value', 0)
        cv = s.get('cv', 0)
        prob_loss = s.get('prob_loss', 0)
        return {
            'methodology': 'North Star Framework',
            'north_star_metric': {
                'name': 'Resultado Esperado Positivo Consistente',
                'value': f"${expected:,.0f}",
                'definition': 'Resultado financiero esperado con alta confiabilidad',
                'why_this_metric': 'Combina rentabilidad y estabilidad operativa',
            },
            'input_metrics': [
                {'name': 'Confianza en Resultados',
                 'value': f"{(1 - prob_loss) * 100:.0f}%",
                 'impact_on_north_star': 'Alto',
                 'lever': 'Reducir volatilidad en variables clave'},
                {'name': 'Estabilidad Operativa',
                 'value': f"CV: {cv * 100:.1f}%",
                 'impact_on_north_star': 'Medio',
                 'lever': 'Diversificar drivers de ingreso'},
            ],
        }

    # ── Operational KPIs ───────────────────────────────────────────────────
    def _generate_operational_kpis(self) -> Dict:
        s = self.statistics
        cv = s.get('cv', 0)
        prob_loss = s.get('prob_loss', 0)
        return {
            'methodology': 'KPIs Operativos',
            'categories': {
                'financial': {
                    'name': 'Métricas Financieras',
                    'metrics': [
                        {'metric': 'Resultado Esperado', 'value': f"${s.get('mean', 0):,.0f}", 'unit': 'mensual'},
                        {'metric': 'Resultado Mediano (P50)', 'value': f"${s.get('p50', 0):,.0f}", 'unit': 'mensual'},
                        {'metric': 'Escenario Conservador (P10)', 'value': f"${s.get('p10', 0):,.0f}", 'unit': 'mensual'},
                        {'metric': 'Escenario Optimista (P90)', 'value': f"${s.get('p90', 0):,.0f}", 'unit': 'mensual'},
                    ],
                },
                'risk': {
                    'name': 'Métricas de Riesgo',
                    'metrics': [
                        {'metric': 'Probabilidad de Pérdida',
                         'value': f"{prob_loss * 100:.1f}%",
                         'interpretation': 'Bajo' if prob_loss < 0.15 else ('Medio' if prob_loss < 0.30 else 'Alto')},
                        {'metric': 'Coeficiente de Variación',
                         'value': f"{cv * 100:.1f}%",
                         'interpretation': 'Estable' if cv < 0.3 else 'Volátil'},
                    ],
                },
            },
        }
