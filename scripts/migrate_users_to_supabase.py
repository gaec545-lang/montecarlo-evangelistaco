"""
Script de migración: configs/users.yaml → Supabase (saas_users)
Evangelista & Co. | Sentinel Decision Intelligence

INSTRUCCIONES:
1. Asegúrate de que la tabla saas_users existe en Supabase.
   (Aplicar supabase/migrations/001_create_users_table.sql primero)
2. Ejecutar UNA SOLA VEZ desde la raíz del proyecto:
       python scripts/migrate_users_to_supabase.py
3. Verificar que los usuarios aparecen en Supabase.
4. Renombrar configs/users.yaml → configs/users.yaml.backup
"""

import sys
import os
import uuid
import yaml
from datetime import datetime
from pathlib import Path

# ── Rutas ──────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
YAML_PATH = ROOT / "configs" / "users.yaml"
SECRETS_PATH = ROOT / ".streamlit" / "secrets.toml"

# ── Leer DATABASE_URL desde secrets.toml (sin depender de Streamlit) ──────────
def get_db_url() -> str:
    try:
        import tomllib
        with open(SECRETS_PATH, "rb") as f:
            secrets = tomllib.load(f)
    except ImportError:
        # Python < 3.11: usar tomli si está disponible, o parsear manualmente
        try:
            import tomli
            with open(SECRETS_PATH, "rb") as f:
                secrets = tomli.load(f)
        except ImportError:
            # Fallback: parseo manual de líneas clave=valor
            secrets = {}
            with open(SECRETS_PATH, "r") as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        k, _, v = line.partition("=")
                        secrets[k.strip()] = v.strip().strip('"')

    url = secrets.get("DATABASE_URL", os.environ.get("DATABASE_URL", ""))
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


def run_migration():
    # ── Conectar a Supabase ────────────────────────────────────────────────────
    from sqlalchemy import create_engine, text
    db_url = get_db_url()
    if not db_url:
        print("❌ No se encontró DATABASE_URL. Verifica .streamlit/secrets.toml")
        sys.exit(1)

    engine = create_engine(db_url, pool_pre_ping=True)
    print(f"✅ Conectado a Supabase PostgreSQL")

    # ── Leer YAML ──────────────────────────────────────────────────────────────
    if not YAML_PATH.exists():
        print(f"❌ No se encontró {YAML_PATH}")
        sys.exit(1)

    with open(YAML_PATH, "r") as f:
        data = yaml.safe_load(f) or {"users": []}

    users = data.get("users", [])
    if not users:
        print("⚠️  No hay usuarios en users.yaml. Nada que migrar.")
        return

    print(f"📋 Encontrados {len(users)} usuario(s) en YAML.")

    # ── Insertar en saas_users ─────────────────────────────────────────────────
    inserted = 0
    skipped = 0

    # ── Crear tabla si no existe (via SQLAlchemy ORM) ────────────────────────────
    # Nota: RLS debe aplicarse manualmente desde Supabase SQL Editor
    #       usando: supabase/migrations/001_create_users_table.sql
    sys.path.insert(0, str(ROOT))
    from src.user_manager import Base as UserBase
    UserBase.metadata.create_all(engine)
    print("✅ Tabla saas_users verificada/creada.")

    # ── Insertar en saas_users ─────────────────────────────────────────────────
    with engine.begin() as conn:
        for u in users:
            username = u.get("username")
            if not username:
                continue

            # Verificar si ya existe
            exists = conn.execute(
                text("SELECT 1 FROM saas_users WHERE username = :username"),
                {"username": username}
            ).fetchone()

            if exists:
                print(f"  ⏭️  Saltando '{username}' (ya existe en Supabase)")
                skipped += 1
                continue

            # Parsear fechas
            def parse_dt(val):
                if not val:
                    return None
                try:
                    return datetime.fromisoformat(val)
                except Exception:
                    return None

            locked_until = parse_dt(u.get("locked_until"))
            last_login = parse_dt(u.get("last_login"))
            created_at = parse_dt(u.get("created_at")) or datetime.now()

            conn.execute(
                text("""
                    INSERT INTO saas_users
                        (id, username, password_hash, role, nombre_completo, email,
                         client_id, is_active, failed_attempts, locked_until,
                         created_at, created_by, last_login)
                    VALUES
                        (:id, :username, :password_hash, :role, :nombre_completo, :email,
                         :client_id, :is_active, :failed_attempts, :locked_until,
                         :created_at, :created_by, :last_login)
                """),
                {
                    "id": str(uuid.uuid4()),
                    "username": username,
                    "password_hash": u.get("password_hash", ""),
                    "role": u.get("role", "Consultor"),
                    "nombre_completo": u.get("nombre_completo", username),
                    "email": u.get("email", f"{username}@evangelistaco.com"),
                    "client_id": u.get("client_id"),
                    "is_active": u.get("is_active", True),
                    "failed_attempts": u.get("failed_attempts", 0),
                    "locked_until": locked_until,
                    "created_at": created_at,
                    "created_by": u.get("created_by"),
                    "last_login": last_login,
                }
            )

            print(f"  ✅ Migrado: '{username}' ({u.get('role')}) → {u.get('email')}")
            inserted += 1

    print(f"\n{'='*50}")
    print(f"Migración completada: {inserted} insertados, {skipped} saltados.")
    print(f"\nPróximo paso: renombrar configs/users.yaml → configs/users.yaml.backup")
    print("    mv configs/users.yaml configs/users.yaml.backup")


if __name__ == "__main__":
    run_migration()
