from typing import Dict, List, Tuple


class ExecutiveDashboardEngine:
    """
    Transforma resultados de Monte Carlo y analisis estrategico en un
    dashboard ejecutivo de alto nivel: health score, KPIs con semaforo
    y briefing en lenguaje de negocio.
    """

    # Umbrales de clasificacion del Business Health Score
    HEALTH_LEVELS = [
        (80, "SALUDABLE",   "#27AE60", "La operacion muestra solidez financiera."),
        (60, "ESTABLE",     "#2ECC71", "Resultados aceptables con riesgos manejables."),
        (40, "VULNERABLE",  "#F39C12", "Existen presiones que requieren atencion."),
        (20, "EN RIESGO",   "#E67E22", "Riesgo significativo. Accion recomendada."),
        (0,  "CRITICO",     "#E74C3C", "Situacion critica. Requiere intervencion inmediata."),
    ]

    def __init__(
        self,
        monte_carlo_results: Dict,
        strategic_analysis: Dict = None,
        config=None,
    ):
        self.stats = monte_carlo_results.get('statistics', {})
        self.sensitivity = monte_carlo_results.get('sensitivity', {})
        self.strategic = strategic_analysis or {}
        self.config = config

    # ──────────────────────────────────────────────────────────────────────
    # API PUBLICA
    # ──────────────────────────────────────────────────────────────────────

    def generate(self) -> Dict:
        """Genera el paquete completo de datos para el dashboard ejecutivo."""
        score, level = self._compute_health_score()
        kpis = self._build_executive_kpis()
        briefing = self._build_executive_briefing(score, level)
        highlights = self._build_strategic_highlights()

        return {
            'health_score': score,
            'health_level': level,
            'executive_kpis': kpis,
            'executive_briefing': briefing,
            'strategic_highlights': highlights,
        }

    # ──────────────────────────────────────────────────────────────────────
    # BUSINESS HEALTH SCORE (0–100)
    # ──────────────────────────────────────────────────────────────────────

    def _compute_health_score(self) -> Tuple[int, Dict]:
        """
        Calcula el Business Health Score penalizando los factores de riesgo clave.

        Logica:
          - Base: 100 puntos
          - prob_loss:    hasta -40 pts (lineal 0%→40%)
          - P10 negativo: -15 pts adicionales
          - volatilidad:  hasta -20 pts (CV 0→1)
          - VaR relativo: hasta -15 pts  (VaR > 30% del valor esperado)
          Bonus:
          - Sesgo positivo (P90 > 2 × |P10|): +5 pts
        """
        stats = self.stats
        score = 100.0

        prob_loss = stats.get('prob_loss', 0)
        mean = stats.get('mean', 0)
        std = stats.get('std', 0)
        p10 = stats.get('p10', 0)
        p90 = stats.get('p90', 0)
        var_95 = stats.get('var_95', 0)

        # Penalizacion por probabilidad de perdida (max -40)
        score -= min(prob_loss * 100, 40)

        # Penalizacion adicional si P10 es negativo
        if p10 < 0:
            score -= 15

        # Penalizacion por volatilidad (CV, max -20)
        cv = abs(std / mean) if mean != 0 else 0
        score -= min(cv * 20, 20)

        # Penalizacion por VaR relativo (max -15)
        if mean != 0:
            var_ratio = abs(var_95 / mean)
            score -= min(var_ratio * 15, 15)

        # Bonus por sesgo positivo
        if p90 > 0 and p10 < 0 and p90 > 2 * abs(p10):
            score += 5
        elif p90 > 0 and p10 >= 0:
            score += 5  # Ambos escenarios positivos

        score = max(0, min(100, round(score)))
        level = self._score_to_level(score)
        return score, level

    def _score_to_level(self, score: int) -> Dict:
        for threshold, label, color, message in self.HEALTH_LEVELS:
            if score >= threshold:
                return {
                    'label': label,
                    'color': color,
                    'message': message,
                    'threshold': threshold,
                }
        return {
            'label': 'CRITICO',
            'color': '#E74C3C',
            'message': 'Situacion critica. Requiere intervencion inmediata.',
            'threshold': 0,
        }

    # ──────────────────────────────────────────────────────────────────────
    # EXECUTIVE KPIs (semaforo verde / amarillo / rojo)
    # ──────────────────────────────────────────────────────────────────────

    def _build_executive_kpis(self) -> List[Dict]:
        stats = self.stats
        mean = stats.get('mean', 0)
        std = stats.get('std', 0)
        p10 = stats.get('p10', 0)
        p50 = stats.get('p50', mean)
        p90 = stats.get('p90', 0)
        prob_loss = stats.get('prob_loss', 0)
        var_95 = stats.get('var_95', 0)
        cv = abs(std / mean) if mean != 0 else 0

        # Umbrales desde config si existen
        threshold_loss = 0.25
        if self.config:
            threshold_loss = self.config.get('thresholds.critical_loss_prob', 0.25)

        kpis = [
            {
                'name': 'Resultado Esperado',
                'value': f"${p50:,.0f}",
                'detail': f"Rango P10–P90: ${p10:,.0f} → ${p90:,.0f}",
                'status': self._traffic_light(p50, green_if=lambda v: v > 0, yellow_if=lambda v: v > -p90 * 0.1),
                'icon': '💰',
            },
            {
                'name': 'Probabilidad de Perdida',
                'value': f"{prob_loss:.1%}",
                'detail': f"Umbral critico: {threshold_loss:.0%}",
                'status': self._traffic_light(
                    prob_loss,
                    green_if=lambda v: v < threshold_loss * 0.5,
                    yellow_if=lambda v: v < threshold_loss,
                ),
                'icon': '⚠️',
            },
            {
                'name': 'Peor Escenario (P10)',
                'value': f"${p10:,.0f}",
                'detail': '1 de cada 10 meses podria caer aqui',
                'status': self._traffic_light(p10, green_if=lambda v: v > 0, yellow_if=lambda v: v > -abs(p50) * 0.2),
                'icon': '📉',
            },
            {
                'name': 'Estabilidad del Negocio',
                'value': f"{max(0, (1 - cv)) * 100:.0f} / 100",
                'detail': f"Coeficiente de variacion: {cv:.1%}",
                'status': self._traffic_light(cv, green_if=lambda v: v < 0.20, yellow_if=lambda v: v < 0.40,
                                               invert=True),
                'icon': '📊',
            },
            {
                'name': 'Exposicion al Riesgo (VaR 95%)',
                'value': f"${abs(var_95):,.0f}",
                'detail': 'Perdida maxima en el 95% de escenarios',
                'status': self._traffic_light(
                    abs(var_95),
                    green_if=lambda v: v < abs(p50) * 0.3,
                    yellow_if=lambda v: v < abs(p50) * 0.7,
                    invert=True,
                ),
                'icon': '🛡️',
            },
            {
                'name': 'Potencial Alcista (P90)',
                'value': f"${p90:,.0f}",
                'detail': f"Upside vs resultado base: +${max(0, p90 - p50):,.0f}",
                'status': self._traffic_light(p90, green_if=lambda v: v > p50 * 1.5, yellow_if=lambda v: v > p50),
                'icon': '🚀',
            },
        ]
        return kpis

    @staticmethod
    def _traffic_light(value, green_if, yellow_if, invert: bool = False) -> str:
        try:
            if green_if(value):
                return 'green'
            elif yellow_if(value):
                return 'yellow'
            else:
                return 'red'
        except Exception:
            return 'yellow'

    # ──────────────────────────────────────────────────────────────────────
    # EXECUTIVE BRIEFING (lenguaje de negocio para C-suite)
    # ──────────────────────────────────────────────────────────────────────

    def _build_executive_briefing(self, score: int, level: Dict) -> List[str]:
        stats = self.stats
        p50 = stats.get('p50', stats.get('mean', 0))
        p10 = stats.get('p10', 0)
        p90 = stats.get('p90', 0)
        prob_loss = stats.get('prob_loss', 0)
        mean = stats.get('mean', 0)
        std = stats.get('std', 0)
        cv = abs(std / mean) if mean != 0 else 0

        briefing = []

        # Punto 1: Estado general
        if score >= 80:
            briefing.append(
                f"El negocio opera en condicion SALUDABLE con un resultado base proyectado "
                f"de ${p50:,.0f}. El riesgo de perdida es bajo ({prob_loss:.1%})."
            )
        elif score >= 60:
            briefing.append(
                f"La operacion es ESTABLE. El resultado esperado es ${p50:,.0f} con una "
                f"probabilidad de perdida de {prob_loss:.1%}, dentro de parametros aceptables."
            )
        elif score >= 40:
            briefing.append(
                f"La situacion es VULNERABLE. Existe un {prob_loss:.1%} de probabilidad de "
                f"perdida. El resultado base es ${p50:,.0f} pero con alta incertidumbre."
            )
        else:
            briefing.append(
                f"ATENCION: El negocio esta EN RIESGO con {prob_loss:.1%} de probabilidad de "
                f"perdida. El escenario pesimista proyecta ${p10:,.0f}. Se requiere accion inmediata."
            )

        # Punto 2: Rango de escenarios
        rango = p90 - p10
        if rango > 0:
            briefing.append(
                f"El rango de resultados posibles oscila entre ${p10:,.0f} (pesimista) "
                f"y ${p90:,.0f} (optimista), una diferencia de ${rango:,.0f}. "
                + ("La variabilidad es alta — el negocio es sensible a factores externos."
                   if cv > 0.35 else
                   "La variabilidad es moderada y manejable.")
            )

        # Punto 3: Recomendacion de accion del Strategic Advisor (si existe)
        sa_headline = self.strategic.get('executive_summary', {}).get('headline', '')
        sa_key_message = self.strategic.get('executive_summary', {}).get('key_message', '')
        if sa_headline:
            briefing.append(sa_headline)
        elif sa_key_message:
            briefing.append(sa_key_message)
        else:
            # Punto 3 generado internamente
            if prob_loss > 0.25:
                briefing.append(
                    "Accion recomendada: Revisar la estructura de costos y evaluar "
                    "estrategias de mitigacion de riesgo con el equipo de consultoria."
                )
            else:
                briefing.append(
                    "El equipo puede enfocarse en capturar el escenario optimista "
                    f"(${p90:,.0f}). Identifica las palancas de crecimiento con tu consultor."
                )

        return briefing

    # ──────────────────────────────────────────────────────────────────────
    # HIGHLIGHTS ESTRATEGICOS (extracto del Strategic Advisor para ejecutivos)
    # ──────────────────────────────────────────────────────────────────────

    def _build_strategic_highlights(self) -> List[Dict]:
        """Extrae las top 3 acciones rapidas del Strategic Advisor."""
        if not self.strategic or 'error' in self.strategic:
            return []

        highlights = []

        # Quick wins del Opportunity Analysis
        quick_wins = self.strategic.get('opportunity_analysis', {}).get('quick_wins', [])
        for qw in quick_wins[:2]:
            highlights.append({'type': 'quick_win', 'text': qw, 'icon': '✅'})

        # Top recomendacion del Strategic Advisor
        recs = self.strategic.get('strategic_recommendations', [])
        if recs:
            top_rec = recs[0]
            actions = top_rec.get('action_items', [])
            if actions:
                highlights.append({
                    'type': 'priority_action',
                    'text': f"[PRIORIDAD 1] {actions[0]}",
                    'icon': '🎯',
                })

        # Proximos pasos inmediatos
        this_week = self.strategic.get('next_steps', {}).get('this_week', [])
        for step in this_week[:1]:
            highlights.append({'type': 'next_step', 'text': step, 'icon': '📅'})

        return highlights[:4]
