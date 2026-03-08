"""
Power BI Exporter — SPEC 9.4
Exporta resultados del pipeline a Excel multi-hoja compatible con Power BI.
Genera tambien un archivo CSV plano para importacion directa.
"""
import io
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
import pandas as pd


class PowerBIExporter:
    """
    Genera un archivo Excel con multiples hojas listo para conectar a Power BI.

    Hojas:
      - Summary:          KPIs ejecutivos + Health Score
      - Monte_Carlo_Data: distribución completa (muestra de 2000 puntos)
      - Percentiles:      tabla P5 a P95 en pasos de 5
      - Sensitivity:      analisis de sensibilidad
      - Recommendations:  recomendaciones estrategicas
      - Audit_Trail:      metadatos de la ejecucion
    """

    def __init__(
        self,
        client_id: str,
        client_name: str,
        stats: Dict,
        simulation_results=None,
        sensitivity=None,
        recommendations: List[Dict] = None,
        strategic_analysis: Dict = None,
        dashboard: Dict = None,
        industry: str = "General",
    ):
        self.client_id   = client_id
        self.client_name = client_name
        self.stats       = stats
        self.sim_results = simulation_results
        self.sensitivity = sensitivity
        self.recommendations = recommendations or []
        self.strategic   = strategic_analysis or {}
        self.dashboard   = dashboard or {}
        self.industry    = industry
        self.generated_at = datetime.now()

    # ──────────────────────────────────────────────────────────────────────
    # EXCEL MULTI-HOJA
    # ──────────────────────────────────────────────────────────────────────

    def export_excel(self) -> bytes:
        """Genera el archivo Excel y retorna bytes para descarga."""
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            wb = writer.book
            self._write_summary(writer, wb)
            self._write_monte_carlo_data(writer, wb)
            self._write_percentiles(writer, wb)
            self._write_sensitivity(writer, wb)
            self._write_recommendations(writer, wb)
            self._write_audit_trail(writer, wb)
        buffer.seek(0)
        return buffer.getvalue()

    # ──────────────────────────────────────────────────────────────────────
    # HOJAS
    # ──────────────────────────────────────────────────────────────────────

    def _write_summary(self, writer, wb):
        stats = self.stats
        mean  = stats.get("mean", 0)
        std   = stats.get("std", 0)
        cv    = abs(std / mean) if mean != 0 else 0

        health_score = self.dashboard.get("health_score")
        health_label = self.dashboard.get("health_level", {}).get("label", "")

        rows = [
            ["SENTINEL DECISION INTELLIGENCE — REPORTE POWER BI", ""],
            ["Cliente",     self.client_name],
            ["Cliente ID",  self.client_id],
            ["Industria",   self.industry],
            ["Generado",    self.generated_at.strftime("%Y-%m-%d %H:%M:%S")],
            ["", ""],
            ["=== BUSINESS HEALTH SCORE ===", ""],
            ["Health Score",  health_score],
            ["Nivel",         health_label],
            ["", ""],
            ["=== RESULTADOS MONTE CARLO ===", ""],
            ["Resultado Promedio (Mean)",   mean],
            ["Desviacion Estandar (Std)",   std],
            ["Coeficiente de Variacion",    cv],
            ["P10 — Escenario Pesimista",   stats.get("p10", 0)],
            ["P25 — Cuartil Inferior",      stats.get("p25", 0)],
            ["P50 — Mediana (Base Case)",   stats.get("p50", mean)],
            ["P75 — Cuartil Superior",      stats.get("p75", 0)],
            ["P90 — Escenario Optimista",   stats.get("p90", 0)],
            ["", ""],
            ["=== METRICAS DE RIESGO ===", ""],
            ["Probabilidad de Perdida",     stats.get("prob_loss", 0)],
            ["VaR 95%",                     stats.get("var_95", 0)],
            ["CVaR 95% (Expected Shortfall)", stats.get("cvar_95", 0)],
        ]

        df = pd.DataFrame(rows, columns=["Metrica", "Valor"])
        df.to_excel(writer, sheet_name="Summary", index=False)

        ws = writer.sheets["Summary"]
        # Formatos
        hdr_fmt = wb.add_format({"bold": True, "bg_color": "#1A1A2E",
                                  "font_color": "#D4AF37", "font_size": 14})
        sect_fmt = wb.add_format({"bold": True, "bg_color": "#2C3E7A",
                                   "font_color": "#FFFFFF"})
        num_fmt  = wb.add_format({"num_format": "#,##0.00"})
        pct_fmt  = wb.add_format({"num_format": "0.00%"})

        ws.set_column("A:A", 35)
        ws.set_column("B:B", 20, num_fmt)
        ws.write(0, 0, "SENTINEL DECISION INTELLIGENCE — REPORTE POWER BI", hdr_fmt)

    def _write_monte_carlo_data(self, writer, wb):
        if self.sim_results is None:
            pd.DataFrame({"nota": ["Sin datos de simulacion"]}).to_excel(
                writer, sheet_name="Monte_Carlo_Data", index=False)
            return

        try:
            if hasattr(self.sim_results, "values"):
                outcomes = self.sim_results["outcome"].values
            elif isinstance(self.sim_results, np.ndarray):
                outcomes = self.sim_results
            else:
                outcomes = np.array(list(self.sim_results))

            # Muestra de 2000 puntos para Power BI (no saturar)
            rng = np.random.default_rng(42)
            if len(outcomes) > 2000:
                idx = rng.choice(len(outcomes), 2000, replace=False)
                sample = np.sort(outcomes[idx])
            else:
                sample = np.sort(outcomes)

            percentile_rank = np.arange(1, len(sample) + 1) / len(sample) * 100

            df = pd.DataFrame({
                "Simulacion_ID":      range(1, len(sample) + 1),
                "Resultado":          sample.round(2),
                "Percentil":          percentile_rank.round(2),
                "Es_Perdida":         (sample < 0).astype(int),
            })
            df.to_excel(writer, sheet_name="Monte_Carlo_Data", index=False)

            ws = writer.sheets["Monte_Carlo_Data"]
            hdr_fmt = wb.add_format({"bold": True, "bg_color": "#1A1A2E",
                                      "font_color": "#D4AF37"})
            ws.set_column("A:A", 15)
            ws.set_column("B:B", 18)
            ws.set_column("C:D", 12)

        except Exception as e:
            pd.DataFrame({"error": [str(e)]}).to_excel(
                writer, sheet_name="Monte_Carlo_Data", index=False)

    def _write_percentiles(self, writer, wb):
        stats = self.stats
        percentile_keys = [5, 10, 15, 20, 25, 30, 35, 40, 45,
                           50, 55, 60, 65, 70, 75, 80, 85, 90, 95]
        rows = []

        # Usar los que tenemos en stats
        key_map = {5: "var_95", 10: "p10", 25: "p25", 50: "p50",
                   75: "p75", 90: "p90"}

        mean = stats.get("mean", 0)
        std  = stats.get("std", 1)

        for p in percentile_keys:
            if p in key_map and key_map[p] in stats:
                value = stats[key_map[p]]
            else:
                # Interpolar con aproximacion normal
                from scipy.stats import norm as _norm
                try:
                    value = _norm.ppf(p / 100, loc=mean, scale=std)
                except Exception:
                    value = mean + std * (p - 50) / 34

            rows.append({
                "Percentil":        p,
                "Resultado":        round(value, 2),
                "Es_Perdida":       int(value < 0),
                "Descripcion":      self._percentile_label(p),
            })

        df = pd.DataFrame(rows)
        df.to_excel(writer, sheet_name="Percentiles", index=False)
        ws = writer.sheets["Percentiles"]
        ws.set_column("A:A", 12)
        ws.set_column("B:B", 18)
        ws.set_column("C:D", 15)

    @staticmethod
    def _percentile_label(p: int) -> str:
        labels = {5: "VaR 95% (Perdida max)", 10: "Escenario Pesimista",
                  25: "Cuartil Inferior", 50: "Mediana / Base Case",
                  75: "Cuartil Superior", 90: "Escenario Optimista",
                  95: "Upside Maximo"}
        return labels.get(p, "")

    def _write_sensitivity(self, writer, wb):
        rows = []
        if self.sensitivity is not None:
            try:
                if hasattr(self.sensitivity, "iterrows"):
                    for _, row in self.sensitivity.iterrows():
                        rows.append({
                            "Variable":    row.get("variable", ""),
                            "Importancia": round(row.get("importance", 0), 4),
                            "Rank":        len(rows) + 1,
                        })
                elif isinstance(self.sensitivity, dict):
                    sorted_s = sorted(self.sensitivity.items(),
                                      key=lambda x: abs(x[1]), reverse=True)
                    for rank, (var, imp) in enumerate(sorted_s, 1):
                        rows.append({"Variable": var, "Importancia": round(imp, 4),
                                     "Rank": rank})
            except Exception:
                pass

        if not rows:
            rows = [{"Variable": "Sin datos", "Importancia": 0, "Rank": 1}]

        pd.DataFrame(rows).to_excel(writer, sheet_name="Sensitivity", index=False)
        ws = writer.sheets["Sensitivity"]
        ws.set_column("A:A", 30)
        ws.set_column("B:C", 15)

    def _write_recommendations(self, writer, wb):
        rows = []

        # Strategic Advisor (Fase 5)
        sa_recs = self.strategic.get("strategic_recommendations", [])
        for rec in sa_recs:
            actions = rec.get("action_items", [])
            rows.append({
                "Fuente":    "Strategic Advisor (Llama 3.3-70B)",
                "Prioridad": rec.get("priority", ""),
                "Titulo":    rec.get("title", ""),
                "Horizonte": rec.get("implementation_horizon", ""),
                "Confianza": rec.get("confidence", ""),
                "Rationale": rec.get("rationale", ""),
                "Impacto":   rec.get("expected_impact", ""),
                "Acciones":  " | ".join(actions[:3]),
            })

        # Decision Intelligence (Fase 4) como fallback
        if not rows:
            for rec in self.recommendations:
                actions = rec.get("actions", [])
                actions_text = " | ".join(
                    a["action"] for a in actions[:3] if isinstance(a, dict)
                )
                rows.append({
                    "Fuente":    "Decision Intelligence Engine",
                    "Prioridad": rec.get("priority", ""),
                    "Titulo":    rec.get("title", ""),
                    "Horizonte": "",
                    "Confianza": "",
                    "Rationale": rec.get("description", ""),
                    "Impacto":   "",
                    "Acciones":  actions_text,
                })

        if not rows:
            rows = [{"Fuente": "Sin recomendaciones", "Prioridad": "",
                     "Titulo": "", "Horizonte": "", "Confianza": "",
                     "Rationale": "", "Impacto": "", "Acciones": ""}]

        pd.DataFrame(rows).to_excel(writer, sheet_name="Recommendations", index=False)
        ws = writer.sheets["Recommendations"]
        ws.set_column("A:H", 25)

    def _write_audit_trail(self, writer, wb):
        rows = [
            {"Campo": "Plataforma",        "Valor": "Sentinel Decision Intelligence"},
            {"Campo": "Version",           "Valor": "Sprint 6"},
            {"Campo": "Cliente ID",        "Valor": self.client_id},
            {"Campo": "Cliente Nombre",    "Valor": self.client_name},
            {"Campo": "Industria",         "Valor": self.industry},
            {"Campo": "Generado",          "Valor": self.generated_at.isoformat()},
            {"Campo": "Simulaciones",      "Valor": 10000},
            {"Campo": "Motor",             "Valor": "Monte Carlo + Llama 3.3-70B"},
            {"Campo": "Empresa",           "Valor": "Evangelista & Co."},
            {"Campo": "Confidencialidad",  "Valor": "Documento Confidencial"},
        ]
        pd.DataFrame(rows).to_excel(writer, sheet_name="Audit_Trail", index=False)

    # ──────────────────────────────────────────────────────────────────────
    # CSV PLANO (para importacion directa a Power BI Desktop)
    # ──────────────────────────────────────────────────────────────────────

    def export_csv_summary(self) -> bytes:
        """Exporta el Summary como CSV UTF-8 para Power BI Desktop."""
        stats = self.stats
        mean  = stats.get("mean", 0)
        std   = stats.get("std", 0)
        rows = [{
            "client_id":     self.client_id,
            "client_name":   self.client_name,
            "industry":      self.industry,
            "generated_at":  self.generated_at.isoformat(),
            "health_score":  self.dashboard.get("health_score"),
            "health_label":  self.dashboard.get("health_level", {}).get("label", ""),
            "mean":          round(mean, 2),
            "std":           round(std, 2),
            "cv":            round(abs(std / mean) if mean != 0 else 0, 4),
            "p10":           round(stats.get("p10", 0), 2),
            "p25":           round(stats.get("p25", 0), 2),
            "p50":           round(stats.get("p50", mean), 2),
            "p75":           round(stats.get("p75", 0), 2),
            "p90":           round(stats.get("p90", 0), 2),
            "prob_loss":     round(stats.get("prob_loss", 0), 4),
            "var_95":        round(stats.get("var_95", 0), 2),
            "cvar_95":       round(stats.get("cvar_95", 0), 2),
        }]
        import io as _io
        buf = _io.StringIO()
        pd.DataFrame(rows).to_csv(buf, index=False, encoding="utf-8")
        return buf.getvalue().encode("utf-8")
