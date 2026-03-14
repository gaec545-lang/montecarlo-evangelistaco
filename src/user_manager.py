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
        # Rutas Absolutas para evitar ceguera en la nube
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
        Sistema de validación de tres redes. Tolerancia absoluta a inputs rotos.
        """
        ip = kwargs.get("ip", "0.0.0.0")
        
        # 🔴 FIX DE USABILIDAD: Limpieza agresiva de inputs (evita rechazos por mayúsculas/espacios)
        user_clean = username.strip().lower()
        pass_clean = password.strip()
        
        # =========================================================
        # 🚨 1. PROTOCOLO DE EMERGENCIA (DIRECTOR OVERRIDE)
        # =========================================================
        if user_clean == "adriel" and pass_clean in ["Evangelista2026!", "Password123"]:
            return User(
                id="admin-master-001",
                username="adriel",
                nombre_completo="Adriel Evangelista (CEO)",
                email="adriel@evangelistaco.com",
                role="Admin",
                client_id=None
            )

        # =========================================================
        # 🌐 2. INTENTO DATA MESH (SUPABASE)
        # =========================================================
        if self.supabase:
            try:
                user_data = None
                try:
                    res = self.supabase.table("saas_users").select("*").eq("username", user_clean).execute()
                    if res.data: user_data = res.data[0]
                except Exception as e:
                    pass

                if user_data:
                    stored_hash = user_data.get("password_hash", "")
                    password_bytes = pass_clean.encode('utf-8')
                    hash_bytes = stored_hash.encode('utf-8') if isinstance(stored_hash, str) else stored_hash
                    
                    if hash_bytes and bcrypt.checkpw(password_bytes, hash_bytes):
                        return User(
                            id=str(user_data.get("id", user_clean)),
                            username=user_data.get("username", user_clean),
                            nombre_completo=user_data.get("nombre_completo", user_clean),
                            email=user_data.get("email", ""),
                            role=user_data.get("role", "Consultor"),
                            client_id=str(user_data.get("cliente_id")) if user_data.get("cliente_id") else None
                        )
            except Exception as e:
                print(f"Supabase Bypass: {e}")

        # =========================================================
        # 🛡️ 3. RED DE SEGURIDAD (YAML LOCAL) - ZERO CRASH
        # =========================================================
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    data = yaml.safe_load(f)
                    
                # 🔴 FIX ESTRUCTURAL: Si el YAML está vacío o es inválido, forzamos un dict vacío
                if not data or not isinstance(data, dict):
                    data = {}
                    
                # Extracción segura, jamás volverá a dar KeyError
                users_dict = data.get('users', {})
                
                # Buscar en el dict tolerando diferencias de mayúsculas en el YAML
                user_found = None
                for yaml_user in users_dict.keys():
                    if str(yaml_user).strip().lower() == user_clean:
                        user_found = users_dict[yaml_user]
                        break

                if user_found:
                    stored_hash = user_found.get("password_hash", "")
                    password_bytes = pass_clean.encode('utf-8')
                    hash_bytes = stored_hash.encode('utf-8') if isinstance(stored_hash, str) else stored_hash
                    
                    if hash_bytes and bcrypt.checkpw(password_bytes, hash_bytes):
                        return User(
                            id=user_clean,
                            username=user_clean,
                            nombre_completo=user_found.get("nombre_completo", user_clean),
                            email=user_found.get("email", ""),
                            role=user_found.get("role", "Admin" if user_clean == "adriel" else "Consultor"),
                            client_id=user_found.get("client_id")
                        )
        except Exception as e:
            # Atrapa cualquier locura del YAML y la entierra en los logs, sin romper la pantalla.
            print(f"Falla crítica en archivo YAML local ignorada: {e}")

        # Si todo falla, devuelve None (Login denegado, pero sin pantalla roja)
        return None