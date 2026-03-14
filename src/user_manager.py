import os
import bcrypt
import yaml
from datetime import datetime
import streamlit as st
from supabase import create_client, Client
from dataclasses import dataclass
from typing import Optional

# ==============================================================================
# ENTIDAD DE DATOS ESTRUCTURADA
# ==============================================================================
@dataclass
class User:
    id: str
    username: str
    nombre_completo: str
    email: str
    role: str
    client_id: Optional[str] = None

# ==============================================================================
# MOTOR DE AUTENTICACIÓN (TOLERANCIA A FALLOS MULTICAPA)
# ==============================================================================
class UserManager:
    def __init__(self, config_path: str = None):
        # 🔴 FIX ESTRUCTURAL: Rutas Absolutas. 
        # Garantiza que el servidor encuentre el YAML sin importar desde dónde arranque.
        if config_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.config_path = os.path.abspath(os.path.join(base_dir, '..', 'configs', 'users.yaml'))
        else:
            self.config_path = config_path
            
        self.supabase = self._init_supabase()

    def _init_supabase(self) -> Optional[Client]:
        """Inicialización Zero-Crash del Data Mesh"""
        def get_credential(key_name: str) -> str:
            val = os.getenv(key_name)
            if not val and hasattr(st, "secrets"):
                try: val = st.secrets[key_name]
                except KeyError: val = None
            return val

        url = get_credential("SUPABASE_URL")
        key = get_credential("SUPABASE_KEY")
        
        if url and key:
            try: 
                return create_client(url, key)
            except Exception: 
                return None
        return None

    def authenticate(self, username: str, password: str, **kwargs) -> Optional[User]:
        """
        Sistema de validación de tres redes.
        1. Llave Maestra (God Mode)
        2. Data Mesh (Supabase)
        3. Red de Seguridad Local (YAML)
        """
        ip = kwargs.get("ip", "0.0.0.0")
        
        # =========================================================
        # 🚨 PROTOCOLO DE EMERGENCIA (DIRECTOR OVERRIDE)
        # =========================================================
        # Llave maestra inquebrantable. Garantiza acceso total al CEO si la DB cae.
        if username == "adriel" and password == "Evangelista2026!":
            return User(
                id="admin-master-001",
                username="adriel",
                nombre_completo="Adriel Evangelista (CEO)",
                email="adriel@evangelistaco.com",
                role="Admin",
                client_id=None
            )

        # =========================================================
        # INTENTO 1: Data Mesh (Supabase)
        # =========================================================
        if self.supabase:
            try:
                user_data = None
                
                # Buscar en la tabla 'saas_users'
                try:
                    res = self.supabase.table("saas_users").select("*").eq("username", username).execute()
                    if res.data: user_data = res.data[0]
                except Exception as e:
                    print(f"Intento en saas_users fallido: {e}")

                if user_data:
                    stored_hash = user_data.get("password_hash", "")
                    
                    # Prevención de TypeError criptográfico
                    password_bytes = password.encode('utf-8')
                    hash_bytes = stored_hash.encode('utf-8') if isinstance(stored_hash, str) else stored_hash
                    
                    if hash_bytes and bcrypt.checkpw(password_bytes, hash_bytes):
                        return User(
                            id=str(user_data.get("id", username)),
                            username=user_data.get("username", username),
                            nombre_completo=user_data.get("nombre_completo", username),
                            email=user_data.get("email", ""),
                            role=user_data.get("role", "Consultor"),
                            client_id=str(user_data.get("cliente_id")) if user_data.get("cliente_id") else None
                        )
            except Exception as e:
                print(f"Bypass de Supabase. Razon: {e}")

        # =========================================================
        # INTENTO 2: Red de Seguridad (YAML Local)
        # =========================================================
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    data = yaml.safe_load(f) or {}
                    
                users_dict = data.get('users', {})
                if username in users_dict:
                    user_data = users_dict[username]
                    stored_hash = user_data.get("password_hash", "")
                    
                    password_bytes = password.encode('utf-8')
                    hash_bytes = stored_hash.encode('utf-8') if isinstance(stored_hash, str) else stored_hash
                    
                    if hash_bytes and bcrypt.checkpw(password_bytes, hash_bytes):
                        return User(
                            id=username,
                            username=username,
                            nombre_completo=user_data.get("nombre_completo", username),
                            email=user_data.get("email", ""),
                            role=user_data.get("role", "Admin" if username == "adriel" else "Consultor"),
                            client_id=user_data.get("client_id")
                        )
        except Exception as e:
            print(f"Error de validación local: {e}")

        # Si todas las redes fallan, acceso denegado.
        return None