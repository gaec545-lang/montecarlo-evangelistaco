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
# MOTOR DE AUTENTICACIÓN (TOLERANCIA A FALLOS)
# ==============================================================================
class UserManager:
    def __init__(self, config_path: str = 'configs/users.yaml'):
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
        Sistema de validación de doble red con blindaje polimórfico (**kwargs).
        Absorbe cualquier parámetro legacy (como 'ip') sin colapsar.
        """
        ip = kwargs.get("ip", "0.0.0.0") # El sistema lo absorbe pero no explota si no existe
        
        # =========================================================
        # INTENTO 1: Data Mesh (Supabase)
        # =========================================================
        if self.supabase:
            try:
                user_data = None
                
                # Intentamos buscar en la tabla 'saas_consultores' primero (si el email se usa como username)
                try:
                    res = self.supabase.table("saas_consultores").select("*").eq("email", username).execute()
                    if res.data:
                        # OJO: La tabla saas_consultores actual no tiene password_hash. 
                        # Si entra aquí, forzamos el fallback local para validar la contraseña,
                        # o asumimos que es un usuario sin acceso via web directa aún.
                        pass 
                except Exception:
                    pass

                # Intentamos la tabla confirmada de usuarios
                if not user_data:
                    try:
                        res = self.supabase.table("saas_users").select("*").eq("username", username).execute()
                        if res.data: user_data = res.data[0]
                    except Exception as e:
                        # Falla silenciosa si la tabla no existe o hay RLS
                        print(f"Intento en saas_users fallido: {e}")

                if user_data:
                    stored_hash = user_data.get("password_hash", "")
                    
                    # 🔴 FIX CRÍTICO: Prevención de TypeError criptográfico
                    password_bytes = password.encode('utf-8')
                    hash_bytes = stored_hash.encode('utf-8') if isinstance(stored_hash, str) else stored_hash
                    
                    # Si el hash en BD está vacío, fallamos para usar el local
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
                # Falla silenciosa total para que la red de seguridad local pueda actuar
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
                    
                    # 🔴 FIX CRÍTICO REPLICADO EN LOCAL
                    password_bytes = password.encode('utf-8')
                    hash_bytes = stored_hash.encode('utf-8') if isinstance(stored_hash, str) else stored_hash
                    
                    if bcrypt.checkpw(password_bytes, hash_bytes):
                        return User(
                            id=username,
                            username=username,
                            nombre_completo=user_data.get("nombre_completo", username),
                            email=user_data.get("email", ""),
                            role=user_data.get("role", "Consultor"),
                            client_id=user_data.get("client_id")
                        )
        except Exception as e:
            st.error(f"Error de sistema en validación local: {e}")

        # Si ambas redes fallan, el acceso se deniega
        return None