"""
Test simple de ConfigurationManager
Ejecutar desde la raíz: python3 test_simple.py
"""

from src.configuration_manager import ConfigurationManager

print("=" * 60)
print("TEST DE CONFIGURATION MANAGER")
print("=" * 60)

# Test 1: Cargar configuración
print("\n[Test 1] Cargando configuración...")
try:
    config = ConfigurationManager(
        template='templates/alimentos.yaml',
        client_config='clients/test_pasteleria_config.yaml'
    )
    print("✅ Configuración cargada exitosamente")
    print(f"   Cliente: {config.get('client.name')}")
    print(f"   Industria: {config.get('client.industry')}")
except Exception as e:
    print(f"❌ Error al cargar: {e}")
    exit(1)

# Test 2: Acceso con dot notation
print("\n[Test 2] Acceso a parámetros con dot notation...")
try:
    precio = config.get('business_parameters.precio_venta_unitario')
    assert precio == 45, f"Esperaba 45, obtuve {precio}"
    print(f"✅ Precio venta: ${precio}")
    
    receta_harina = config.get('business_parameters.receta.harina')
    assert receta_harina == 0.5, f"Esperaba 0.5, obtuve {receta_harina}"
    print(f"✅ Receta harina: {receta_harina} kg/unidad")
    
    costo_fijo = config.get('business_parameters.costo_fijo_mensual')
    print(f"✅ Costo fijo mensual: ${costo_fijo:,}")
except AssertionError as e:
    print(f"❌ Error en assertion: {e}")
    exit(1)
except Exception as e:
    print(f"❌ Error inesperado: {e}")
    exit(1)

# Test 3: Default value
print("\n[Test 3] Probando default value...")
try:
    inexistente = config.get('parametro.que.no.existe', default=999)
    assert inexistente == 999, f"Default value falló: {inexistente}"
    print(f"✅ Default value funciona correctamente: {inexistente}")
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# Test 4: Get variables
print("\n[Test 4] Obteniendo variables comunes...")
try:
    variables = config.get_variables()
    print(f"✅ Variables encontradas: {len(variables)}")
    for var in variables:
        print(f"   - {var['name']}: {var['description']}")
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# Test 5: Get distribution config
print("\n[Test 5] Obteniendo configuración de distribución...")
try:
    dist_config = config.get_distribution_config('precio_harina')
    print(f"✅ Distribución para precio_harina: {dist_config['type']}")
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# Test 6: Validación
print("\n[Test 6] Validando configuración...")
try:
    is_valid, errors = config.validate()
    if is_valid:
        print("✅ Configuración válida")
    else:
        print("❌ Configuración inválida:")
        for error in errors:
            print(f"   - {error}")
        exit(1)
except Exception as e:
    print(f"❌ Error en validación: {e}")
    exit(1)

# Resumen final
print("\n" + "=" * 60)
print("🎉 TODOS LOS TESTS PASARON EXITOSAMENTE")
print("=" * 60)
print(f"\nConfigManager: {config}")
print("\n✅ Sistema listo para siguiente paso (Monte Carlo Engine)")