import pandas as pd
import logging
from supabase import create_client, Client
from src.connection_manager import ConnectionManager

class DataExtractionEngine:
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.conn_manager = ConnectionManager()

    def extract_data(self, table_name: str) -> pd.DataFrame:
        logging.info(f"Iniciando extracción API (service_role) para cliente {self.client_id} | Tabla: {table_name}")
        try:
            # 1. Abrimos la bóveda central y extraemos las llaves del cliente
            creds = self.conn_manager.get_api_connection(self.client_id)
            url = creds.get("url")
            key = creds.get("key")

            if not url or not key:
                raise ValueError("Las credenciales API en la bóveda están corruptas o incompletas.")

            # 2. Forjamos el túnel HTTPS de alta velocidad
            supabase: Client = create_client(url, key)

            # 3. Extraemos los datos (Atravesando RLS con service_role)
            # Nota: Supabase limita por defecto a 1000 filas. Forzamos el límite a 50,000 para el Monte Carlo.
            response = supabase.table(table_name).select("*").limit(50000).execute()
            
            # 4. Transformamos el vector JSON en un DataFrame de Pandas estructurado
            data = response.data
            if not data:
                raise ValueError(f"La tabla '{table_name}' está vacía, no existe, o los permisos RLS bloquearon la lectura (verifica que usaste service_role).")
            
            df = pd.DataFrame(data)
            logging.info(f"Extracción exitosa: {len(df)} registros vectorizados listos para simulación.")
            
            return df

        except Exception as e:
            logging.error(f"Fallo crítico en la extracción de datos: {str(e)}")
            raise
