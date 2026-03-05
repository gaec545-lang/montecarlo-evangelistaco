import pandas as pd
from typing import Dict
import sqlalchemy
from src.configuration_manager import ConfigurationManager
from src.connection_manager import ConnectionManager

class DataExtractionEngine:
    """Extractor Dinámico de Datos Corporativos - Fase 1"""
    
    def __init__(self, supabase_credentials: dict, config: ConfigurationManager):
        # Mantenemos supabase_credentials en los argumentos para no romper el DecisionPipeline
        self.config = config
        self.client_engine = None
        self.extracted_data = {}
        
        # El motor necesita saber a qué cliente está auditando para buscar su llave
        self.client_id = self.config.get('client.id', 'default_client')
        
    def connect(self):
        print(f"\n🔗 Iniciando protocolo de ingesta para cliente: {self.client_id}")
        try:
            # 1. Recuperar la llave encriptada desde la Bóveda Central de Evangelista & Co.
            conn_manager = ConnectionManager()
            client_uri = conn_manager.get_connection(self.client_id)
            
            # 2. Establecer el puente al servidor operativo del cliente
            self.client_engine = sqlalchemy.create_engine(client_uri, pool_pre_ping=True)
            with self.client_engine.connect() as conn:
                pass
            print("✅ Conexión establecida con el servidor de base de datos del cliente.")
            
        except ValueError as e:
            print(f"⚠️ {e}")
            print("⚠️ El motor operará en modo estático (Fallback YAML).")
        except Exception as e:
            print(f"❌ Error al penetrar el servidor del cliente: {e}")
            print("⚠️ El motor operará en modo estático (Fallback YAML).")

    def extract_variable_data(self, variable_name: str, table_name: str) -> pd.DataFrame:
        if not self.client_engine:
            raise ConnectionError("No hay túnel de datos activo con el cliente.")
            
        # Asumimos un esquema estándar en las bases de datos de los clientes (fecha, valor)
        query = f"SELECT fecha, valor FROM {table_name} ORDER BY fecha ASC"
        df = pd.read_sql(query, self.client_engine)
        
        if len(df) < 10:
            raise ValueError(f"Volumen de datos histórico insuficiente (mínimo 10 registros).")
            
        return df

    def extract_all_variables(self) -> Dict[str, pd.DataFrame]:
        variables = self.config.get_variables()
        
        for var in variables:
            var_name = var['name']
            # Busca el mapeo SQL exacto en el YAML, o infiere un nombre lógico
            table_name = var.get('sql_table', f"historico_{var_name}")
            
            try:
                df = self.extract_variable_data(var_name, table_name)
                self.extracted_data[var_name] = df
                print(f"   📊 {var_name}: Ingesta de {len(df)} registros corporativos exitosa.")
            except Exception as e:
                print(f"   ⚠️ Fallo en ingesta de '{var_name}': {e} -> Usando parámetros estáticos.")
                
        return self.extracted_data
        
    def close(self):
        # Destruir la conexión para liberar recursos de Railway
        if self.client_engine:
            self.client_engine.dispose()