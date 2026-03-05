import time
from src.configuration_manager import ConfigurationManager
from src.data_extraction_engine import DataExtractionEngine
from src.monte_carlo_engine import UniversalMonteCarloEngine
from src.business_translator import BusinessTranslator
from src.decision_intelligence_engine import DecisionIntelligenceEngine

class PipelineExecutionError(Exception):
    pass

class DecisionPipeline:
    """Pipeline maestro para Decision Intelligence"""
    
    def __init__(self, config: ConfigurationManager, supabase_credentials: dict = None):
        self.config = config
        self.supabase_creds = supabase_credentials
        
        self.data_engine = DataExtractionEngine(self.supabase_creds, self.config) if self.supabase_creds else None
        self.mc_engine = UniversalMonteCarloEngine(self.config)
        self.decision_engine = DecisionIntelligenceEngine(self.config)
        
        self.pipeline_state = {
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

    def execute(self) -> dict:
        # FASE 1
        extracted_data = {}
        if self.data_engine:
            extracted_data = self.run_phase(1, "Data Extraction Engine", 
                lambda: (self.data_engine.connect(), self.data_engine.extract_all_variables())[1])
        
        # FASE 2
        def run_mc():
            self.mc_engine.load_historical_data(extracted_data if extracted_data else None)
            self.mc_engine.setup_simulation()
            return {
                'results': self.mc_engine.run(),
                'statistics': self.mc_engine.get_statistics(),
                'sensitivity': self.mc_engine.sensitivity_analysis()
            }
        mc_results = self.run_phase(2, "Monte Carlo Simulation Engine", run_mc)
        
        # FASE 3
        business_narrative = self.run_phase(3, "Business Translator", 
            lambda: BusinessTranslator(self.config, extracted_data).translate(mc_results['statistics'], mc_results['sensitivity']))
        
        # FASE 4
        decision_results = self.run_phase(4, "Decision Intelligence Engine",
            lambda: self.decision_engine.generate_recommendations(mc_results['statistics'], mc_results['sensitivity']))
            
        return {
            'raw_data': extracted_data,
            'simulation_results': mc_results['results'],
            'statistics': mc_results['statistics'],
            'sensitivity': mc_results['sensitivity'],
            'business_narrative': business_narrative,
            'recommendations': decision_results,
            'execution_summary': self.pipeline_state
        }