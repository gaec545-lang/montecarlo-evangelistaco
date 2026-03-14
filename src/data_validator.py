"""
Data Validator - Escudo 3 (El Bisturí)
Evangelista & Co. | Sentinel Decision Intelligence V2

Valida la calidad de datos antes de ejecutar el pipeline completo.
Usa Great Expectations para definir y verificar expectativas de negocio.
"""

import logging
import warnings
from datetime import datetime, date
from typing import Optional

import pandas as pd
import numpy as np

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

logger = logging.getLogger(__name__)


# ── Importación segura de Great Expectations ──────────────────────────────────

def _import_ge():
    """Importa Great Expectations con fallback si no está disponible o no es compatible."""
    try:
        import great_expectations as ge
        # Prueba de sanidad: GE 0.18.x tiene incompatibilidad con Python 3.14 + pydantic v2
        ge.from_pandas(pd.DataFrame({"x": [1]}))
        return ge
    except Exception:
        return None


# ── Validador fallback (sin Great Expectations) ───────────────────────────────

class _PandasValidator:
    """
    Validador básico usando pandas puro.
    Se usa cuando Great Expectations no está instalado.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def expect_column_values_to_not_be_null(self, col: str) -> bool:
        if col not in self.df.columns:
            return False
        return bool(self.df[col].notna().all())

    def expect_column_values_to_be_between(self, col: str,
                                            min_value=None, max_value=None) -> bool:
        if col not in self.df.columns:
            return False
        series = self.df[col].dropna()
        if min_value is not None and (series < min_value).any():
            return False
        if max_value is not None and (series > max_value).any():
            return False
        return True

    def expect_column_to_exist(self, col: str) -> bool:
        return col in self.df.columns

    def expect_table_row_count_to_be_between(self, min_value=None, max_value=None) -> bool:
        n = len(self.df)
        if min_value is not None and n < min_value:
            return False
        if max_value is not None and n > max_value:
            return False
        return True

    def expect_column_values_to_be_of_type(self, col: str, type_: str) -> bool:
        if col not in self.df.columns:
            return False
        dtype = str(self.df[col].dtype)
        type_map = {
            "float":    ["float", "float32", "float64"],
            "int":      ["int", "int32", "int64"],
            "str":      ["object", "string"],
            "datetime": ["datetime64", "datetime"],
        }
        return any(t in dtype for t in type_map.get(type_, [type_]))


# ── Motor principal ────────────────────────────────────────────────────────────

class DataValidator:
    """
    Valida calidad de datos antes de ejecutar el pipeline de 3 Escudos.

    Uso:
        validator = DataValidator()
        is_valid, errores, warnings = validator.validate_client_data(df_proyectos, df_compras)
        if not is_valid:
            raise DataQualityError(errores)
    """

    def __init__(self):
        self.ge = _import_ge()
        self.use_ge = self.ge is not None
        if self.use_ge:
            logger.info("DataValidator: usando Great Expectations")
        else:
            logger.info("DataValidator: usando validador pandas (GE no instalado)")

    def _make_validator(self, df: pd.DataFrame):
        """Crea un validador GE o fallback pandas."""
        if self.use_ge:
            try:
                return self.ge.from_pandas(df)
            except Exception:
                pass
        return _PandasValidator(df)

    # ── Validaciones individuales ──────────────────────────────────────────────

    def validate_fact_proyectos(self, df: pd.DataFrame) -> tuple[bool, list, list]:
        """
        Valida la tabla fact_proyectos (ingresos del cliente).

        Expectativas mínimas:
          - Al menos 3 filas (necesitamos historia)
          - No nulls en columnas críticas
          - Montos > 0
          - Fechas en rango válido (últimos 5 años)
        """
        errores = []
        advertencias = []

        if df is None or df.empty:
            return False, ["fact_proyectos está vacío o no existe"], []

        v = self._make_validator(df)

        # 1. Mínimo de filas
        if len(df) < 3:
            errores.append(f"fact_proyectos tiene solo {len(df)} fila(s). Mínimo requerido: 3")

        # 2. Detectar columna de fecha
        fecha_col = next((c for c in df.columns if "fecha" in c.lower()), None)
        if not fecha_col:
            errores.append("No se encontró columna de fecha en fact_proyectos")
        else:
            if not v.expect_column_values_to_not_be_null(fecha_col):
                errores.append(f"Hay fechas NULL en fact_proyectos.{fecha_col}")
            else:
                # Verificar rango de fechas
                try:
                    fechas = pd.to_datetime(df[fecha_col], errors="coerce")
                    nulls_fecha = fechas.isna().sum()
                    if nulls_fecha > 0:
                        errores.append(f"{nulls_fecha} fechas no parseables en {fecha_col}")

                    fecha_min = fechas.min()
                    fecha_max = fechas.max()
                    ahora = pd.Timestamp.now()
                    cinco_anos = ahora - pd.DateOffset(years=5)

                    if fecha_min < cinco_anos:
                        advertencias.append(
                            f"fact_proyectos tiene datos de más de 5 años atrás ({fecha_min.date()}). "
                            "Considerar filtrar registros antiguos."
                        )
                    if fecha_max > ahora + pd.DateOffset(days=1):
                        advertencias.append(
                            f"fact_proyectos tiene fechas futuras ({fecha_max.date()}). "
                            "Verificar datos."
                        )
                except Exception as e:
                    advertencias.append(f"No se pudo validar rango de fechas: {e}")

        # 3. Detectar columna de monto
        monto_col = next(
            (c for c in df.columns if any(k in c.lower() for k in
             ["monto", "ingreso", "factur", "importe", "valor"])),
            None
        )
        if not monto_col:
            errores.append("No se encontró columna de monto/ingreso en fact_proyectos")
        else:
            if not v.expect_column_values_to_not_be_null(monto_col):
                errores.append(f"Hay montos NULL en fact_proyectos.{monto_col}")

            if not v.expect_column_values_to_be_between(monto_col, min_value=0):
                n_neg = (df[monto_col] < 0).sum()
                errores.append(
                    f"fact_proyectos tiene {n_neg} monto(s) negativo(s) en {monto_col}. "
                    "Los ingresos deben ser ≥ 0."
                )

            # Verificar outliers extremos (> 100x la mediana)
            try:
                mediana = df[monto_col].median()
                max_val = df[monto_col].max()
                if mediana > 0 and max_val > mediana * 100:
                    advertencias.append(
                        f"fact_proyectos tiene outlier extremo en {monto_col}: "
                        f"max={max_val:,.0f} vs mediana={mediana:,.0f}. Verificar."
                    )
            except Exception:
                pass

        is_valid = len(errores) == 0
        return is_valid, errores, advertencias

    def validate_fact_compras(self, df: pd.DataFrame) -> tuple[bool, list, list]:
        """
        Valida la tabla fact_compras (costos del cliente).
        """
        errores = []
        advertencias = []

        if df is None or df.empty:
            advertencias.append("fact_compras está vacío. Se usarán costos estimados.")
            return True, [], advertencias  # No es error crítico

        v = self._make_validator(df)

        fecha_col = next((c for c in df.columns if "fecha" in c.lower()), None)
        costo_col = next(
            (c for c in df.columns if any(k in c.lower() for k in
             ["monto", "costo", "importe", "total", "valor"])),
            None
        )

        if fecha_col and not v.expect_column_values_to_not_be_null(fecha_col):
            errores.append(f"Hay fechas NULL en fact_compras.{fecha_col}")

        if costo_col:
            if not v.expect_column_values_to_be_between(costo_col, min_value=0):
                n_neg = (df[costo_col] < 0).sum()
                errores.append(
                    f"fact_compras tiene {n_neg} costo(s) negativo(s). "
                    "Los costos deben ser ≥ 0."
                )
        else:
            advertencias.append("No se encontró columna de costo en fact_compras. "
                                 "Se usarán costos estimados.")

        is_valid = len(errores) == 0
        return is_valid, errores, advertencias

    def validate_forecasting_results(self, forecasting_results: dict) -> tuple[bool, list, list]:
        """
        Valida los resultados del Escudo 1 antes de pasarlos al Escudo 2.
        """
        errores = []
        advertencias = []

        if not forecasting_results or "error" in forecasting_results:
            advertencias.append(
                f"Escudo 1 reportó error: {forecasting_results.get('error', 'desconocido')}. "
                "El Escudo 2 usará parámetros base."
            )
            return True, [], advertencias

        df_ing = forecasting_results.get("ingresos_12m")
        df_cos = forecasting_results.get("costos_12m")

        if df_ing is not None and not df_ing.empty:
            if (df_ing["valor_proyectado"] < 0).any():
                errores.append("Escudo 1 proyectó ingresos negativos. Revisar datos históricos.")
            if df_ing["valor_proyectado"].max() > df_ing["valor_proyectado"].mean() * 5:
                advertencias.append(
                    "Hay picos extremos en la proyección de ingresos. "
                    "Posible overfitting del modelo Prophet."
                )

        if df_cos is not None and not df_cos.empty:
            if df_ing is not None and not df_ing.empty:
                ratio = df_cos["valor_proyectado"].mean() / max(1, df_ing["valor_proyectado"].mean())
                if ratio > 0.95:
                    advertencias.append(
                        f"Margen proyectado muy estrecho: costos = {ratio:.0%} de ingresos. "
                        "Alta sensibilidad a shocks."
                    )

        is_valid = len(errores) == 0
        return is_valid, errores, advertencias

    # ── Pipeline completo ─────────────────────────────────────────────────────

    def validate_all(self, df_proyectos: Optional[pd.DataFrame] = None,
                     df_compras: Optional[pd.DataFrame] = None,
                     forecasting_results: Optional[dict] = None) -> dict:
        """
        Ejecuta todas las validaciones y retorna un reporte consolidado.

        Returns:
            dict con is_valid, errores_criticos, advertencias, resumen
        """
        errores_criticos = []
        advertencias = []
        resultados_detalle = {}

        # Validar fact_proyectos
        if df_proyectos is not None:
            ok, errs, warns = self.validate_fact_proyectos(df_proyectos)
            resultados_detalle["fact_proyectos"] = {"valid": ok, "errores": errs, "advertencias": warns}
            errores_criticos.extend(errs)
            advertencias.extend(warns)

        # Validar fact_compras
        if df_compras is not None:
            ok, errs, warns = self.validate_fact_compras(df_compras)
            resultados_detalle["fact_compras"] = {"valid": ok, "errores": errs, "advertencias": warns}
            errores_criticos.extend(errs)
            advertencias.extend(warns)

        # Validar resultados de Escudo 1
        if forecasting_results is not None:
            ok, errs, warns = self.validate_forecasting_results(forecasting_results)
            resultados_detalle["escudo_1"] = {"valid": ok, "errores": errs, "advertencias": warns}
            errores_criticos.extend(errs)
            advertencias.extend(warns)

        is_valid = len(errores_criticos) == 0

        reporte = {
            "validaciones_passed": is_valid,
            "errores_criticos":    errores_criticos,
            "advertencias":        advertencias,
            "detalle":             resultados_detalle,
            "motor":               "Great Expectations" if self.use_ge else "Pandas (fallback)",
            "validado_en":         datetime.now().isoformat(),
        }

        if is_valid:
            logger.info(f"DataValidator: ✅ PASSED | {len(advertencias)} advertencias")
        else:
            logger.warning(f"DataValidator: ❌ FAILED | {len(errores_criticos)} errores críticos")

        return reporte


class DataQualityError(Exception):
    """Se lanza cuando los datos no pasan la validación de calidad."""
    pass
