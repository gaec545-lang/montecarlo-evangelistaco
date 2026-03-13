import streamlit as st
from cryptography.fernet import Fernet

def get_encryption_key() -> bytes:
    try:
        key = st.secrets["ENCRYPTION_KEY"]
        return key.encode('utf-8')
    except Exception:
        raise ValueError("CRÍTICO: ENCRYPTION_KEY no encontrada en .streamlit/secrets.toml")

def encrypt_data(data: str) -> str:
    f = Fernet(get_encryption_key())
    return f.encrypt(data.encode('utf-8')).decode('utf-8')

def decrypt_data(encrypted_data: str) -> str:
    f = Fernet(get_encryption_key())
    return f.decrypt(encrypted_data.encode('utf-8')).decode('utf-8')