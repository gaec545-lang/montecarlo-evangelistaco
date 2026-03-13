from sqlalchemy import create_engine, Column, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import streamlit as st
from src.security import encrypt_data, decrypt_data

Base = declarative_base()

class ClientConnection(Base):
    __tablename__ = 'client_connections'
    client_id = Column(String(50), primary_key=True)
    encrypted_uri = Column(Text, nullable=False)
    created_by = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ConnectionManager:
    def __init__(self):
        try:
            db_url = st.secrets["DATABASE_URL"]
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql://", 1)
            self.engine = create_engine(db_url, pool_pre_ping=True)
            Base.metadata.create_all(self.engine)
            Session = sessionmaker(bind=self.engine)
            self.session = Session()
        except Exception as e:
            raise ConnectionError(f"Fallo al conectar con Supabase central: {e}")

    def save_connection(self, client_id: str, raw_uri: str, username: str) -> bool:
        encrypted_uri = encrypt_data(raw_uri)
        existing = self.session.query(ClientConnection).filter_by(client_id=client_id).first()
        if existing:
            existing.encrypted_uri = encrypted_uri
            existing.updated_at = datetime.utcnow()
        else:
            new_conn = ClientConnection(client_id=client_id, encrypted_uri=encrypted_uri, created_by=username)
            self.session.add(new_conn)
        self.session.commit()
        return True

    def get_connection(self, client_id: str) -> str:
        record = self.session.query(ClientConnection).filter_by(client_id=client_id).first()
        if not record:
            raise ValueError(f"No hay conexión registrada para el cliente {client_id}")
        return decrypt_data(record.encrypted_uri)
        
    def get_all_connections(self) -> list:
        # Extrae la metadata sin desencriptar las contraseñas por seguridad
        records = self.session.query(ClientConnection).all()
        return [{
            "client_id": r.client_id, 
            "creado_por": r.created_by, 
            "fecha_creacion": r.created_at.strftime("%Y-%m-%d %H:%M:%S")
        } for r in records]    

    def save_api_connection(self, client_id: str, project_url: str, api_key: str, username: str) -> bool:
        import json
        payload = json.dumps({"url": project_url, "key": api_key})
        encrypted_data = encrypt_data(payload)
        
        existing = self.session.query(ClientConnection).filter_by(client_id=client_id).first()
        if existing:
            existing.encrypted_uri = encrypted_data
            existing.updated_at = datetime.utcnow()
        else:
            new_conn = ClientConnection(client_id=client_id, encrypted_uri=encrypted_data, created_by=username)
            self.session.add(new_conn)
        self.session.commit()
        return True

    def get_api_connection(self, client_id: str) -> dict:
        import json
        record = self.session.query(ClientConnection).filter_by(client_id=client_id).first()
        if not record:
            raise ValueError(f"No hay conexión registrada para el cliente {client_id}")
        
        decrypted_data = decrypt_data(record.encrypted_uri)
        return json.loads(decrypted_data)
