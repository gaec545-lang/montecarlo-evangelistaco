import time
import logging
from src.configuration_manager import ConfigurationManager
from src.data_extraction_engine import DataExtractionEngine
from src.monte_carlo_engine import UniversalMonteCarloEngine
from src.business_translator import BusinessTranslator
from src.decision_intelligence_engine import DecisionIntelligenceEngine
from src.forecasting_engine import ForecastingEngine

logger = logging.getLogger(__name__)


class PipelineExecutionError(Exception):
    pass


class DecisionPipeline:
    """Pipeline maestro para Decision Intelligence (3 Escudos)"""

    def __init__(self, config: ConfigurationManager, supabase_credentials: dict = None):
        self.config = config
        self.supabase_creds = supabase_credentials
        self.client_id = config.get('client.id')

        self.data_engine = DataExtractionEngine(self.supabase_creds, self.config) if self.supabase_creds else None
        self.mc_engine = UniversalMonteCarloEngine(self.config)
        self.decision_engine = DecisionIntelligenceEngine(self.config)

        self.pipeline_state = {
            'phase_0_completed': False,
            'phase_1_completed': False, 'phase_2_completed': False,
            'phase_3_completed': False, 'phase_4_completed': False,
            'execution_time': {}
        }

    def run_phase(self, phase_number: int, phase_name: str, phase_function):
        print(f"\n{'='*60}\nFASE {phase_number}: {phase_name}\n{'='*60}")
        start_time = time.time()
        try:
            result = phase_function()
            elapsed = time.time() - start_time
            self.pipeline_state[f'phase_{phase_number}_completed'] = True
            self.pipeline_state['execution_time'][phase_name] = elapsed
            print(f"✅ FASE {phase_number} completada en {elapsed:.2f}s")
            return result
        except Exception as e:
            print(f"❌ FASE {phase_number} falló: {str(e)}")
            raise PipelineExecutionError(f"Pipeline detenido en Fase {phase_number}: {e}")

    def run_forecasting(self, horizonte_meses: int = 12) -> dict:
        """
        FASE 0: Escudo 1 - Radar (Forecasting Engine).
        Proyecta ingresos, costos y volatilidad macro a 12 meses.
        No lanza excepción si falla: devuelve resultados vacíos para no bloquear el pipeline.
        """
        try:
            engine = ForecastingEngine(
                supabase_creds=self.supabase_creds,
                client_id=self.client_id,
            )
            engine.load_data(use_dummy=(not self.supabase_creds))
            return engine.run_all(horizonte_meses=horizonte_meses)
        except Exception as e:
            logger.warning(f"ForecastingEngine falló (continuando con pipeline): {e}")
            return {"error": str(e), "horizonte_meses": horizonte_meses}

    def execute(self, horizonte_meses: int = 12) -> dict:
        # FASE 0: Escudo 1 - Forecasting (nueva)
        # Proyección temporal a 12 meses - no bloquea el pipeline si falla
        forecasting_results = self.run_phase(
            0, "Escudo 1 - Forecasting Engine (Radar)",
            lambda: self.run_forecasting(horizonte_meses)
        )

        # FASE 1: Extracción (mantenida por compatibilidad)
        extracted_data = {}
        self.pipeline_state['phase_1_completed'] = True

        # FASE 2: Monte Carlo
        def run_mc():
            self.mc_engine.load_historical_data()
            self.mc_engine.setup_simulation()
            return {
                'results': self.mc_engine.run(),
                'statistics': self.mc_engine.get_statistics(),
                'sensitivity': self.mc_engine.sensitivity_analysis()
            }

        mc_results = self.run_phase(2, "Monte Carlo Simulation Engine", run_mc)

        # FASE 3: Traductor de Negocios
        business_narrative = self.run_phase(3, "Business Translator",
            lambda: BusinessTranslator(self.config, extracted_data).translate(mc_results['statistics'], mc_results['sensitivity']))

        # FASE 4: Inteligencia de Decisiones
        decision_results = self.run_phase(4, "Decision Intelligence Engine",
            lambda: self.decision_engine.generate_recommendations(mc_results['statistics'], mc_results['sensitivity']))

        return {
            'raw_data': extracted_data,
            'forecasting_results': forecasting_results,       # NUEVO: Escudo 1
            'simulation_results': mc_results['results'],
            'statistics': mc_results['statistics'],
            'sensitivity': mc_results['sensitivity'],
            'business_narrative': business_narrative,
            'recommendations': decision_results,
            'execution_summary': self.pipeline_state
        }
