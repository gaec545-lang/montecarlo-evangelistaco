"""
Script de carga: BANXICO → saas_variables_exogenas
Evangelista & Co. | Sentinel Decision Intelligence V2

Descarga datos macroeconómicos de la API de BANXICO (SIE) y los inserta
en la tabla global saas_variables_exogenas de Supabase.

PREREQUISITOS:
1. Registrarte en https://www.banxico.org.mx/SieAPIRest/ y obtener tu token.
2. Añadir en .streamlit/secrets.toml:
       BANXICO_TOKEN = "tu_token_aqui"
3. Aplicar migración: supabase/migrations/002_create_variables_exogenas.sql
4. Ejecutar desde la raíz del proyecto:
       python scripts/load_banxico_data.py [--meses 24]

SERIES DISPONIBLES (BANXICO SIE):
  SF43718  → TIIE a 28 días (%)
  SF46410  → USD/MXN tipo de cambio FIX
  SP30577  → INPC (Índice Nacional de Precios al Consumidor)
  SF43936  → CETES 28 días (%)
"""

import sys
import os
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path

import requests
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Series a descargar ─────────────────────────────────────────────────────────
SERIES_BANXICO = {
    "TIIE":       {"id": "SF43718", "fuente": "BANXICO"},
    "USD_MXN":    {"id": "SF46410", "fuente": "BANXICO"},
    "INPC":       {"id": "SP30577", "fuente": "BANXICO"},
    "CETES_28":   {"id": "SF43936", "fuente": "BANXICO"},
}

BANXICO_BASE_URL = (
    "https://www.banxico.org.mx/SieAPIRest/service/v1/series/{serie}/datos/{inicio}/{fin}"
)


# ── Leer secrets ───────────────────────────────────────────────────────────────

def _load_secrets() -> dict:
    try:
        import tomllib
        with open(ROOT / ".streamlit" / "secrets.toml", "rb") as f:
            return tomllib.load(f)
    except ImportError:
        secrets = {}
        with open(ROOT / ".streamlit" / "secrets.toml") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, _, v = line.partition("=")
                    secrets[k.strip()] = v.strip().strip('"')
        return secrets


# ── Descarga de BANXICO ────────────────────────────────────────────────────────

def fetch_banxico_serie(serie_id: str, token: str,
                         fecha_inicio: str, fecha_fin: str) -> list[dict]:
    """
    Descarga datos de una serie de BANXICO SIE.

    Args:
        serie_id:     ID de la serie (ej: 'SF43718')
        token:        Token de acceso BANXICO
        fecha_inicio: Formato 'YYYY-MM-DD'
        fecha_fin:    Formato 'YYYY-MM-DD'

    Returns:
        Lista de dicts con claves: fecha, dato
    """
    url = BANXICO_BASE_URL.format(
        serie=serie_id,
        inicio=fecha_inicio.replace("-", "/"),
        fin=fecha_fin.replace("-", "/"),
    )
    headers = {"Bmx-Token": token}

    resp = requests.get(url, headers=headers, timeout=30)

    if resp.status_code == 401:
        raise ValueError("Token BANXICO inválido o expirado. Verifica BANXICO_TOKEN en secrets.toml")

    if resp.status_code != 200:
        raise RuntimeError(f"BANXICO API error {resp.status_code}: {resp.text[:200]}")

    data = resp.json()
    series_data = data.get("bmx", {}).get("series", [])
    if not series_data:
        return []

    registros = series_data[0].get("datos", [])
    return registros  # [{"fecha": "06/01/2024", "dato": "11.00"}, ...]


def parse_banxico_registros(registros: list, variable: str,
                              serie_info: dict) -> pd.DataFrame:
    """Convierte la respuesta de BANXICO a un DataFrame normalizado."""
    rows = []
    for r in registros:
        raw_fecha = r.get("fecha", "")
        raw_valor = r.get("dato", "").replace(",", "")

        if not raw_valor or raw_valor in ("N/E", "N/D", ""):
            continue

        try:
            # BANXICO devuelve fechas en formato dd/mm/yyyy
            fecha = datetime.strptime(raw_fecha, "%d/%m/%Y").date()
            valor = float(raw_valor)
        except (ValueError, TypeError):
            continue

        rows.append({
            "variable":  variable,
            "fecha":     fecha,
            "valor":     valor,
            "fuente":    serie_info["fuente"],
            "serie_id":  serie_info["id"],
        })

    return pd.DataFrame(rows)


# ── Inserción en Supabase ──────────────────────────────────────────────────────

def insert_to_supabase(df: pd.DataFrame, engine) -> int:
    """Inserta filas en saas_variables_exogenas (ignora duplicados)."""
    from sqlalchemy import text

    if df.empty:
        return 0

    inserted = 0
    with engine.begin() as conn:
        for _, row in df.iterrows():
            try:
                conn.execute(
                    text("""
                        INSERT INTO saas_variables_exogenas
                            (variable, fecha, valor, fuente, serie_id)
                        VALUES
                            (:variable, :fecha, :valor, :fuente, :serie_id)
                        ON CONFLICT (variable, fecha) DO NOTHING
                    """),
                    {
                        "variable": row["variable"],
                        "fecha":    str(row["fecha"]),
                        "valor":    float(row["valor"]),
                        "fuente":   row.get("fuente"),
                        "serie_id": row.get("serie_id"),
                    }
                )
                inserted += 1
            except Exception as e:
                logger.warning(f"Fila omitida ({row['variable']} {row['fecha']}): {e}")

    return inserted


# ── Main ───────────────────────────────────────────────────────────────────────

def run(meses: int = 24):
    secrets = _load_secrets()
    token = secrets.get("BANXICO_TOKEN") or os.environ.get("BANXICO_TOKEN", "")

    if not token:
        logger.error(
            "❌ No se encontró BANXICO_TOKEN.\n"
            "   1. Regístrate en https://www.banxico.org.mx/SieAPIRest/\n"
            "   2. Añade BANXICO_TOKEN = 'tu_token' en .streamlit/secrets.toml"
        )
        sys.exit(1)

    db_url = secrets.get("DATABASE_URL", "")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    from sqlalchemy import create_engine
    engine = create_engine(db_url, pool_pre_ping=True)
    logger.info("✅ Conectado a Supabase")

    fecha_fin   = datetime.now().strftime("%Y-%m-%d")
    fecha_ini   = (datetime.now() - timedelta(days=meses * 31)).strftime("%Y-%m-%d")
    logger.info(f"Descargando {meses} meses: {fecha_ini} → {fecha_fin}")

    total_insertados = 0

    for variable, info in SERIES_BANXICO.items():
        logger.info(f"  📡 Descargando {variable} (serie {info['id']})...")
        try:
            registros = fetch_banxico_serie(info["id"], token, fecha_ini, fecha_fin)
            df = parse_banxico_registros(registros, variable, info)
            n = insert_to_supabase(df, engine)
            total_insertados += n
            logger.info(f"     ✅ {len(df)} registros descargados, {n} insertados")
        except Exception as e:
            logger.warning(f"     ⚠️  {variable}: {e}")

    logger.info(f"\n{'='*50}")
    logger.info(f"Carga completada: {total_insertados} registros nuevos en saas_variables_exogenas")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Carga datos de BANXICO en Supabase")
    parser.add_argument("--meses", type=int, default=24,
                        help="Meses históricos a descargar (default: 24)")
    args = parser.parse_args()
    run(meses=args.meses)
