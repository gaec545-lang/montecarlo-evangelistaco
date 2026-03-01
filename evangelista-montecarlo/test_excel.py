from src.excel_connector import ExcelConnector

print("=" * 60)
print("TEST DE EXCEL CONNECTOR")
print("=" * 60)

# Test 1: Cargar archivo
print("\n[Test 1] Cargando archivo Excel...")
try:
    connector = ExcelConnector('data/costos_ejemplo.xlsx')
    print(f"✅ Archivo cargado: {connector}")
except FileNotFoundError as e:
    print(f"❌ {e}")
    print("\n💡 Solución: Ejecuta primero 'python3 crear_excel_ejemplo.py'")
    exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# Test 2: Listar hojas
print("\n[Test 2] Listando hojas...")
try:
    sheets = connector.list_sheets()
    print(f"✅ Hojas encontradas: {sheets}")
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# Test 3: Leer hoja
print("\n[Test 3] Leyendo hoja 'Costos'...")
try:
    df = connector.read_sheet('Costos')
    print(f"✅ Datos leídos: {len(df)} filas, {len(df.columns)} columnas")
    print(f"\nPrimeras 3 filas:")
    print(df.head(3))
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# Test 4: Verificar limpieza
print("\n[Test 4] Verificando limpieza de datos...")
try:
    # Verificar que no hay valores nulos en columnas críticas
    assert df['Insumo'].notna().all(), "Hay valores nulos en Insumo"
    assert df['Costo_kg'].notna().all(), "Hay valores nulos en Costo_kg"
    print("✅ Datos limpios (sin nulos en columnas críticas)")
    
    # Verificar tipos
    assert df['Fecha'].dtype == 'datetime64[ns]', "Fecha no es datetime"
    print("✅ Tipos de datos correctos (Fecha es datetime)")
except AssertionError as e:
    print(f"❌ {e}")
    exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# Test 5: Info de columnas
print("\n[Test 5] Información de columnas...")
try:
    info = connector.get_column_info('Costos')
    print("✅ Info de columnas:")
    print(info)
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# Test 6: Filtrar datos
print("\n[Test 6] Filtrando datos de Harina...")
try:
    df_harina = df[df['Insumo'] == 'Harina']
    print(f"✅ Filas de Harina: {len(df_harina)}")
    print(f"   Costo promedio: ${df_harina['Costo_kg'].mean():.2f}")
    print(f"   Costo mínimo: ${df_harina['Costo_kg'].min():.2f}")
    print(f"   Costo máximo: ${df_harina['Costo_kg'].max():.2f}")
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

print("\n" + "=" * 60)
print("🎉 TODOS LOS TESTS DE EXCEL PASARON")
print("=" * 60)
print("\n✅ ExcelConnector listo")
print("✅ Siguiente paso: Crear MonteCarloEngine")