import bcrypt
import yaml
import os
from datetime import datetime

# 1. Crear el directorio si no existe
os.makedirs('configs', exist_ok=True)

# 2. Definir credenciales maestras (Cámbialas si quieres, pero deben tener Mayúscula, Minúscula y Número)
plain_password = "Password123"

# 3. Encriptación de grado militar (bcrypt)
salt = bcrypt.gensalt()
hashed_password = bcrypt.hashpw(plain_password.encode('utf-8'), salt).decode('utf-8')

# 4. Construcción del perfil de usuario
admin_user = {
    "username": "adriel",
    "password_hash": hashed_password,
    "role": "Consultor",
    "nombre_completo": "Adriel Evangelista",
    "email": "director@evangelistaco.com",
    "created_at": datetime.now().isoformat(),
    "last_login": None,
    "is_active": True,
    "created_by": "system",
    "failed_attempts": 0,
    "locked_until": None
}

# 5. Guardado en la bóveda de configuración
data = {"users": [admin_user]}
with open('configs/users.yaml', 'w') as f:
    yaml.dump(data, f, default_flow_style=False)

print("✅ Bóveda de usuarios inicializada.")
print(f"Usuario: {admin_user['username']}")
print(f"Contraseña: {plain_password}")