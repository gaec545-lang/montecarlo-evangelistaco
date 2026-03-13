from src.configuration_manager import ConfigurationManager
from src.monte_carlo_engine import UniversalMonteCarloEngine
import time
import numpy as np  

print("=" * 60)
print("TEST DE MONTE CARLO ENGINE")
print("=" * 60)

# Test 1: Cargar configuración
print("\n[Test 1] Cargando configuración...")
try:
    config = ConfigurationManager(
        template='templates/alimentos.yaml',
        client_config='clients/test_pasteleria_config.yaml'
    )
    print("✅ Configuración cargada")
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# Test 2: Inicializar engine
print("\n[Test 2] Inicializando Monte Carlo Engine...")
try:
    engine = UniversalMonteCarloEngine(config)
    print("✅ Engine inicializado")
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# Test 3: Cargar datos históricos
print("\n[Test 3] Cargando datos históricos...")
try:
    engine.load_historical_data()
    print("✅ Datos históricos procesados")
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# Test 4: Setup simulación
print("\n[Test 4] Configurando simulación...")
try:
    engine.setup_simulation()
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# Test 5: Ejecutar simulación
print("\n[Test 5] Ejecutando simulación...")
try:
    start = time.time()
    results = engine.run()
    elapsed = time.time() - start
    
    print(f"✅ Simulación completada en {elapsed:.1f} segundos")
    print(f"   Total simulaciones: {len(results):,}")
    print(f"   Variables simuladas: {len([c for c in results.columns if c not in ['outcome', 'simulation_id']])}")
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# Test 6: Estadísticas
print("\n[Test 6] Calculando estadísticas...")
try:
    stats = engine.get_statistics()
    
    print("✅ Estadísticas calculadas:")
    print(f"\n   📊 RESULTADOS:")
    print(f"   ├─ Media (P50): ${stats['mean']:,.0f}")
    print(f"   ├─ Mediana: ${stats['median']:,.0f}")
    print(f"   ├─ Desviación estándar: ${stats['std']:,.0f}")
    print(f"   ├─ Mínimo: ${stats['min']:,.0f}")
    print(f"   └─ Máximo: ${stats['max']:,.0f}")
    
    print(f"\n   📈 PERCENTILES:")
    print(f"   ├─ P10 (pesimista): ${stats['p10']:,.0f}")
    print(f"   ├─ P50 (mediana): ${stats['p50']:,.0f}")
    print(f"   └─ P90 (optimista): ${stats['p90']:,.0f}")
    
    print(f"\n   ⚠️  RIESGOS:")
    print(f"   ├─ Probabilidad de pérdida: {stats['prob_loss']:.1%}")
    print(f"   ├─ VaR 95%: ${abs(stats['var_95']):,.0f}")
    print(f"   └─ CVaR 95%: ${abs(stats['cvar_95']):,.0f}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# Test 7: Análisis de sensibilidad
print("\n[Test 7] Análisis de sensibilidad...")
try:
    sensitivity = engine.sensitivity_analysis()
    
    print("✅ Análisis completado:")
    print("\n   📊 IMPACTO DE VARIABLES:")
    for idx, row in sensitivity.iterrows():
        bar_length = int(row['importance'] * 50)
        bar = "█" * bar_length
        print(f"   {row['variable']:20} {bar} {row['importance']:.1%}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# Test 8: Validar resultados
print("\n[Test 8] Validando resultados...")
try:
    # Verificar que no hay NaN o infinitos
    assert not results['outcome'].isna().any(), "Hay NaN en resultados"
    assert not np.isinf(results['outcome']).any(), "Hay infinitos en resultados"
    
    # Verificar que prob_loss tiene sentido
    assert 0 <= stats['prob_loss'] <= 1, "Prob pérdida fuera de rango"
    
    # Verificar que P50 está entre min y max
    assert stats['min'] <= stats['p50'] <= stats['max'], "P50 fuera de rango"
    
    print("✅ Resultados validados (sin errores lógicos)")
    
except AssertionError as e:
    print(f"❌ {e}")
    exit(1)

print("\n" + "=" * 60)
print("🎉 TODOS LOS TESTS DE MONTE CARLO PASARON")
print("=" * 60)

# Test 8: Validar resultados lógicos
print("\n[Test 8] Validando resultados...")
try:
    assert not results['outcome'].isna().any(), "Hay NaN en resultados"
    assert not np.isinf(results['outcome']).any(), "Hay infinitos en resultados"
    assert 0 <= stats['prob_loss'] <= 1, "Prob pérdida fuera de rango"
    print("✅ Resultados validados (sin errores lógicos)")
except AssertionError as e:
    print(f"❌ {e}")
    exit(1)

# Test 9: Evaluar Triggers de Decision Intelligence
print("\n[Test 9] Evaluando Triggers de Negocio (Sentinel)...")
try:
    # Llamamos al nuevo método que construyó Claude
    triggers = engine.evaluate_triggers(stats)
    
    if triggers:
        print(f"🚨 {len(triggers)} TRIGGER(S) ACTIVADO(S):\n")
        
        # Agrupar por nivel
        criticos = [t for t in triggers if t['nivel'] == 'CRÍTICO']
        altos = [t for t in triggers if t['nivel'] == 'ALTO']
        medios = [t for t in triggers if t.get('nivel') == 'MEDIO']
        
        if criticos:
            print("   🔴 ALERTAS CRÍTICAS:")
            for trigger in criticos:
                print(f"      • {trigger['metrica']}: {trigger['mensaje']}")
        
        if altos:
            print("   🟡 ALERTAS ALTAS:")
            for trigger in altos:
                print(f"      • {trigger['metrica']}: {trigger['mensaje']}")
                
        if medios:
            print("   🟠 ALERTAS MEDIAS:")
            for trigger in medios:
                print(f"      • {trigger['metrica']}: {trigger['mensaje']}")
    else:
        print("   ✅ No hay alertas de riesgo.")
        print("   ✅ Todos los indicadores operativos están dentro de los umbrales del YAML.")
        
except AttributeError:
    print("❌ Error: El método 'evaluate_triggers' no se encontró en UniversalMonteCarloEngine.")
    print("💡 Asegúrate de haber guardado src/monte_carlo_engine.py con el nuevo código de la Fase 2.")
except Exception as e:
    print(f"❌ Error inesperado al evaluar triggers: {e}")

print("\n" + "=" * 60)
print("🎉 FASE 2 COMPLETADA: MOTOR Y TRIGGERS OPERATIVOS")
print("=" * 60)
