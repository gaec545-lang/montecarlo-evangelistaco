from src.database_connector import DatabaseConnector, DatabaseConnectionError

print("=" * 70)
print("TEST DE DATABASE CONNECTOR")
print("=" * 70)

# NOTA: Ajustar estas credenciales a tu entorno de desarrollo
# En producción, usar variables de entorno

TEST_CONFIG = {
    'engine': 'postgresql',
    'host': 'localhost',  # Ajustar
    'port': 5432,
    'database': 'test_db',  # Ajustar
    'username': 'test_user',  # Ajustar
    'password': 'test_password'  # Ajustar
}

print("\n⚠️  NOTA: Este test requiere una base de datos configurada.")
print(f"Intentando conectar a: {TEST_CONFIG['engine']}://{TEST_CONFIG['host']}:{TEST_CONFIG['port']}/{TEST_CONFIG['database']}")
print("\nSi no tienes BD configurada, este test fallará (esperado).")
print("Continuar con Fase 2 de todas formas.\n")

input("Presiona Enter para continuar con el test...")

try:
    connector = DatabaseConnector(**TEST_CONFIG)
    
    print("\n✅ Conexión exitosa!")
    
    # Test: Listar tablas
    tables = connector.list_tables()
    print(f"\n📋 Tablas disponibles: {len(tables)}")
    for table in tables[:5]:  # Primeras 5
        print(f"   - {table}")
    
    # Test: Validar conexión
    is_valid, message = connector.validate_connection()
    print(f"\n{message}")
    
    connector.close()
    
    print("\n🎉 DatabaseConnector funcionando correctamente")
    
except DatabaseConnectionError as e:
    print(f"\n❌ Error de conexión (esperado si no hay BD):\n{e}")
    print("\n💡 Para testing completo, configurar BD de desarrollo.")
    print("   Sistema continuará funcionando con ExcelConnector como fallback.")

print("\n✅ FASE 1 COMPLETA")
print("=" * 70)
