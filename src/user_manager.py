import bcrypt
import logging
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Optional
import os
import re

from sqlalchemy import create_engine, Column, String, Boolean, Integer, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, sessionmaker

os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    filename='logs/audit.log',
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

Base = declarative_base()


class SaasUser(Base):
    """Modelo ORM para la tabla saas_users en Supabase."""
    __tablename__ = 'saas_users'

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username        = Column(String(50), unique=True, nullable=False)
    password_hash   = Column(Text, nullable=False)
    role            = Column(String(20), nullable=False)
    nombre_completo = Column(String(100), nullable=False)
    email           = Column(String(100), unique=True, nullable=False)
    client_id       = Column(Text)
    is_active       = Column(Boolean, default=True)
    failed_attempts = Column(Integer, default=0)
    locked_until    = Column(DateTime)
    created_at      = Column(DateTime, default=datetime.utcnow)
    created_by      = Column(Text)
    last_login      = Column(DateTime)


@dataclass
class User:
    username: str
    password_hash: str
    role: str
    nombre_completo: str
    email: str
    created_at: str
    last_login: Optional[str]
    is_active: bool
    created_by: Optional[str]
    failed_attempts: int = 0
    locked_until: Optional[str] = None
    client_id: Optional[str] = None


class UserManager:
    def __init__(self):
        db_url = self._get_db_url()
        engine = create_engine(db_url, pool_pre_ping=True)
        Base.metadata.create_all(engine)   # Crea la tabla si no existe
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def _get_db_url(self) -> str:
        try:
            import streamlit as st
            url = st.secrets["DATABASE_URL"]
        except Exception:
            url = os.environ.get("DATABASE_URL", "")

        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url

    def _row_to_user(self, row: SaasUser) -> User:
        return User(
            username=row.username,
            password_hash=row.password_hash,
            role=row.role,
            nombre_completo=row.nombre_completo,
            email=row.email,
            created_at=row.created_at.isoformat() if row.created_at else None,
            last_login=row.last_login.isoformat() if row.last_login else None,
            is_active=row.is_active,
            created_by=row.created_by,
            failed_attempts=row.failed_attempts or 0,
            locked_until=row.locked_until.isoformat() if row.locked_until else None,
            client_id=row.client_id,
        )

    def _validate_password_complexity(self, password: str) -> bool:
        if len(password) < 8: return False
        if not re.search(r"[A-Z]", password): return False
        if not re.search(r"[a-z]", password): return False
        if not re.search(r"[0-9]", password): return False
        return True

    def create_user(self, username, password, role, nombre_completo, email, created_by, client_id=None) -> bool:
        if self.session.query(SaasUser).filter_by(username=username).first():
            return False

        if not self._validate_password_complexity(password):
            raise ValueError("La contraseña exige 8 caracteres, 1 mayúscula, 1 minúscula y 1 número.")

        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

        new_user = SaasUser(
            username=username,
            password_hash=hashed_password,
            role=role,
            nombre_completo=nombre_completo,
            email=email,
            client_id=client_id,
            is_active=True,
            failed_attempts=0,
            created_at=datetime.now(),
            created_by=created_by,
            last_login=None,
        )

        self.session.add(new_user)
        self.session.commit()
        logging.info(f"USER_CREATED | user={username} | role={role} | client_id={client_id}")
        return True

    def authenticate(self, username: str, password: str, ip: str = "unknown") -> Optional[User]:
        row = self.session.query(SaasUser).filter_by(username=username).first()

        if not row:
            logging.warning(f"LOGIN_FAILED | user={username} | reason=user_not_found | ip={ip}")
            return None

        if row.locked_until:
            if datetime.now() < row.locked_until:
                logging.warning(f"LOGIN_FAILED | user={username} | reason=account_locked | ip={ip}")
                return None
            else:
                row.locked_until = None
                row.failed_attempts = 0

        if not row.is_active:
            logging.warning(f"LOGIN_FAILED | user={username} | reason=account_disabled | ip={ip}")
            return None

        if bcrypt.checkpw(password.encode('utf-8'), row.password_hash.encode('utf-8')):
            row.failed_attempts = 0
            row.last_login = datetime.now()
            self.session.commit()
            logging.info(f"LOGIN_SUCCESS | user={username} | role={row.role} | ip={ip}")
            return self._row_to_user(row)
        else:
            row.failed_attempts = (row.failed_attempts or 0) + 1
            reason = "invalid_password"
            if row.failed_attempts >= 5:
                row.locked_until = datetime.now() + timedelta(minutes=15)
                logging.warning(f"ACCOUNT_LOCKED | user={username} | reason=max_attempts")
                reason = "max_attempts_reached"

            self.session.commit()
            logging.warning(f"LOGIN_FAILED | user={username} | reason={reason} | ip={ip}")
            return None

    def get_all_users(self) -> list:
        rows = self.session.query(SaasUser).all()
        return [asdict(self._row_to_user(r)) for r in rows]

    def toggle_user_status(self, username: str) -> bool:
        row = self.session.query(SaasUser).filter_by(username=username).first()
        if row:
            row.is_active = not row.is_active
            self.session.commit()
            return row.is_active
        return False

    def delete_user(self, username: str) -> bool:
        row = self.session.query(SaasUser).filter_by(username=username).first()
        if row:
            self.session.delete(row)
            self.session.commit()
            return True
        return False
