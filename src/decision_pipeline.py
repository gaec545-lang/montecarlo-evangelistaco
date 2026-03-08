import time
from src.configuration_manager import ConfigurationManager
from src.data_extraction_engine import DataExtractionEngine
from src.monte_carlo_engine import UniversalMonteCarloEngine
from src.business_translator import BusinessTranslator
from src.decision_intelligence_engine import DecisionIntelligenceEngine
from src.strategic_advisor import StrategicAdvisor

class PipelineExecutionError(Exception):
    pass

class DecisionPipeline:
    """Pipeline maestro para Decision Intelligence"""

    def __init__(self, config: ConfigurationManager, supabase_credentials: dict = None, groq_api_key: str = None):
        self.config = config
        self.supabase_creds = supabase_credentials
        self.groq_api_key = groq_api_key

        self.data_engine = DataExtractionEngine(self.supabase_creds, self.config) if self.supabase_creds else None
        self.mc_engine = UniversalMonteCarloEngine(self.config)
        self.decision_engine = DecisionIntelligenceEngine(self.config)
        self.strategic_advisor = StrategicAdvisor(groq_api_key) if groq_api_key else None

        self.pipeline_state = {
            'phase_1_completed': False, 'phase_2_completed': False,
            'phase_3_completed': False, 'phase_4_completed': False,
            'phase_5_completed': False,
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
            import traceback
            print(f"❌ FASE {phase_number} falló: {str(e)}")
            print(traceback.format_exc())
            raise PipelineExecutionError(f"Pipeline detenido en Fase {phase_number}: {type(e).__name__}: {e}") from e

    def execute(self) -> dict:
        # FASE 1: Ajuste de Extracción
        # La IA de Llama ya inyectó los parámetros estadísticos en el YAML.
        extracted_data = {}
        self.pipeline_state['phase_1_completed'] = True

        # FASE 2: Simulación Monte Carlo
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

        # FASE 4: Inteligencia de Decisiones (reglas del YAML)
        decision_results = self.run_phase(4, "Decision Intelligence Engine",
            lambda: self.decision_engine.generate_recommendations(mc_results['statistics'], mc_results['sensitivity']))

        # FASE 5: Strategic Advisor (Llama 3.3-70B — opcional si hay API key)
        strategic_analysis = {}
        if self.strategic_advisor:
            def run_strategic_advisor():
                industry = self.config.get('client_info', {}).get('industry', 'General Business')
                client_name = self.config.get('client_info', {}).get('name', 'Client')
                client_context = self.config.get('client_info', {}).get('description', '')
                business_drivers = self.config.get('business_parameters', {}) or {}

                # KPIs y proyecciones desde decision_results si existen
                kpis = decision_results.get('kpis', {}) if isinstance(decision_results, dict) else {}
                projections = decision_results.get('projections', {}) if isinstance(decision_results, dict) else {}

                return self.strategic_advisor.generate_strategic_recommendations(
                    monte_carlo_results={
                        'statistics': mc_results['statistics'],
                        'sensitivity': mc_results['sensitivity'],
                    },
                    kpis=kpis,
                    projections=projections,
                    business_drivers=business_drivers,
                    industry=industry,
                    client_name=client_name,
                    client_context=client_context,
                )

            try:
                strategic_analysis = self.run_phase(5, "Strategic Advisor (Llama 3.3-70B)", run_strategic_advisor)
            except PipelineExecutionError as e:
                print(f"⚠️  Strategic Advisor falló (no crítico): {e}")
                self.pipeline_state['phase_5_completed'] = False
                strategic_analysis = {'error': str(e)}
        else:
            print("\n⏭️  FASE 5: Strategic Advisor omitida (sin GROQ API key)")
            self.pipeline_state['phase_5_completed'] = False

        return {
            'raw_data': extracted_data,
            'simulation_results': mc_results['results'],
            'statistics': mc_results['statistics'],
            'sensitivity': mc_results['sensitivity'],
            'business_narrative': business_narrative,
            'recommendations': decision_results,
            'strategic_analysis': strategic_analysis,
            'execution_summary': self.pipeline_state
        }
