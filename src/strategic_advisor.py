import json
import re
from typing import Dict, List, Optional
from groq import Groq


class StrategicAdvisor:
    """Senior Business Strategist powered by Llama 3.3-70B via GROQ."""

    MODEL = "llama-3.3-70b-versatile"
    TEMPERATURE = 0.4
    MAX_TOKENS = 4096

    def __init__(self, groq_api_key: str):
        self.client = Groq(api_key=groq_api_key)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_strategic_recommendations(
        self,
        monte_carlo_results: dict,
        kpis: dict,
        projections: dict,
        business_drivers: dict,
        industry: str,
        client_name: str,
        client_context: str = "",
    ) -> dict:
        messages = [
            {"role": "system", "content": self._build_system_prompt(industry)},
            {"role": "user", "content": self._build_context_prompt(
                monte_carlo_results, kpis, projections,
                business_drivers, client_name, client_context, industry
            )},
            {"role": "user", "content": self._build_task_prompt()},
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=messages,
                temperature=self.TEMPERATURE,
                max_tokens=self.MAX_TOKENS,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content
            data = json.loads(raw)
        except json.JSONDecodeError:
            # Try to extract JSON from the text
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            data = json.loads(match.group()) if match else {}
        except Exception as e:
            data = {"error": str(e)}

        return self._validate_and_enrich(data, monte_carlo_results)

    # ------------------------------------------------------------------
    # Prompt builders
    # ------------------------------------------------------------------

    def _build_system_prompt(self, industry: str) -> str:
        return f"""You are a Senior Business Strategist and Management Consultant with 20+ years of experience in {industry}.

Your expertise includes:
- McKinsey-style strategic analysis (MECE frameworks, issue trees)
- Monte Carlo risk modeling interpretation
- Financial scenario planning and sensitivity analysis
- Operational excellence and KPI design
- Executive communication and board-level reporting

You communicate with precision, using data to support every recommendation. You translate quantitative uncertainty into actionable business decisions. You think in terms of risk-adjusted returns, portfolio effects, and strategic optionality.

IMPORTANT: Always respond with valid JSON only. No preamble, no markdown, no explanations outside the JSON structure."""

    def _build_context_prompt(
        self,
        monte_carlo_results: dict,
        kpis: dict,
        projections: dict,
        business_drivers: dict,
        client_name: str,
        client_context: str,
        industry: str,
    ) -> str:
        stats = monte_carlo_results.get('statistics', {})
        sensitivity = monte_carlo_results.get('sensitivity', {})

        mean = stats.get('mean', stats.get('expected_value', 0))
        std = stats.get('std', 0)
        p10 = stats.get('p10', 0)
        p50 = stats.get('p50', mean)
        p90 = stats.get('p90', 0)
        prob_loss = stats.get('prob_loss', 0)
        var_95 = stats.get('var_95', 0)

        top_drivers = []
        if isinstance(sensitivity, dict):
            sorted_drivers = sorted(
                sensitivity.items(), key=lambda x: abs(x[1]), reverse=True
            )[:5]
            top_drivers = [{"variable": k, "impact": round(v, 4)} for k, v in sorted_drivers]

        context = {
            "client": {
                "name": client_name,
                "industry": industry,
                "context": client_context,
            },
            "monte_carlo_results": {
                "expected_outcome": round(mean, 2),
                "std_deviation": round(std, 2),
                "pessimistic_p10": round(p10, 2),
                "base_case_p50": round(p50, 2),
                "optimistic_p90": round(p90, 2),
                "probability_of_loss": round(prob_loss, 4),
                "value_at_risk_95": round(var_95, 2),
                "top_sensitivity_drivers": top_drivers,
            },
            "kpis": kpis,
            "projections": projections,
            "business_drivers": business_drivers,
        }

        return f"BUSINESS CONTEXT:\n{json.dumps(context, ensure_ascii=False, indent=2)}"

    def _build_task_prompt(self) -> str:
        return """Based on the business context and Monte Carlo results provided, generate a comprehensive strategic analysis.

Return a JSON object with exactly this structure:

{
  "executive_summary": {
    "headline": "One-sentence strategic assessment",
    "risk_profile": "LOW | MODERATE | HIGH | CRITICAL",
    "confidence_level": "HIGH | MEDIUM | LOW",
    "key_message": "2-3 sentence narrative for the executive team"
  },
  "strategic_recommendations": [
    {
      "priority": 1,
      "title": "Recommendation title",
      "rationale": "Why this recommendation based on the data",
      "expected_impact": "Quantified expected impact if possible",
      "implementation_horizon": "IMMEDIATE (0-30d) | SHORT_TERM (1-3m) | MEDIUM_TERM (3-6m) | LONG_TERM (6m+)",
      "confidence": "HIGH | MEDIUM | LOW",
      "action_items": ["Specific action 1", "Specific action 2", "Specific action 3"]
    }
  ],
  "risk_analysis": {
    "primary_risks": [
      {
        "risk": "Risk description",
        "probability": "HIGH | MEDIUM | LOW",
        "impact": "HIGH | MEDIUM | LOW",
        "mitigation": "Specific mitigation strategy"
      }
    ],
    "scenario_analysis": {
      "bear_case": "Description of pessimistic scenario and response",
      "base_case": "Description of most likely scenario",
      "bull_case": "Description of optimistic scenario and how to capture upside"
    }
  },
  "opportunity_analysis": {
    "quick_wins": ["Action that can drive results in 30 days", "..."],
    "strategic_bets": ["Higher-risk, higher-reward opportunity", "..."],
    "defensive_moves": ["Action to protect current position", "..."]
  },
  "kpi_targets": [
    {
      "kpi": "KPI name",
      "current_baseline": "Current value or unknown",
      "target_90d": "Target in 90 days",
      "target_180d": "Target in 180 days",
      "owner": "Role responsible"
    }
  ],
  "next_steps": {
    "this_week": ["Immediate action 1", "Immediate action 2"],
    "this_month": ["30-day milestone 1", "30-day milestone 2"],
    "this_quarter": ["90-day goal 1", "90-day goal 2"]
  }
}

Provide 3-5 strategic recommendations ranked by priority. Be specific, data-driven, and actionable."""

    # ------------------------------------------------------------------
    # Validation and enrichment
    # ------------------------------------------------------------------

    def _validate_and_enrich(self, data: dict, monte_carlo_results: dict) -> dict:
        # Ensure required top-level keys exist
        required_sections = [
            "executive_summary", "strategic_recommendations",
            "risk_analysis", "opportunity_analysis", "kpi_targets", "next_steps"
        ]
        for section in required_sections:
            if section not in data:
                data[section] = self._get_default_section(section)

        # Validate executive_summary
        summary = data.get("executive_summary", {})
        if not isinstance(summary, dict):
            data["executive_summary"] = self._get_default_section("executive_summary")
        else:
            valid_risk = {"LOW", "MODERATE", "HIGH", "CRITICAL"}
            if summary.get("risk_profile") not in valid_risk:
                stats = monte_carlo_results.get("statistics", {})
                prob_loss = stats.get("prob_loss", 0)
                summary["risk_profile"] = (
                    "CRITICAL" if prob_loss > 0.30
                    else "HIGH" if prob_loss > 0.15
                    else "MODERATE" if prob_loss > 0.05
                    else "LOW"
                )

        # Validate recommendations list
        recs = data.get("strategic_recommendations", [])
        if not isinstance(recs, list) or len(recs) == 0:
            data["strategic_recommendations"] = self._get_default_section("strategic_recommendations")
        else:
            valid_horizons = {"IMMEDIATE", "SHORT_TERM", "MEDIUM_TERM", "LONG_TERM"}
            valid_confidence = {"HIGH", "MEDIUM", "LOW"}
            for i, rec in enumerate(recs):
                if not isinstance(rec, dict):
                    continue
                rec.setdefault("priority", i + 1)
                rec.setdefault("title", f"Recommendation {i + 1}")
                rec.setdefault("rationale", "")
                rec.setdefault("expected_impact", "To be quantified")
                if rec.get("implementation_horizon") not in valid_horizons:
                    rec["implementation_horizon"] = "SHORT_TERM"
                if rec.get("confidence") not in valid_confidence:
                    rec["confidence"] = "MEDIUM"
                if not isinstance(rec.get("action_items"), list):
                    rec["action_items"] = []

        # Enrich with metadata
        data["_metadata"] = {
            "model": self.MODEL,
            "temperature": self.TEMPERATURE,
            "generated_at": self._now_iso(),
        }

        return data

    def _get_default_section(self, section: str) -> dict | list:
        defaults = {
            "executive_summary": {
                "headline": "Analysis pending — insufficient data for recommendation",
                "risk_profile": "MODERATE",
                "confidence_level": "LOW",
                "key_message": "Strategic analysis could not be completed. Please review input data.",
            },
            "strategic_recommendations": [
                {
                    "priority": 1,
                    "title": "Review and validate simulation inputs",
                    "rationale": "Insufficient context to generate specific recommendations",
                    "expected_impact": "Improved forecast accuracy",
                    "implementation_horizon": "IMMEDIATE",
                    "confidence": "HIGH",
                    "action_items": [
                        "Validate business model parameters",
                        "Review historical data quality",
                        "Confirm KPI definitions with stakeholders",
                    ],
                }
            ],
            "risk_analysis": {
                "primary_risks": [],
                "scenario_analysis": {
                    "bear_case": "Downside scenario analysis not available",
                    "base_case": "Base case analysis not available",
                    "bull_case": "Upside scenario analysis not available",
                },
            },
            "opportunity_analysis": {
                "quick_wins": [],
                "strategic_bets": [],
                "defensive_moves": [],
            },
            "kpi_targets": [],
            "next_steps": {
                "this_week": [],
                "this_month": [],
                "this_quarter": [],
            },
        }
        return defaults.get(section, {})

    @staticmethod
    def _now_iso() -> str:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
