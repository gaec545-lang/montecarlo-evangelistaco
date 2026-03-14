import os
import bcrypt
import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta
import uuid

class UserManager:
    """
    Gestiona autenticación y usuarios en Supabase.
    NO usa SQLAlchemy ni archivos YAML.
    """
    
    def __init__(self):
        """Inicializa conexión a Supabase."""
        # Obtener credenciales
        try:
            self.supabase_url = st.secrets.get("SUPABASE_URL")
            self.supabase_key = st.secrets.get("SUPABASE_KEY")
        except:
            self.supabase_url = os.getenv("SUPABASE_URL")
            self.supabase_key = os.getenv("SUPABASE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("❌ Faltan SUPABASE_URL o SUPABASE_KEY en secrets.toml")
        
        # Crear cliente de Supabase
        self.supabase = create_client(self.supabase_url, self.supabase_key)
    
    def authenticate(self, username: str, password: str) -> dict:
        """
        Autentica un usuario.
        
        Returns:
            dict con datos del usuario si éxito, None si falla
        """
        try:
            # Buscar usuario en Supabase
            response = self.supabase.table('saas_users').select('*').eq('username', username).execute()
            
            if not response.data or len(response.data) == 0:
                return None
            
            user = response.data[0]
            
            # Verificar si está bloqueado
            if user.get('locked_until'):
                locked_until = datetime.fromisoformat(user['locked_until'].replace('Z', '+00:00'))
                if datetime.now(locked_until.tzinfo) < locked_until:
                    return None
            
            # Verificar si está activo
            if not user.get('is_active', True):
                return None
            
            # Verificar password
            password_hash = user['password_hash']
            if bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                # Login exitoso - resetear intentos fallidos
                self.supabase.table('saas_users').update({
                    'failed_attempts': 0,
                    'last_login': datetime.now().isoformat()
                }).eq('id', user['id']).execute()
                
                return user
            else:
                # Login fallido - incrementar intentos
                failed_attempts = user.get('failed_attempts', 0) + 1
                update_data = {'failed_attempts': failed_attempts}
                
                # Bloquear si excede 5 intentos
                if failed_attempts >= 5:
                    update_data['locked_until'] = (datetime.now() + timedelta(minutes=15)).isoformat()
                
                self.supabase.table('saas_users').update(update_data).eq('id', user['id']).execute()
                
                return None
        
        except Exception as e:
            print(f"❌ Error en authenticate: {e}")
            return None
    
    def create_user(self, username: str, password: str, role: str = 'consultor', 
                   nombre_completo: str = None, email: str = None, client_id: str = None) -> bool:
        """
        Crea un nuevo usuario en Supabase.
        
        Args:
            username: Nombre de usuario único
            password: Contraseña en texto plano (se hasheará)
            role: Rol (admin, consultor, cliente)
            nombre_completo: Nombre completo opcional
            email: Email opcional
            client_id: UUID del cliente (si role=cliente)
        
        Returns:
            True si éxito, False si falla
        """
        try:
            # Hash password con bcrypt
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Crear usuario
            user_data = {
                'id': str(uuid.uuid4()),
                'username': username,
                'password_hash': password_hash,
                'role': role,
                'nombre_completo': nombre_completo,
                'email': email,
                'client_id': client_id,
                'is_active': True,
                'failed_attempts': 0,
                'created_at': datetime.now().isoformat()
            }
            
            self.supabase.table('saas_users').insert(user_data).execute()
            return True
        
        except Exception as e:
            print(f"❌ Error creando usuario: {e}")
            return False
    
    def get_user(self, username: str) -> dict:
        """Obtiene datos de un usuario por username."""
        try:
            response = self.supabase.table('saas_users').select('*').eq('username', username).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            print(f"❌ Error obteniendo usuario: {e}")
            return None
    
    def list_users(self) -> list:
        """Lista todos los usuarios."""
        try:
            response = self.supabase.table('saas_users').select('*').order('created_at', desc=True).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"❌ Error listando usuarios: {e}")
            return []
    
    def update_user(self, user_id: str, **kwargs) -> bool:
        """
        Actualiza datos de un usuario.
        
        Args:
            user_id: UUID del usuario
            **kwargs: Campos a actualizar (role, nombre_completo, email, is_active, etc.)
        """
        try:
            # Si se actualiza password, hashear
            if 'password' in kwargs:
                kwargs['password_hash'] = bcrypt.hashpw(
                    kwargs.pop('password').encode('utf-8'), 
                    bcrypt.gensalt()
                ).decode('utf-8')
            
            self.supabase.table('saas_users').update(kwargs).eq('id', user_id).execute()
            return True
        except Exception as e:
            print(f"❌ Error actualizando usuario: {e}")
            return False
    
    def delete_user(self, user_id: str) -> bool:
        """Elimina un usuario (soft delete - marca como inactivo)."""
        try:
            self.supabase.table('saas_users').update({'is_active': False}).eq('id', user_id).execute()
            return True
        except Exception as e:
            print(f"❌ Error eliminando usuario: {e}")
            return False
    
    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """Cambia la contraseña de un usuario."""
        try:
            # Verificar password actual
            if not self.authenticate(username, old_password):
                return False
            
            # Obtener usuario
            user = self.get_user(username)
            if not user:
                return False
            
            # Hash nuevo password
            new_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Actualizar en Supabase
            self.supabase.table('saas_users').update({
                'password_hash': new_hash
            }).eq('id', user['id']).execute()
            
            return True
        except Exception as e:
            print(f"❌ Error cambiando password: {e}")
            return False