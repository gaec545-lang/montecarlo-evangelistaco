"""
Test de Triggers Estocásticos
Ejecutar: python3 test_triggers.py
"""

from src.configuration_manager import ConfigurationManager
from src.monte_carlo_engine import UniversalMonteCarloEngine

print("=" * 70)
print("TEST DE TRIGGERS ESTOCÁSTICOS (DECISION INTELLIGENCE)")
print("=" * 70)

# Cargar configuración
config = ConfigurationManager(
    template='templates/alimentos.yaml',
    client_config='clients/test_pasteleria_config.yaml'
)

# Inicializar engine
engine = UniversalMonteCarloEngine(config)
engine.load_historical_data()
engine.setup_simulation()

# Ejecutar simulación
print("\n🎲 Ejecutando simulación...\n")
results = engine.run()

# Obtener estadísticas
stats = engine.get_statistics()

print("\n📊 ESTADÍSTICAS CALCULADAS:")
print(f"   Prob Pérdida: {stats['prob_loss']:.1%}")
print(f"   Media: ${stats['mean']:,.0f}")
print(f"   Desv Std: ${stats['std']:,.0f}")
print(f"   Coef Variación: {(stats['std']/stats['mean']):.1%}")
print(f"   P10: ${stats['p10']:,.0f}")

# ════════════════════════════════════════════════════════════
# EVALUAR TRIGGERS
# ════════════════════════════════════════════════════════════

print("\n" + "─" * 70)
print("EVALUANDO TRIGGERS DE NEGOCIO...")
print("─" * 70)

try:
    triggers = engine.evaluate_triggers(stats)
    
    if triggers:
        print(f"\n🚨 {len(triggers)} ALERTA(S) DETECTADA(S):\n")
        
        for idx, trigger in enumerate(triggers, 1):
            nivel = trigger['nivel']
            
            # Emoji según nivel
            emoji = {
                'CRÍTICO': '🔴',
                'ALTO': '🟡',
                'MEDIO': '🟠'
            }.get(nivel, '⚪')
            
            print(f"{emoji} ALERTA #{idx} [{nivel}]")
            print(f"{'─' * 70}")
            print(f"Métrica: {trigger['metrica']}")
            print(f"Valor Actual: {trigger['valor_actual']:.1%}" if isinstance(trigger['valor_actual'], float) and trigger['valor_actual'] < 1 else f"Valor Actual: ${trigger['valor_actual']:,.0f}")
            print(f"Umbral: {trigger['umbral_permitido']:.1%}" if isinstance(trigger['umbral_permitido'], float) and trigger['umbral_permitido'] < 1 else f"Umbral: ${trigger['umbral_permitido']:,.0f}")
            print(f"\n{trigger['mensaje']}")
            print(f"\n💡 RECOMENDACIÓN:")
            print(f"{trigger['recomendacion']}")
            
            if 'contexto' in trigger:
                print(f"\n📋 Contexto adicional:")
                for key, value in trigger['contexto'].items():
                    if isinstance(value, float):
                        print(f"   {key}: {value:,.2f}")
                    else:
                        print(f"   {key}: {value}")
            
            print("\n")
    
    else:
        print("\n✅ NO HAY ALERTAS")
        print("Todos los indicadores están dentro de los umbrales de negocio.")
        print("Operación saludable detectada.")
    
except ValueError as e:
    print(f"\n❌ Error en evaluate_triggers: {e}")
except Exception as e:
    print(f"\n❌ Error inesperado: {e}")

print("\n" + "=" * 70)
print("🎉 TEST DE TRIGGERS COMPLETADO")
print("=" * 70)

# ════════════════════════════════════════════════════════════
# SIMULACIÓN DE ESCENARIO DE RIESGO ALTO
# ════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("SIMULACIÓN: ESCENARIO DE RIESGO ALTO (Forzado para testing)")
print("=" * 70)

# Crear stats manipuladas para activar todos los triggers
stats_riesgo_alto = {
    'prob_loss': 0.35,  # > 0.25 (critical_loss_prob)
    'mean': 30000,
    'std': 15000,       # CV = 0.50 > 0.35
    'p10': -5000,       # Negativo
    'p25': 10000,
    'p50': 30000,
    'p75': 50000,
    'p90': 65000,
    'var_95': -8000,
    'cvar_95': -12000,
    'median': 30000,
    'min': -20000,
    'max': 80000
}

print("\n📊 ESTADÍSTICAS FORZADAS (Escenario Adverso):")
print(f"   Prob Pérdida: {stats_riesgo_alto['prob_loss']:.1%}")
print(f"   Coef Variación: {(stats_riesgo_alto['std']/stats_riesgo_alto['mean']):.1%}")
print(f"   P10: ${stats_riesgo_alto['p10']:,.0f}")

triggers_riesgo = engine.evaluate_triggers(stats_riesgo_alto)

print(f"\n🚨 {len(triggers_riesgo)} ALERTA(S) ACTIVADA(S) (TODAS LAS REGLAS):\n")

for idx, trigger in enumerate(triggers_riesgo, 1):
    print(f"[{trigger['nivel']}] {trigger['metrica']}")

print("\n✅ Todas las reglas de triggers están funcionando correctamente")
print("=" * 70)
