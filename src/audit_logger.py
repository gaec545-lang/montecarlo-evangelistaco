"""
Audit Logger — SPEC 8.1
Log persistente de eventos del sistema en formato JSON Lines.
Almacena en logs/audit.jsonl (append-only).
"""
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

_LOG_PATH = Path(__file__).parent.parent / "logs" / "audit.jsonl"
_lock = threading.Lock()


# ═══════════════════════════════════════════════════════════════
# TIPOS DE EVENTO
# ═══════════════════════════════════════════════════════════════

class EventType:
    AUTH_SUCCESS   = "auth.success"
    AUTH_FAILURE   = "auth.failure"
    AUTH_LOGOUT    = "auth.logout"
    PIPELINE_RUN   = "pipeline.run"
    PIPELINE_ERROR = "pipeline.error"
    PDF_DOWNLOAD   = "pdf.download"
    YAML_GENERATE  = "yaml.generate"
    CONFIG_INVALID = "config.invalid"
    ADMIN_ACTION   = "admin.action"


# ═══════════════════════════════════════════════════════════════
# CORE
# ═══════════════════════════════════════════════════════════════

def _write(entry: Dict):
    """Escribe una entrada al log de forma thread-safe."""
    _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(entry, ensure_ascii=False, default=str)
    with _lock:
        with open(_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def log_event(
    event_type: str,
    username: str = "system",
    client_id: str = None,
    role: str = None,
    details: Dict[str, Any] = None,
    duration_ms: int = None,
    success: bool = True,
    ip: str = None,
) -> None:
    """Registra un evento de auditoría."""
    entry = {
        "ts":         datetime.now(timezone.utc).isoformat(),
        "event":      event_type,
        "username":   username,
        "success":    success,
    }
    if client_id:   entry["client_id"]   = client_id
    if role:        entry["role"]        = role
    if duration_ms is not None: entry["duration_ms"] = duration_ms
    if ip:          entry["ip"]          = ip
    if details:     entry["details"]     = details

    try:
        _write(entry)
    except Exception:
        pass  # Nunca romper el flujo por un fallo de log


# ═══════════════════════════════════════════════════════════════
# HELPERS DE ALTO NIVEL
# ═══════════════════════════════════════════════════════════════

def log_auth(username: str, success: bool, role: str = None, ip: str = None):
    log_event(
        EventType.AUTH_SUCCESS if success else EventType.AUTH_FAILURE,
        username=username, role=role, ip=ip, success=success,
    )


def log_pipeline(
    username: str,
    client_id: str,
    role: str,
    duration_ms: int,
    health_score: int = None,
    phases_completed: int = 0,
    error: str = None,
):
    success = error is None
    log_event(
        EventType.PIPELINE_RUN if success else EventType.PIPELINE_ERROR,
        username=username, client_id=client_id, role=role,
        duration_ms=duration_ms, success=success,
        details={
            "health_score": health_score,
            "phases_completed": phases_completed,
            "error": error,
        },
    )


def log_pdf(username: str, client_id: str, role: str):
    log_event(EventType.PDF_DOWNLOAD, username=username, client_id=client_id, role=role)


def log_yaml_generate(username: str, client_id: str, success: bool, error: str = None):
    log_event(
        EventType.YAML_GENERATE, username=username, client_id=client_id,
        success=success, details={"error": error} if error else None,
    )


def log_admin(username: str, action: str, target: str = None):
    log_event(
        EventType.ADMIN_ACTION, username=username,
        details={"action": action, "target": target},
    )


# ═══════════════════════════════════════════════════════════════
# QUERY
# ═══════════════════════════════════════════════════════════════

def read_logs(
    limit: int = 200,
    event_type: str = None,
    username: str = None,
    client_id: str = None,
    since_hours: int = None,
) -> List[Dict]:
    """Lee y filtra el log de auditoría."""
    if not _LOG_PATH.exists():
        return []

    entries = []
    try:
        with open(_LOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except Exception:
        return []

    # Filtros
    if event_type:
        entries = [e for e in entries if e.get("event") == event_type]
    if username:
        entries = [e for e in entries if e.get("username") == username]
    if client_id:
        entries = [e for e in entries if e.get("client_id") == client_id]
    if since_hours:
        cutoff = datetime.now(timezone.utc).timestamp() - since_hours * 3600
        filtered = []
        for e in entries:
            try:
                ts = datetime.fromisoformat(e["ts"]).timestamp()
                if ts >= cutoff:
                    filtered.append(e)
            except Exception:
                filtered.append(e)
        entries = filtered

    return entries[-limit:]


def get_summary_stats(since_hours: int = 24) -> Dict:
    """Estadisticas resumidas de las ultimas N horas para el Admin Panel."""
    logs = read_logs(limit=5000, since_hours=since_hours)
    total = len(logs)
    by_event: Dict[str, int] = {}
    auth_fails = 0
    pipeline_errors = 0
    avg_duration_ms = None
    durations = []

    for e in logs:
        ev = e.get("event", "unknown")
        by_event[ev] = by_event.get(ev, 0) + 1
        if ev == EventType.AUTH_FAILURE:
            auth_fails += 1
        if ev == EventType.PIPELINE_ERROR:
            pipeline_errors += 1
        if "duration_ms" in e:
            durations.append(e["duration_ms"])

    if durations:
        avg_duration_ms = round(sum(durations) / len(durations))

    return {
        "total_events": total,
        "by_event": by_event,
        "auth_failures": auth_fails,
        "pipeline_errors": pipeline_errors,
        "avg_pipeline_ms": avg_duration_ms,
        "since_hours": since_hours,
    }
