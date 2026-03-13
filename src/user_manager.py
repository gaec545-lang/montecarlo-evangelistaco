import yaml
import bcrypt
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import List, Optional
import os
import re

os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    filename='logs/audit.log',
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

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
    def __init__(self, config_path: str = 'configs/users.yaml'):
        self.config_path = config_path
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.config_path):
            with open(self.config_path, 'w') as file:
                yaml.dump({'users': []}, file)

    def _load_users(self) -> dict:
        with open(self.config_path, 'r') as file:
            return yaml.safe_load(file) or {'users': []}

    def _save_users(self, data: dict):
        with open(self.config_path, 'w') as file:
            yaml.dump(data, file, default_flow_style=False)

    def _validate_password_complexity(self, password: str) -> bool:
        if len(password) < 8: return False
        if not re.search(r"[A-Z]", password): return False
        if not re.search(r"[a-z]", password): return False
        if not re.search(r"[0-9]", password): return False
        return True

    def create_user(self, username, password, role, nombre_completo, email, created_by, client_id=None) -> bool:
        data = self._load_users()
        if any(u['username'] == username for u in data['users']):
            return False 
        
        if not self._validate_password_complexity(password):
            raise ValueError("La contraseña exige 8 caracteres, 1 mayúscula, 1 minúscula y 1 número.")
            
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        
        new_user = User(
            username=username,
            password_hash=hashed_password,
            role=role,
            nombre_completo=nombre_completo,
            email=email,
            created_at=datetime.now().isoformat(),
            last_login=None,
            is_active=True,
            created_by=created_by,
            client_id=client_id
        )
        
        data['users'].append(asdict(new_user))
        self._save_users(data)
        logging.info(f"USER_CREATED | user={username} | role={role} | client_id={client_id}")
        return True

    def authenticate(self, username: str, password: str, ip: str = "unknown") -> Optional[User]:
        data = self._load_users()
        user_idx, user_data = next(((i, u) for i, u in enumerate(data['users']) if u['username'] == username), (None, None))

        if not user_data:
            logging.warning(f"LOGIN_FAILED | user={username} | reason=user_not_found | ip={ip}")
            return None

        user = User(**user_data)

        if user.locked_until:
            lock_time = datetime.fromisoformat(user.locked_until)
            if datetime.now() < lock_time:
                logging.warning(f"LOGIN_FAILED | user={username} | reason=account_locked | ip={ip}")
                return None
            else:
                user.locked_until = None
                user.failed_attempts = 0

        if not user.is_active:
            logging.warning(f"LOGIN_FAILED | user={username} | reason=account_disabled | ip={ip}")
            return None

        if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            user.failed_attempts = 0
            user.last_login = datetime.now().isoformat()
            data['users'][user_idx] = asdict(user)
            self._save_users(data)
            logging.info(f"LOGIN_SUCCESS | user={username} | role={user.role} | ip={ip}")
            return user
        else:
            user.failed_attempts += 1
            reason = "invalid_password"
            if user.failed_attempts >= 5:
                user.locked_until = (datetime.now() + timedelta(minutes=15)).isoformat()
                logging.warning(f"ACCOUNT_LOCKED | user={username} | reason=max_attempts")
                reason = "max_attempts_reached"
            
            data['users'][user_idx] = asdict(user)
            self._save_users(data)
            logging.warning(f"LOGIN_FAILED | user={username} | reason={reason} | ip={ip}")
            return None

    # --- NUEVAS FUNCIONES OPERATIVAS (CRUD) ---
    def get_all_users(self) -> list:
        data = self._load_users()
        return data.get('users', [])

    def toggle_user_status(self, username: str) -> bool:
        data = self._load_users()
        for user in data['users']:
            if user['username'] == username:
                user['is_active'] = not user['is_active']
                self._save_users(data)
                return user['is_active']
        return False

    def delete_user(self, username: str) -> bool:
        data = self._load_users()
        initial_len = len(data['users'])
        data['users'] = [u for u in data['users'] if u['username'] != username]
        if len(data['users']) < initial_len:
            self._save_users(data)
            return True
        return False
