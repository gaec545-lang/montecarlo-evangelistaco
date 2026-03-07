"""
Decision Intelligence Engine - Fase 4
Genera recomendaciones prescriptivas basadas en reglas de negocio.

Soporta dos formatos de reglas en el YAML:

Formato nuevo (YAML Builder / IA):
  decision_rules:
    - title: "Alta probabilidad de perdida"
      condition: "prob_loss > 0.25"
      priority: "Alta"
      actions:
        - "Revisar estructura de costos"

Formato legacy (configs manuales):
  decision_rules:
    - rule_id: "R001"
      condition: "prob_loss > 0.15"
      severity: "ALTO"
      category: "financial_risk"
      recommendation_template: "Perdida elevada ({prob_loss:.1%})."
"""

from typing import Dict, List, Any, Optional
import pandas as pd
from src.configuration_manager import ConfigurationManager


# Mapa de prioridad string → int para ordenamiento
PRIORITY_MAP = {'Alta': 1, 'CRÍTICO': 1, 'Media': 2, 'ALTO': 2, 'Baja': 3, 'MEDIO': 3}


class DecisionIntelligenceEngine:
    """Motor de recomendaciones prescriptivas."""

    def __init__(self, config: ConfigurationManager):
        self.config = config
        self.decision_rules = self._load_decision_rules()

    def _load_decision_rules(self) -> List[Dict]:
        rules = self.config.get('decision_rules', [])
        if not rules:
            print("No hay decision_rules en YAML. Usando reglas default.")
            return self._get_default_rules()
        return rules

    def _get_default_rules(self) -> List[Dict]:
        return [
            {
                'title': 'Alta probabilidad de perdida',
                'condition': 'prob_loss > 0.20',
                'priority': 'Alta',
                'actions': [
                    'Revisar estructura de costos de forma inmediata',
                    'Analizar principales drivers de riesgo identificados',
                    'Implementar controles de contingencia preventivos',
                    'Evaluar estrategias de cobertura de riesgo',
                ]
            },
            {
                'title': 'Volatilidad excesiva en resultados',
                'condition': 'cv > 0.30',
                'priority': 'Media',
                'actions': [
                    'Evaluar estrategias de diversificacion',
                    'Analizar estabilizacion de variables clave',
                    'Considerar contratos de precio fijo con proveedores',
                ]
            },
            {
                'title': 'VaR significativo detectado',
                'condition': 'abs(var_95) > abs(expected_value) * 0.30 if expected_value != 0 else False',
                'priority': 'Alta',
                'actions': [
                    'Establecer reservas de contingencia',
                    'Revisar politicas de gestion de riesgo',
                    'Implementar monitoreo continuo de exposicion',
                ]
            },
            {
                'title': 'Escenario pesimista con perdidas directas',
                'condition': 'p10 < 0',
                'priority': 'Alta',
                'actions': [
                    'Revisar supuestos del modelo de negocio',
                    'Identificar palancas de reduccion de costos fijos',
                    'Evaluar estrategia de pricing',
                ]
            },
        ]

    def generate_recommendations(self, stats: Dict[str, float],
                                 sensitivity: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Genera recomendaciones evaluando cada regla contra las estadisticas.

        Soporta reglas en formato nuevo (title/priority/actions) y legacy
        (rule_id/severity/recommendation_template). Siempre retorna acciones
        en formato de lista de dicts con step/action/responsible para
        compatibilidad con el dashboard.
        """
        recommendations = []

        # Namespace enriquecido para eval (incluye cv que no viene en stats)
        mean = stats.get('mean', 0)
        std = stats.get('std', 0)
        cv = abs(std / mean) if mean != 0 else 0

        namespace = {
            'prob_loss':     stats.get('prob_loss', 0),
            'var_95':        stats.get('var_95', 0),
            'cvar_95':       stats.get('cvar_95', 0),
            'cv':            cv,
            'expected_value': mean,
            'mean':          mean,
            'std':           std,
            'p10':           stats.get('p10', 0),
            'p25':           stats.get('p25', 0),
            'p50':           stats.get('p50', 0),
            'p75':           stats.get('p75', 0),
            'p90':           stats.get('p90', 0),
            'abs':           abs,
        }

        # Driver principal de riesgo (para acciones contextuales)
        primary_driver = sensitivity.iloc[0]['variable'] if not sensitivity.empty else 'variable_principal'
        primary_importance = sensitivity.iloc[0]['importance'] if not sensitivity.empty else 0.0

        for rule in self.decision_rules:
            condition = rule.get('condition', '')
            if not self._evaluate_condition(condition, namespace):
                continue

            # ── Detectar formato y normalizar ──────────────────────────
            if 'title' in rule:
                # Formato nuevo (YAML Builder / IA / defaults nuevos)
                rec = self._build_from_new_format(rule, stats, primary_driver)
            else:
                # Formato legacy (configs manuales)
                rec = self._build_from_legacy_format(rule, stats, primary_driver, primary_importance)

            recommendations.append(rec)

        # Ordenar por prioridad numérica
        recommendations.sort(key=lambda x: x['priority'])

        # Fallback si ninguna regla disparó
        if not recommendations:
            recommendations.append(self._fallback_recommendation())

        return recommendations

    # ── Constructores por formato ────────────────────────────────────────

    def _build_from_new_format(self, rule: Dict, stats: Dict,
                               primary_driver: str) -> Dict:
        """Construye recomendacion desde formato nuevo (title/priority/actions)."""
        priority_str = rule.get('priority', 'Media')
        priority_int = PRIORITY_MAP.get(priority_str, 2)

        raw_actions = rule.get('actions', [])
        actions = self._normalize_actions(raw_actions, primary_driver)

        expected_savings = abs(stats.get('var_95', 0)) * 0.3

        return {
            'rule_id': rule.get('rule_id', f"R_{priority_str.upper()}"),
            'priority': priority_int,
            'category': rule.get('category', 'risk'),
            'title': rule.get('title', f'Alerta en {primary_driver}'),
            'description': rule.get('description',
                                    f'Condicion de riesgo detectada. '
                                    f'Driver principal: {primary_driver}.'),
            'actions': actions,
            'expected_impact': {
                'prob_loss_reduction': stats.get('prob_loss', 0) * 0.5,
                'expected_savings_mxn': expected_savings,
                'implementation_cost_mxn': 15000,
                'roi_estimated': round(expected_savings / 15000, 2) if expected_savings else 0,
            }
        }

    def _build_from_legacy_format(self, rule: Dict, stats: Dict,
                                   primary_driver: str,
                                   primary_importance: float) -> Dict:
        """Construye recomendacion desde formato legacy (rule_id/severity/recommendation_template)."""
        template = rule.get('recommendation_template', '')
        try:
            description = template.format(
                prob_loss=stats.get('prob_loss', 0),
                primary_driver=primary_driver,
                primary_importance=primary_importance,
                **stats
            )
        except (KeyError, ValueError):
            description = template

        severity = rule.get('severity', 'MEDIO')
        prob_loss = stats.get('prob_loss', 0)
        if severity == 'CRÍTICO' or prob_loss > 0.30:
            priority_int = 1
        elif severity == 'ALTO' or prob_loss > 0.15:
            priority_int = 2
        else:
            priority_int = 3

        actions = self._generate_action_steps(primary_driver)
        expected_savings = abs(stats.get('var_95', 0)) * 0.3

        return {
            'rule_id': rule.get('rule_id', 'R_LEGACY'),
            'priority': priority_int,
            'category': rule.get('category', 'general'),
            'title': f"Mitigar Exposicion en {primary_driver}",
            'description': description,
            'actions': actions,
            'expected_impact': {
                'prob_loss_reduction': stats.get('prob_loss', 0) * primary_importance * 0.5,
                'expected_savings_mxn': expected_savings,
                'implementation_cost_mxn': 15000,
                'roi_estimated': round(expected_savings / 15000, 2) if expected_savings else 0,
            }
        }

    def _fallback_recommendation(self) -> Dict:
        return {
            'rule_id': 'R_FALLBACK',
            'priority': 3,
            'category': 'monitoring',
            'title': 'Monitoreo continuo recomendado',
            'description': 'Los indicadores estan dentro de parametros aceptables. '
                           'Se recomienda revision periodica del modelo.',
            'actions': self._normalize_actions([
                'Revisar resultados de simulacion periodicamente',
                'Actualizar datos historicos mensualmente',
                'Ajustar parametros segun cambios operativos',
            ]),
            'expected_impact': {
                'prob_loss_reduction': 0,
                'expected_savings_mxn': 0,
                'implementation_cost_mxn': 0,
                'roi_estimated': 0,
            }
        }

    # ── Utilidades ───────────────────────────────────────────────────────

    def _normalize_actions(self, raw_actions: List, primary_driver: str = '') -> List[Dict]:
        """
        Convierte acciones a formato estandar de lista de dicts.

        Acepta:
          - Lista de strings: ["Revisar costos", "Analizar riesgo"]
          - Lista de dicts ya normalizados: [{"step": 1, "action": "...", "responsible": "..."}]
        """
        normalized = []
        responsibles = ['CFO', 'Gerente de Compras', 'CFO + Operaciones', 'Direccion General']

        for idx, action in enumerate(raw_actions):
            if isinstance(action, dict) and 'step' in action:
                # Ya esta en formato correcto
                normalized.append(action)
            elif isinstance(action, str):
                normalized.append({
                    'step': idx + 1,
                    'action': action,
                    'responsible': responsibles[idx % len(responsibles)],
                })
            # Ignorar otros tipos silenciosamente

        return normalized

    def _generate_action_steps(self, primary_driver: str) -> List[Dict]:
        return [
            {'step': 1, 'action': f'Analizar exposicion actual en {primary_driver}',
             'responsible': 'CFO', 'deadline_days': 3},
            {'step': 2, 'action': f'Negociar contratos forward para {primary_driver}',
             'responsible': 'Gerente de Compras', 'deadline_days': 14},
            {'step': 3, 'action': 'Implementar cobertura y monitorear resultados',
             'responsible': 'CFO + Operaciones', 'deadline_days': 30},
        ]

    def _evaluate_condition(self, condition: str, namespace: Dict) -> bool:
        try:
            return bool(eval(condition, {"__builtins__": {}, "abs": abs}, namespace))
        except Exception as e:
            print(f"Error evaluando condicion '{condition}': {e}")
            return False
