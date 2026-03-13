from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError, OperationalError
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import logging
from contextlib import contextmanager

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseConnectionError(Exception):
    """Excepción para errores de conexión a base de datos"""
    pass


class DatabaseQueryError(Exception):
    """Excepción para errores en ejecución de queries"""
    pass


class DatabaseConnector:
    """
    Conector universal para Data Mesh con connection pooling
    
    Soporta:
    - PostgreSQL (production primary)
    - SQL Server (enterprise clients)
    - MySQL (legacy support)
    
    Ejemplo de uso:
        connector = DatabaseConnector(
            engine='postgresql',
            host='data-mesh.evangelista.com',
            port=5432,
            database='sentinel_prod',
            username='sentinel_reader',
            password='***'
        )
        
        with connector.get_connection():
            df = connector.query_time_series(
                table='fact_costos_insumos',
                date_column='fecha',
                value_column='costo_unitario',
                filters={'insumo_id': 'HARINA_001'}
            )
    """
    
    # Connection strings por motor
    CONNECTION_TEMPLATES = {
        'postgresql': 'postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}',
        'sqlserver': 'mssql+pyodbc://{username}:{password}@{host}:{port}/{database}?driver=ODBC+Driver+17+for+SQL+Server',
        'mysql': 'mysql+pymysql://{username}:{password}@{host}:{port}/{database}'
    }
    
    def __init__(self,
                 engine: str,
                 host: str,
                 database: str,
                 username: str,
                 password: str,
                 port: Optional[int] = None,
                 pool_size: int = 5,
                 max_overflow: int = 10,
                 pool_timeout: int = 30):
        """
        Inicializa conector con connection pooling
        
        Args:
            engine: Tipo de base de datos ('postgresql', 'sqlserver', 'mysql')
            host: Hostname o IP del servidor
            database: Nombre de la base de datos
            username: Usuario con permisos de lectura
            password: Contraseña
            port: Puerto (usa defaults si None)
            pool_size: Tamaño del connection pool
            max_overflow: Conexiones adicionales permitidas
            pool_timeout: Timeout en segundos
            
        Raises:
            ValueError: Si engine no es soportado
            DatabaseConnectionError: Si no puede establecer conexión inicial
        """
        if engine not in self.CONNECTION_TEMPLATES:
            raise ValueError(
                f"Engine '{engine}' no soportado. "
                f"Opciones: {list(self.CONNECTION_TEMPLATES.keys())}"
            )
        
        self.engine_type = engine
        self.host = host
        self.database = database
        self.username = username
        self.port = port or self._get_default_port(engine)
        
        # Construir connection string
        connection_string = self.CONNECTION_TEMPLATES[engine].format(
            username=username,
            password=password,
            host=host,
            port=self.port,
            database=database
        )
        
        # Crear engine con pooling
        try:
            self.engine: Engine = create_engine(
                connection_string,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_timeout=pool_timeout,
                pool_pre_ping=True,  # Verifica conexiones antes de usar
                echo=False  # Set True para debugging SQL
            )
            
            # Test de conexión inicial
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info(
                f"✅ DatabaseConnector inicializado: {engine}://{host}:{self.port}/{database}"
            )
            
        except OperationalError as e:
            raise DatabaseConnectionError(
                f"❌ No se pudo conectar a {engine}://{host}:{self.port}/{database}\n"
                f"Error: {str(e)}\n"
                f"Verifica: credenciales, firewall, servicio activo"
            )
        except SQLAlchemyError as e:
            raise DatabaseConnectionError(
                f"❌ Error en SQLAlchemy: {str(e)}"
            )
    
    @staticmethod
    def _get_default_port(engine: str) -> int:
        """Retorna puerto default por motor"""
        defaults = {
            'postgresql': 5432,
            'sqlserver': 1433,
            'mysql': 3306
        }
        return defaults[engine]
    
    @contextmanager
    def get_connection(self):
        """
        Context manager para conexiones seguras
        
        Uso:
            with connector.get_connection() as conn:
                result = conn.execute(text("SELECT * FROM tabla"))
        """
        connection = self.engine.connect()
        try:
            yield connection
        except SQLAlchemyError as e:
            logger.error(f"❌ Error en query: {str(e)}")
            raise DatabaseQueryError(f"Query falló: {str(e)}")
        finally:
            connection.close()
    
    def query_time_series(self,
                         table: str,
                         date_column: str,
                         value_column: str,
                         filters: Optional[Dict[str, Any]] = None,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None,
                         order_by: str = 'ASC') -> pd.DataFrame:
        """
        Extrae serie temporal de la base de datos
        
        Args:
            table: Nombre de la tabla (ej: 'fact_costos_insumos')
            date_column: Columna de fecha
            value_column: Columna con valor a analizar
            filters: Dict con filtros WHERE (ej: {'insumo_id': 'HARINA_001'})
            start_date: Fecha inicio (opcional)
            end_date: Fecha fin (opcional)
            order_by: Orden temporal ('ASC' o 'DESC')
            
        Returns:
            DataFrame con columnas ['fecha', 'valor']
            
        Raises:
            DatabaseQueryError: Si query falla
        """
        # Construir query parametrizada (previene SQL injection)
        query_parts = [
            f"SELECT {date_column} as fecha, {value_column} as valor",
            f"FROM {table}",
            "WHERE 1=1"
        ]
        
        params = {}
        
        # Agregar filtros
        if filters:
            for idx, (key, value) in enumerate(filters.items()):
                param_name = f"filter_{idx}"
                query_parts.append(f"AND {key} = :{param_name}")
                params[param_name] = value
        
        # Filtros de fecha
        if start_date:
            query_parts.append(f"AND {date_column} >= :start_date")
            params['start_date'] = start_date
        
        if end_date:
            query_parts.append(f"AND {date_column} <= :end_date")
            params['end_date'] = end_date
        
        # Ordenar
        query_parts.append(f"ORDER BY {date_column} {order_by}")
        
        query = " ".join(query_parts)
        
        logger.info(f"📊 Ejecutando query en {table}...")
        
        try:
            df = pd.read_sql(
                text(query),
                self.engine,
                params=params
            )
            
            if df.empty:
                logger.warning(
                    f"⚠️  Query retornó 0 filas. "
                    f"Verifica filtros: {filters}"
                )
            else:
                logger.info(
                    f"✅ Serie temporal extraída: {len(df)} registros "
                    f"({df['fecha'].min()} a {df['fecha'].max()})"
                )
            
            # Convertir fecha a datetime si no lo es
            df['fecha'] = pd.to_datetime(df['fecha'])
            
            # Ordenar por fecha (seguridad adicional)
            df = df.sort_values('fecha').reset_index(drop=True)
            
            return df
            
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                f"❌ Error ejecutando query en tabla '{table}':\n{str(e)}"
            )
    
    def list_tables(self, schema: Optional[str] = None) -> List[str]:
        """
        Lista todas las tablas disponibles
        
        Args:
            schema: Schema específico (opcional)
            
        Returns:
            Lista de nombres de tablas
        """
        inspector = inspect(self.engine)
        
        if schema:
            tables = inspector.get_table_names(schema=schema)
        else:
            tables = inspector.get_table_names()
        
        return tables
    
    def get_table_schema(self, table: str) -> pd.DataFrame:
        """
        Obtiene schema de una tabla
        
        Args:
            table: Nombre de la tabla
            
        Returns:
            DataFrame con columnas, tipos y constraints
        """
        inspector = inspect(self.engine)
        
        columns = inspector.get_columns(table)
        
        schema_info = []
        for col in columns:
            schema_info.append({
                'columna': col['name'],
                'tipo': str(col['type']),
                'nullable': col['nullable'],
                'default': col.get('default')
            })
        
        return pd.DataFrame(schema_info)
    
    def validate_connection(self) -> Tuple[bool, str]:
        """
        Valida que la conexión esté activa
        
        Returns:
            (is_valid, message)
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True, "✅ Conexión activa"
        except SQLAlchemyError as e:
            return False, f"❌ Conexión caída: {str(e)}"
    
    def close(self):
        """Cierra connection pool"""
        self.engine.dispose()
        logger.info("🔒 Connection pool cerrado")
    
    def __repr__(self) -> str:
        """Representación string"""
        return (
            f"<DatabaseConnector: {self.engine_type}://"
            f"{self.host}:{self.port}/{self.database}>"
        )
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
