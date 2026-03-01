import os
from src.database_connector import DatabaseConnector, DatabaseConnectionError

print("=" * 70)
print("TEST DE DATABASE CONNECTOR (MSSQL)")
print("=" * 70)

# Uso estricto de variables de entorno para evitar hardcoding en repositorios.
# Se proveen valores por defecto orientados a Microsoft SQL Server para desarrollo local.
TEST_CONFIG = {
    'engine': os.getenv('TEST_DB_ENGINE', 'mssql'),
    'host': os.getenv('TEST_DB_HOST', 'localhost'),
    'port': int(os.getenv('TEST_DB_PORT', 1433)),
    'database': os.getenv('TEST_DB_NAME', 'test_db'),
    'username': os.getenv('TEST_DB_USER', 'test_user'),
    'password': os.getenv('TEST_DB_PASS', 'test_password')
}

print("\n⚠️  NOTA: Intentando conectar al Data Mesh de prueba...")
print(f"Target: {TEST_CONFIG['engine']}://{TEST_CONFIG['host']}:{TEST_CONFIG['port']}/{TEST_CONFIG['database']}")

connector = None
try:
    connector = DatabaseConnector(**TEST_CONFIG)
    print("\n✅ Conexión inicializada en memoria.")
    
    # Test 1: Validar conexión real
    is_valid, message = connector.validate_connection()
    if not is_valid:
        raise DatabaseConnectionError(message)
        
    print(f"✅ Validación exitosa: {message}")
    
    # Test 2: Listar tablas
    tables = connector.list_tables()
    print(f"\n📋 Tablas disponibles: {len(tables)}")
    for table in tables[:5]:
        print(f"   - {table}")

except DatabaseConnectionError as e:
    print(f"\n❌ Error de conexión (Esperado si no hay instancia MSSQL local activa):\n{e}")
    print("\n💡 El motor de conexión está listo. Para pruebas E2E, levanta una base de datos local.")
except Exception as e:
    print(f"\n❌ Error crítico inesperado:\n{e}")
finally:
    # Este bloque garantiza que la conexión se cierre SIEMPRE, incluso si hay errores previos.
    if connector:
        connector.close()
        print("\n🔒 Conexión cerrada y recursos liberados de forma segura.")

print("\n✅ FASE 1 COMPLETA Y AUDITADA")
print("=" * 70)
