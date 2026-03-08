"""
Config Validator — SPEC 8.2
Valida configuraciones YAML de cliente antes de ejecutar el pipeline.
Retorna un ValidationResult con errores criticos y advertencias.
"""
import ast
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ValidationResult:
    is_valid: bool = True
    errors:   List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(self, msg: str):
        self.errors.append(msg)
        self.is_valid = False

    def add_warning(self, msg: str):
        self.warnings.append(msg)

    @property
    def summary(self) -> str:
        parts = []
        if self.errors:
            parts.append(f"{len(self.errors)} error(s) critico(s)")
        if self.warnings:
            parts.append(f"{len(self.warnings)} advertencia(s)")
        return ", ".join(parts) if parts else "Configuracion valida"


# ═══════════════════════════════════════════════════════════════
# VALIDADOR PRINCIPAL
# ═══════════════════════════════════════════════════════════════

class ConfigValidator:
    """Valida un dict de configuracion de cliente (ya parseado desde YAML)."""

    REQUIRED_TOP_KEYS = ['variables', 'business_model']
    DISTRIBUTION_TYPES = {'normal', 'triangular', 'uniform', 'lognormal', 'beta', 'fixed'}
    NORMAL_PARAMS = {'mean', 'std'}
    TRIANGULAR_PARAMS = {'min', 'max', 'mode'}
    UNIFORM_PARAMS = {'min', 'max'}
    SANITY_SCALE_LIMIT = 1e10  # Si mean > 10B es problema de escala

    def validate(self, config: Dict) -> ValidationResult:
        result = ValidationResult()

        self._check_required_keys(config, result)
        self._check_client_info(config, result)
        self._check_variables(config, result)
        self._check_business_model(config, result)
        self._check_decision_rules(config, result)
        self._check_thresholds(config, result)
        self._check_simulation(config, result)

        return result

    # ──────────────────────────────────────────────────────────────────────
    # CHECKS
    # ──────────────────────────────────────────────────────────────────────

    def _check_required_keys(self, config: Dict, r: ValidationResult):
        for key in self.REQUIRED_TOP_KEYS:
            if key not in config:
                r.add_error(f"Seccion requerida ausente: '{key}'")

    def _check_client_info(self, config: Dict, r: ValidationResult):
        info = config.get('client_info') or config.get('client', {})
        if not info:
            r.add_warning("Seccion 'client_info' no encontrada. Se usaran valores por defecto.")
            return
        if not info.get('name') and not info.get('client_name'):
            r.add_warning("client_info.name esta vacio.")
        if not info.get('industry'):
            r.add_warning("client_info.industry no definido. Afecta la generacion de KPIs.")

    def _check_variables(self, config: Dict, r: ValidationResult):
        variables = config.get('variables', {})
        if not variables:
            r.add_error("'variables' esta vacio. El pipeline no puede ejecutarse sin variables.")
            return
        if not isinstance(variables, dict):
            r.add_error("'variables' debe ser un diccionario de nombre→parametros.")
            return

        for var_name, var_cfg in variables.items():
            self._check_single_variable(var_name, var_cfg, r)

    def _check_single_variable(self, name: str, cfg: Any, r: ValidationResult):
        if not isinstance(cfg, dict):
            r.add_error(f"Variable '{name}': debe ser un dict con parametros de distribucion.")
            return

        dist = cfg.get('distribution', 'normal')
        if dist not in self.DISTRIBUTION_TYPES:
            r.add_warning(f"Variable '{name}': distribucion '{dist}' no reconocida. "
                          f"Se usara 'normal'. Validas: {self.DISTRIBUTION_TYPES}")

        # Verificar parametros minimos por distribucion
        if dist == 'normal':
            if 'mean' not in cfg:
                r.add_error(f"Variable '{name}' (normal): falta 'mean'.")
            if 'std' not in cfg:
                r.add_error(f"Variable '{name}' (normal): falta 'std'. "
                            f"Std=0 causaria distribucion degenerada.")
            elif cfg.get('std', 0) < 0:
                r.add_error(f"Variable '{name}': 'std' no puede ser negativo ({cfg['std']}).")
            elif cfg.get('std', 0) == 0:
                r.add_warning(f"Variable '{name}': std=0. La variable sera constante (sin aleatoriedad).")
            # Sanity scale
            mean = cfg.get('mean', 0)
            if abs(mean) > self.SANITY_SCALE_LIMIT:
                r.add_error(f"Variable '{name}': mean={mean:,.0f} excede el limite de escala. "
                            f"Probable error en el YAML (multiplicacion por volumen).")

        elif dist == 'triangular':
            for p in self.TRIANGULAR_PARAMS:
                if p not in cfg:
                    r.add_error(f"Variable '{name}' (triangular): falta '{p}'.")
            mn, mx, mo = cfg.get('min', 0), cfg.get('max', 0), cfg.get('mode', 0)
            if mn > mx:
                r.add_error(f"Variable '{name}': min ({mn}) > max ({mx}).")
            if not (mn <= mo <= mx):
                r.add_warning(f"Variable '{name}': mode ({mo}) deberia estar entre min ({mn}) y max ({mx}).")

        elif dist == 'uniform':
            for p in self.UNIFORM_PARAMS:
                if p not in cfg:
                    r.add_error(f"Variable '{name}' (uniform): falta '{p}'.")

        elif dist == 'fixed':
            if 'value' not in cfg and 'mean' not in cfg:
                r.add_error(f"Variable '{name}' (fixed): falta 'value'.")

    def _check_business_model(self, config: Dict, r: ValidationResult):
        bm = config.get('business_model', {})
        if not bm:
            r.add_error("'business_model' esta vacio.")
            return

        fn = bm.get('function') or bm.get('formula')
        if not fn:
            r.add_error("business_model: falta 'function' (la expresion Python del modelo).")
            return

        # Intentar parsear como Python
        try:
            ast.parse(fn, mode='eval')
        except SyntaxError as e:
            r.add_error(f"business_model.function tiene error de sintaxis Python: {e}")
            return

        # Advertir si usa patrones de escala conocidos
        scale_patterns = [r'\*\s*volumen', r'\*\s*\d{3,}', r'1000\s*\*', r'\*\s*1000']
        for pattern in scale_patterns:
            if re.search(pattern, fn, re.IGNORECASE):
                r.add_warning(
                    f"business_model.function contiene multiplicacion de escala ({pattern}). "
                    "Verifica que las variables ya esten en la escala correcta."
                )
                break

        # Verificar que las variables referenciadas en la funcion existen
        variables = set(config.get('variables', {}).keys())
        # Extraer nombres simples usados en la funcion (heuristica)
        names_in_fn = set(re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', fn))
        # Excluir keywords Python y builtins
        python_builtins = {'max', 'min', 'abs', 'sum', 'round', 'int', 'float',
                           'if', 'else', 'and', 'or', 'not', 'True', 'False', 'None',
                           'len', 'range', 'print'}
        refs = names_in_fn - python_builtins
        missing = refs - variables
        if missing and variables:  # solo advertir si hay variables definidas
            r.add_warning(
                f"business_model.function referencia nombres no definidos en 'variables': "
                f"{missing}. Puede ser parametro de business_parameters o error tipografico."
            )

    def _check_decision_rules(self, config: Dict, r: ValidationResult):
        rules = config.get('decision_rules', [])
        if not rules:
            r.add_warning("No hay 'decision_rules'. Se usaran reglas por defecto.")
            return
        if not isinstance(rules, list):
            r.add_error("'decision_rules' debe ser una lista.")
            return

        for i, rule in enumerate(rules):
            if not isinstance(rule, dict):
                r.add_warning(f"decision_rules[{i}]: no es un dict, se ignorara.")
                continue
            if not rule.get('condition'):
                r.add_warning(f"decision_rules[{i}]: sin 'condition', la regla nunca disparara.")
            else:
                # Verificar que la condicion es Python valido
                try:
                    ast.parse(rule['condition'], mode='eval')
                except SyntaxError as e:
                    r.add_error(f"decision_rules[{i}].condition error de sintaxis: {e}")

    def _check_thresholds(self, config: Dict, r: ValidationResult):
        thresholds = config.get('thresholds', {})
        if not thresholds:
            return
        critical_loss = thresholds.get('critical_loss_prob')
        if critical_loss is not None:
            if not 0 < critical_loss < 1:
                r.add_warning(
                    f"thresholds.critical_loss_prob={critical_loss} debe estar entre 0 y 1."
                )

    def _check_simulation(self, config: Dict, r: ValidationResult):
        sim = config.get('simulation', {})
        if not sim:
            return
        n = sim.get('iterations') or sim.get('n_simulations')
        if n is not None:
            if n < 100:
                r.add_error(f"simulation.iterations={n} es demasiado bajo. Minimo recomendado: 1000.")
            elif n < 1000:
                r.add_warning(f"simulation.iterations={n} es bajo. Se recomiendan 10,000+.")
            elif n > 100_000:
                r.add_warning(f"simulation.iterations={n} es muy alto. Puede ser lento en Cloud.")


# ═══════════════════════════════════════════════════════════════
# CONVENIENCE
# ═══════════════════════════════════════════════════════════════

def validate_config(config: Dict) -> ValidationResult:
    """Valida un dict de configuracion y retorna el resultado."""
    return ConfigValidator().validate(config)


def validate_config_file(path: str) -> ValidationResult:
    """Carga y valida un YAML directamente desde archivo."""
    import yaml
    try:
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return validate_config(config or {})
    except FileNotFoundError:
        r = ValidationResult()
        r.add_error(f"Archivo no encontrado: {path}")
        return r
    except yaml.YAMLError as e:
        r = ValidationResult()
        r.add_error(f"Error parseando YAML: {e}")
        return r
