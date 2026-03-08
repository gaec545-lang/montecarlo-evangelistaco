"""
History Manager — SPEC 9.1
Almacena snapshots de resultados de pipeline por cliente y permite
comparar tendencias a lo largo del tiempo.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


_BASE = Path(__file__).parent.parent / "data" / "history"
_MAX_SNAPSHOTS = 90  # Maximos snapshots por cliente


def _client_dir(client_id: str) -> Path:
    d = _BASE / client_id
    d.mkdir(parents=True, exist_ok=True)
    return d


# ═══════════════════════════════════════════════════════════════
# GUARDAR
# ═══════════════════════════════════════════════════════════════

def save_snapshot(
    client_id: str,
    stats: Dict,
    health_score: int = None,
    sensitivity: Dict = None,
    label: str = None,
) -> str:
    """
    Guarda un snapshot de los resultados del pipeline.
    Retorna el nombre del archivo generado.
    """
    ts = datetime.now(timezone.utc)
    filename = ts.strftime("%Y%m%d_%H%M%S") + f"_{ts.microsecond // 1000:03d}.json"

    snapshot = {
        "timestamp": ts.isoformat(),
        "label": label or ts.strftime("%d/%m/%Y %H:%M"),
        "health_score": health_score,
        "stats": {
            "mean":      stats.get("mean", 0),
            "std":       stats.get("std", 0),
            "p10":       stats.get("p10", 0),
            "p50":       stats.get("p50", 0),
            "p90":       stats.get("p90", 0),
            "prob_loss": stats.get("prob_loss", 0),
            "var_95":    stats.get("var_95", 0),
        },
    }
    if sensitivity:
        # Guardar solo top 5 drivers como dict {variable: importance}
        if hasattr(sensitivity, "iterrows"):
            top = sensitivity.head(5)
            snapshot["top_drivers"] = dict(zip(top["variable"], top["importance"].round(4)))
        elif isinstance(sensitivity, dict):
            sorted_s = sorted(sensitivity.items(), key=lambda x: abs(x[1]), reverse=True)[:5]
            snapshot["top_drivers"] = {k: round(v, 4) for k, v in sorted_s}

    path = _client_dir(client_id) / filename
    path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2))

    _prune(client_id)
    return filename


def _prune(client_id: str):
    """Elimina snapshots mas antiguos si se supera el limite."""
    files = sorted(_client_dir(client_id).glob("*.json"))
    for old in files[:-_MAX_SNAPSHOTS]:
        old.unlink(missing_ok=True)


# ═══════════════════════════════════════════════════════════════
# CARGAR
# ═══════════════════════════════════════════════════════════════

def load_snapshots(client_id: str, limit: int = 30) -> List[Dict]:
    """Carga los ultimos N snapshots mas recientes (orden cronologico)."""
    d = _client_dir(client_id)
    files = sorted(d.glob("*.json"))[-limit:]
    snapshots = []
    for f in files:
        try:
            snapshots.append(json.loads(f.read_text()))
        except Exception:
            continue
    return snapshots


def load_latest(client_id: str) -> Optional[Dict]:
    """Retorna el snapshot mas reciente o None."""
    snaps = load_snapshots(client_id, limit=1)
    return snaps[0] if snaps else None


# ═══════════════════════════════════════════════════════════════
# COMPARACION
# ═══════════════════════════════════════════════════════════════

def compute_delta(current: Dict, previous: Dict) -> Dict:
    """
    Calcula el delta entre el snapshot actual y el anterior.
    Retorna un dict con delta absoluto y porcentual por metrica.
    """
    cur_s = current.get("stats", current)
    prv_s = previous.get("stats", previous)

    metrics = ["mean", "p50", "p90", "p10", "prob_loss", "var_95"]
    deltas = {}

    for m in metrics:
        c = cur_s.get(m, 0)
        p = prv_s.get(m, 0)
        abs_delta = c - p
        pct_delta = (abs_delta / abs(p) * 100) if p != 0 else 0
        deltas[m] = {
            "current":   round(c, 4),
            "previous":  round(p, 4),
            "delta":     round(abs_delta, 4),
            "delta_pct": round(pct_delta, 2),
        }

    # Health score delta
    cur_hs = current.get("health_score")
    prv_hs = previous.get("health_score")
    if cur_hs is not None and prv_hs is not None:
        deltas["health_score"] = {
            "current":  cur_hs,
            "previous": prv_hs,
            "delta":    cur_hs - prv_hs,
        }

    return deltas
