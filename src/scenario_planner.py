"""
Scenario Planner — SPEC 9.3
Permite ejecutar simulaciones what-if modificando parametros de variables
en memoria, sin tocar el YAML original.
Compara el escenario modificado vs el baseline.
"""
import copy
import numpy as np
from typing import Dict, List, Optional, Tuple


class ScenarioPlanner:
    """
    Motor de what-if analysis sobre una configuracion de variables existente.

    Uso:
        planner = ScenarioPlanner(base_config)
        planner.set_adjustment('ingresos', delta_mean_pct=+10)
        planner.set_adjustment('costos', delta_mean_pct=-5)
        results = planner.run(n_simulations=5000)
        comparison = planner.compare(baseline_stats, results['statistics'])
    """

    N_SIMULATIONS_DEFAULT = 5_000

    def __init__(self, base_config: Dict):
        """
        base_config: dict completo de la configuracion del cliente
        (output de ConfigurationManager o el dict del YAML)
        """
        self.base_config   = base_config
        self.adjustments: Dict[str, Dict] = {}  # var_name → {delta_mean_pct, delta_std_pct, ...}
        self._scenario_config: Optional[Dict] = None

    # ──────────────────────────────────────────────────────────────────────
    # CONFIGURACION DE AJUSTES
    # ──────────────────────────────────────────────────────────────────────

    def set_adjustment(
        self,
        variable: str,
        delta_mean_pct: float = 0.0,
        delta_std_pct: float = 0.0,
        delta_mean_abs: float = None,
    ):
        """
        Registra un ajuste para una variable.

        Args:
            variable:       Nombre de la variable a ajustar
            delta_mean_pct: Cambio porcentual en la media (ej. +10 = +10%)
            delta_std_pct:  Cambio porcentual en la desviacion estandar
            delta_mean_abs: Cambio absoluto en la media (anula delta_mean_pct)
        """
        self.adjustments[variable] = {
            "delta_mean_pct": delta_mean_pct,
            "delta_std_pct":  delta_std_pct,
            "delta_mean_abs": delta_mean_abs,
        }
        self._scenario_config = None  # invalidar config cacheada

    def clear_adjustments(self):
        self.adjustments = {}
        self._scenario_config = None

    def get_scenario_variables(self) -> Dict:
        """
        Devuelve el dict de variables con los ajustes aplicados.
        Util para mostrar en la UI antes de ejecutar.
        """
        variables = copy.deepcopy(self.base_config.get("variables", {}))
        for var, adj in self.adjustments.items():
            if var not in variables:
                continue
            v = variables[var]
            original_mean = v.get("mean", 0)
            original_std  = v.get("std", 0)

            # Aplicar delta de media
            if adj.get("delta_mean_abs") is not None:
                v["mean"] = original_mean + adj["delta_mean_abs"]
            elif adj.get("delta_mean_pct", 0) != 0:
                v["mean"] = original_mean * (1 + adj["delta_mean_pct"] / 100)

            # Aplicar delta de desviacion estandar
            if adj.get("delta_std_pct", 0) != 0:
                v["std"] = max(0, original_std * (1 + adj["delta_std_pct"] / 100))

        return variables

    # ──────────────────────────────────────────────────────────────────────
    # SIMULACION
    # ──────────────────────────────────────────────────────────────────────

    def run(self, n_simulations: int = N_SIMULATIONS_DEFAULT) -> Dict:
        """
        Ejecuta la simulacion Monte Carlo con los ajustes aplicados.
        Retorna dict con 'statistics' y 'samples'.
        """
        scenario_vars = self.get_scenario_variables()
        business_model_cfg = self.base_config.get("business_model", {})
        fn_str = business_model_cfg.get("function") or business_model_cfg.get("formula", "")

        if not fn_str:
            raise ValueError("business_model.function no definido en la configuracion.")

        # Compilar la funcion del modelo de negocio
        try:
            fn_code = compile(fn_str, "<scenario>", "eval")
        except SyntaxError as e:
            raise ValueError(f"Error en business_model.function: {e}")

        # Generar muestras para cada variable
        rng = np.random.default_rng()
        samples: Dict[str, np.ndarray] = {}

        for var_name, var_cfg in scenario_vars.items():
            dist = var_cfg.get("distribution", "normal")
            n = n_simulations

            try:
                if dist == "normal":
                    mean = float(var_cfg.get("mean", 0))
                    std  = float(var_cfg.get("std", 1))
                    samples[var_name] = rng.normal(mean, max(std, 0), n)

                elif dist == "triangular":
                    lo   = float(var_cfg.get("min", 0))
                    hi   = float(var_cfg.get("max", 1))
                    mode = float(var_cfg.get("mode", (lo + hi) / 2))
                    # numpy triangular usa c = (mode - left) / (right - left)
                    c = (mode - lo) / (hi - lo) if hi != lo else 0.5
                    samples[var_name] = rng.triangular(lo, mode, hi, n)

                elif dist == "uniform":
                    lo = float(var_cfg.get("min", 0))
                    hi = float(var_cfg.get("max", 1))
                    samples[var_name] = rng.uniform(lo, hi, n)

                elif dist == "lognormal":
                    mean = float(var_cfg.get("mean", 1))
                    std  = float(var_cfg.get("std", 0.3))
                    # Parametrizar lognormal con mean/std de la distribucion subyacente
                    sigma = np.sqrt(np.log(1 + (std / mean) ** 2)) if mean > 0 else std
                    mu    = np.log(mean) - sigma ** 2 / 2 if mean > 0 else 0
                    samples[var_name] = rng.lognormal(mu, sigma, n)

                elif dist == "fixed":
                    val = float(var_cfg.get("value", var_cfg.get("mean", 0)))
                    samples[var_name] = np.full(n, val)

                else:
                    # Default: normal
                    mean = float(var_cfg.get("mean", 0))
                    std  = float(var_cfg.get("std", 1))
                    samples[var_name] = rng.normal(mean, max(std, 0), n)

            except Exception:
                samples[var_name] = np.zeros(n)

        # Evaluar el modelo de negocio para cada simulacion
        outcomes = np.zeros(n_simulations)
        safe_builtins = {"abs": abs, "max": max, "min": min, "round": round}

        for i in range(n_simulations):
            ns = {var: float(arr[i]) for var, arr in samples.items()}
            ns.update(safe_builtins)
            try:
                outcomes[i] = eval(fn_code, {"__builtins__": {}}, ns)
            except Exception:
                outcomes[i] = 0.0

        stats = self._compute_stats(outcomes)
        return {"statistics": stats, "samples": outcomes}

    @staticmethod
    def _compute_stats(outcomes: np.ndarray) -> Dict:
        loss_mask = outcomes < 0
        return {
            "mean":      float(np.mean(outcomes)),
            "std":       float(np.std(outcomes)),
            "p10":       float(np.percentile(outcomes, 10)),
            "p25":       float(np.percentile(outcomes, 25)),
            "p50":       float(np.percentile(outcomes, 50)),
            "p75":       float(np.percentile(outcomes, 75)),
            "p90":       float(np.percentile(outcomes, 90)),
            "prob_loss": float(np.mean(loss_mask)),
            "var_95":    float(np.percentile(outcomes, 5)),
            "cvar_95":   float(np.mean(outcomes[outcomes <= np.percentile(outcomes, 5)])
                               if loss_mask.any() else 0),
        }

    # ──────────────────────────────────────────────────────────────────────
    # COMPARACION
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def compare(baseline_stats: Dict, scenario_stats: Dict) -> List[Dict]:
        """
        Compara baseline vs escenario y retorna lista de metricas con deltas.
        """
        metrics = [
            ("Resultado Esperado (P50)", "p50",       "$",  False),
            ("Resultado Promedio",        "mean",      "$",  False),
            ("Escenario Pesimista (P10)", "p10",       "$",  False),
            ("Escenario Optimista (P90)", "p90",       "$",  False),
            ("Probabilidad de Perdida",   "prob_loss", "%",  True),
            ("VaR 95%",                   "var_95",    "$",  True),
            ("Volatilidad (Std Dev)",     "std",       "$",  True),
        ]

        comparison = []
        for label, key, unit, lower_is_better in metrics:
            base = baseline_stats.get(key, 0)
            scen = scenario_stats.get(key, 0)
            delta_abs = scen - base
            delta_pct = (delta_abs / abs(base) * 100) if base != 0 else 0

            # Determinar si el cambio es favorable
            if lower_is_better:
                favorable = delta_abs < 0
            else:
                favorable = delta_abs > 0
            neutral = abs(delta_pct) < 0.5

            comparison.append({
                "metric":       label,
                "key":          key,
                "unit":         unit,
                "baseline":     base,
                "scenario":     scen,
                "delta_abs":    delta_abs,
                "delta_pct":    delta_pct,
                "favorable":    favorable,
                "neutral":      neutral,
            })

        return comparison
