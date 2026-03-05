"""
Decision Intelligence Engine - Fase 4
Genera recomendaciones prescriptivas basadas en reglas de negocio
"""

from typing import Dict, List, Any
import pandas as pd
from src.configuration_manager import ConfigurationManager

class DecisionIntelligenceEngine:
    """Motor de recomendaciones prescriptivas."""
    
    def __init__(self, config: ConfigurationManager):
        self.config = config
        self.decision_rules = self._load_decision_rules()
    
    def _load_decision_rules(self) -> List[Dict]:
        rules = self.config.get('decision_rules', [])
        if not rules:
            print("⚠️ No hay decision_rules en YAML. Usando reglas default.")
            return self._get_default_rules()
        return rules
    
    def _get_default_rules(self) -> List[Dict]:
        return [{
            'rule_id': 'R001_DEFAULT',
            'condition': 'prob_loss > 0.15',
            'severity': 'ALTO',
            'category': 'financial_risk',
            'recommendation_template': (
                'Probabilidad de pérdida elevada ({prob_loss:.1%}). '
                'Revisar estructura de costos y estrategia de pricing.'
            )
        }]
    
    def generate_recommendations(self, stats: Dict[str, float], sensitivity: pd.DataFrame) -> List[Dict[str, Any]]:
        recommendations = []
        primary_driver = sensitivity.iloc[0]['variable']
        primary_importance = sensitivity.iloc[0]['importance']
        
        for rule in self.decision_rules:
            if self._evaluate_condition(rule['condition'], stats):
                rec = self._build_recommendation(rule, stats, primary_driver, primary_importance)
                recommendations.append(rec)
                
        recommendations.sort(key=lambda x: x['priority'])
        return recommendations
    
    def _evaluate_condition(self, condition: str, stats: Dict) -> bool:
        try:
            return eval(condition, {"__builtins__": {}}, stats)
        except Exception as e:
            print(f"⚠️ Error evaluando condición '{condition}': {e}")
            return False
            
    def _build_recommendation(self, rule: Dict, stats: Dict, primary_driver: str, primary_importance: float) -> Dict:
        rec_template = rule.get('recommendation_template', '')
        description = rec_template.format(
            prob_loss=stats['prob_loss'],
            primary_driver=primary_driver,
            primary_importance=primary_importance,
            **stats
        )
        
        return {
            'rule_id': rule['rule_id'],
            'priority': self._calculate_priority(rule, stats),
            'category': rule.get('category', 'general'),
            'title': f"Mitigar Exposición en {primary_driver}",
            'description': description,
            'actions': self._generate_action_steps(primary_driver, stats),
            'expected_impact': self._estimate_impact(primary_driver, primary_importance, stats)
        }

    def _calculate_priority(self, rule: Dict, stats: Dict) -> int:
        severity = rule.get('severity', 'MEDIO')
        prob_loss = stats['prob_loss']
        if severity == 'CRÍTICO' or prob_loss > 0.30: return 1
        elif severity == 'ALTO' or prob_loss > 0.15: return 2
        return 3

    def _generate_action_steps(self, primary_driver: str, stats: Dict) -> List[Dict]:
        return [
            {'step': 1, 'action': f'Analizar exposición actual en {primary_driver}', 'responsible': 'CFO', 'deadline_days': 3},
            {'step': 2, 'action': f'Negociar contratos forward para {primary_driver}', 'responsible': 'Gerente de Compras', 'deadline_days': 14},
            {'step': 3, 'action': 'Implementar cobertura y monitorear resultados', 'responsible': 'CFO + Operaciones', 'deadline_days': 30}
        ]

    def _estimate_impact(self, primary_driver: str, importance: float, stats: Dict) -> Dict:
        current_prob_loss = stats['prob_loss']
        expected_reduction = current_prob_loss * importance * 0.5
        expected_savings = abs(stats['var_95']) * 0.3
        implementation_cost = 15000
        roi = expected_savings / implementation_cost if implementation_cost > 0 else 0
        
        return {
            'prob_loss_reduction': expected_reduction,
            'expected_savings_mxn': expected_savings,
            'implementation_cost_mxn': implementation_cost,
            'roi_estimated': roi
        }