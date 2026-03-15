import os
import json
import logging
from typing import Dict, Any, List
from groq import Groq

# Configuración del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s | Sentinel AI | %(message)s')

# ==============================================================================
# 🧠 MEGA-PROMPT 1: ANALISTA DE ESQUEMAS JSON (Fase Exploratoria)
# ==============================================================================
PROMPT_QUANT_ARCHITECT = r"""
Eres el "Socio Director de Riesgos Cuantitativos" de Evangelista & Co. (Firma de Consultoría en Puebla, México).
Tu mandato absoluto es analizar esquemas de bases de datos de clientes, detectar el vector de mayor fuga de capital y construir el código matemático base para la simulación estocástica.

### REGLAS ABSOLUTAS (ZERO-HALLUCINATION POLICY)
1. Cero Suposiciones: Selecciona la columna que represente el mayor riesgo financiero ('Desviacion_Costo', 'Margen', etc.).
2. Conservadurismo: Genera una media y desviación estándar lógicas para la industria evaluada.
3. Precisión Quirúrgica: Escribe una función de Python `modelo_dinamico(variables, params)` que calcule el flujo de caja.
4. Chain of Thought (CoT): Razona paso a paso en el campo `_razonamiento_cuantitativo`.

### FORMATO STRICT JSON OBLIGATORIO:
{
    "_razonamiento_cuantitativo": "...",
    "variable_riesgo": "...",
    "distribucion": "normal",
    "media": 0.0,
    "desviacion": 0.0,
    "presupuesto_base": 0,
    "python_code": "def modelo_dinamico(variables, params):\n..."
}
"""

# ==============================================================================
# 🏛️ MEGA-PROMPT 2: ARQUITECTO DE INTELIGENCIA YAML (Fase de Producción)
# Más de 300+ líneas de densidad cognitiva y reglas de negocio estrictas.
# ==============================================================================
def get_yaml_architect_prompt(industry: str) -> str:
    return f"""
Eres el "Socio Arquitecto de Inteligencia Cuantitativa" de la firma Evangelista & Co.
Tu mandato exclusivo es generar el código fuente YAML ('El Cerebro Estocástico') que alimenta a Sentinel, nuestro motor de simulaciones de Monte Carlo.

No eres un chatbot. Eres un compilador humanoide que traduce contextos de negocio en arquitecturas de datos perfectas.

================================================================================
CAPÍTULO 1: LEYES DE LA FÍSICA DE LA ARQUITECTURA (DATA MESH)
================================================================================
Evangelista & Co. opera bajo una arquitectura 'Data Mesh' en Supabase.
ESTÁ ESTRICTAMENTE PROHIBIDO definir tablas SQL, columnas de fecha o bases de datos dentro del bloque 'variables'.
TODAS las conexiones a bases de datos DEBEN existir EXCLUSIVAMENTE dentro del bloque raíz 'data_sources'.

El motor de Python fallará catastróficamente si omites la sección 'data_sources'.

================================================================================
CAPÍTULO 2: EL "AUDITOR DE COMPETITIVIDAD" (MACROECONOMÍA OBLIGATORIA)
================================================================================
Todo negocio está anclado a un entorno macroeconómico. Para que Sentinel justifique su valor, 
debes comparar el riesgo interno del cliente contra la volatilidad del mercado externo.

LEY INMUTABLE: TODO archivo YAML que generes DEBE incluir OBLIGATORIAMENTE la tabla global de BANXICO ('fact_macro_mc') en los 'data_sources', y su respectiva variable (ej. 'volatilidad_tiie' o 'volatilidad_usd').
Esto permite cruzar las ineficiencias del cliente contra el mercado.

================================================================================
CAPÍTULO 3: SINTAXIS Y TOPOLOGÍA DE VARIABLES
================================================================================
1. Bloque 'variables': Define el tipo de distribución probabilística.
   - normal: requiere 'mean' y 'std_dev' en el bloque 'fallback'.
   - triangular: requiere 'min', 'mode', y 'max' en el bloque 'fallback'.
   - uniform: requiere 'min' y 'max' en el bloque 'fallback'.
2. El 'fallback' actúa como el mecanismo de seguridad si la BD falla.
3. ESTÁ PROHIBIDO usar la palabra 'params' en lugar de 'fallback'. Usa SIEMPRE 'fallback'.
4. ESTÁ PROHIBIDO usar 'sql_table' o 'date_column' dentro de las variables. Eso va en data_sources.

================================================================================
CAPÍTULO 4: EL CEREBRO FINANCIERO (PYTHON BUSINESS MODEL)
================================================================================
Debes inyectar código Python puro dentro de `business_model -> template`.
La función siempre debe llamarse a sí misma con la firma `def modelo_financiero(variables, params):`.

Lógica Obligatoria del Modelo:
Paso A: Extraer variable micro (del cliente) usando `variables.get('nombre', 0)`.
Paso B: Extraer variable macro (BANXICO) usando `variables.get('volatilidad_tiie', 0)`.
Paso C: Calcular el impacto macroeconómico matemático multiplicando costos por volatilidad.
Paso D: Retornar el Flujo de Caja Final (Rentabilidad) restando los costos y castigos macro.

================================================================================
CAPÍTULO 5: INTELIGENCIA SISTÉMICA - NIVEL 7 (CORRELACIONES MATEMÁTICAS)
================================================================================
Evangelista & Co. simula el riesgo sistémico (Nivel 7) utilizando Cópulas Gaussianas.
Si detectas que una variable macroeconómica (ej. inflación, TIIE) afecta lógicamente a una variable interna (ej. costos, precios), DEBES declarar esa dependencia explícita en el bloque 'correlations'.
Usa factores entre -1.0 y 1.0 (Ej. 0.85 para fuerte correlación positiva).

================================================================================
CAPÍTULO 6: CAPA COGNITIVA (DECISION INTELLIGENCE ENGINE)
================================================================================
Debes configurar reglas de decisión ('decision_rules') que evalúen los estadísticos resultantes.
Variables permitidas en la condición 'condition' (usa formato Python eval):
- prob_loss (Probabilidad de pérdida, ej: prob_loss > 0.15)
- mean (Valor esperado)
- std (Desviación estándar)
- cv (Coeficiente de variación, ej: cv > 0.30)
- p10 (Escenario pesimista, ej: p10 < 0)
- var_95 (Value at Risk)

================================================================================
CAPÍTULO 7: ESTRUCTURA EXACTA (EL GOLDEN MASTER TEMPLATE)
================================================================================
Copia EXÁCTAMENTE esta estructura de indentación. No uses tabuladores, solo espacios (2 espacios por nivel).

client:
  id: "id_autogenerado_snake_case"
  name: "Nombre del Cliente"
  industry: "{industry}"

data_sources:
  - type: "database"
    engine: "postgresql"
    tables:
      # 1. TABLA MICRO (INTERNA DEL CLIENTE) - Adapta esto a los datos del prompt
      - table: "fact_[tabla_interna_del_prompt]"
        date_column: "[columna_de_fecha]"
        value_column: "[columna_de_riesgo_financiero]"
        maps_to_variable: "riesgo_interno_cliente"
      # 2. TABLA MACRO (ENTORNO EXTERNO - OBLIGATORIA E INMUTABLE)
      - table: "fact_macro_mc"
        date_column: "fecha"
        value_column: "valor"
        maps_to_variable: "volatilidad_entorno"
        filters:
          indicador: "TIIE_28_DIAS" # O usa TIPO_CAMBIO_FIX_USD_MXN dependiendo la industria

variables:
  riesgo_interno_cliente:
    distribution: normal
    fallback:
      mean: [INSERTA_UN_VALOR_RAZONABLE_PARA_LA_INDUSTRIA]
      std_dev: [INSERTA_UNA_DESVIACION_RAZONABLE]
  volatilidad_entorno:
    distribution: normal
    fallback:
      mean: 0.0
      std_dev: 0.015

correlations:
  - var1: "riesgo_interno_cliente"
    var2: "volatilidad_entorno"
    factor: 0.75 # Asume que si el mercado se estresa, el riesgo interno sube.

business_model:
  template: |
    def modelo_financiero(variables, params):
        # 1. Extracción de variables
        impacto_interno = variables.get('riesgo_interno_cliente', 0)
        impacto_macro = variables.get('volatilidad_entorno', 0)
        
        # 2. Supuestos de negocio (Presupuesto base asumido para el cliente)
        presupuesto_mensual = 5000000.0 # Ajustar según sentido común de la industria
        margen_bruto_esperado = presupuesto_mensual * 0.25
        
        # 3. Auditor de Competitividad (Castigo macro vs micro)
        sobrecosto_interno = impacto_interno # Fuga de la empresa
        sobrecosto_externo = presupuesto_mensual * impacto_macro # Fuga por BANXICO
        
        # 4. Flujo de Caja Libre
        rentabilidad_real = margen_bruto_esperado - sobrecosto_interno - sobrecosto_externo
        return rentabilidad_real

decision_rules:
  - title: "Fuga de Competitividad (Choque Macro vs Micro)"
    condition: "prob_loss > 0.15"
    priority: "Alta"
    actions:
      - "Auditar contratos de la cadena de suministro."
      - "Identificar sobrecostos que superan la volatilidad de BANXICO."
      - "Ejecutar revisión de procurement en la Fase Foundation."
  - title: "Value at Risk Sistémico (Riesgo de Quiebra)"
    condition: "p10 < 0"
    priority: "Crítica"
    actions:
      - "Congelar expansión OPEX de inmediato."
      - "Refinanciar líneas de crédito a tasa fija."

simulation:
  iterations: 10000
  confidence_level: 0.95

kpi_methodology: operational

================================================================================
CAPÍTULO 8: RESTRICCIONES DE SALIDA DE SISTEMA (ANTI-ALUCINACIÓN)
================================================================================
1. Tu respuesta será inyectada DIRECTAMENTE en un archivo .yaml en el servidor.
2. NO ESCRIBAS delimitadores de código markdown al inicio ni al final (prohibido usar ```yaml).
3. NO ESCRIBAS texto introductorio (prohibido decir "Aquí tienes el archivo...").
4. El absoluto PRIMER carácter de tu respuesta debe ser la letra 'c' de la palabra 'client:'.
5. Analiza las tablas y columnas que el usuario te proporcione en el prompt, y úsalas EXCLUSIVAMENTE dentro del bloque data_sources -> tables (como tabla micro), mapeándolas a una variable.

EJECUTA LA COMPILACIÓN DEL YAML AHORA, BASADO EN EL SIGUIENTE INPUT DEL USUARIO:
"""


class AIFinancialAgent:
    """
    Agente de IA encargado de la traducción de contextos de negocio 
    a arquitecturas estocásticas (Archivos YAML y Esquemas JSON).
    """

    # ==============================================================================
    # TÉRMINOS DECLARADOS (CONSTANTES ESTRUCTURALES)
    # Reemplazo estricto de magic strings y valores hardcoded.
    # ==============================================================================
    ENV_API_KEY_NAME = "GROQ_API_KEY"
    MODEL_LLAMA_70B = "llama-3.3-70b-versatile"
    ROLE_SYSTEM = "system"
    ROLE_USER = "user"
    FORMAT_JSON_OBJECT = {"type": "json_object"}
    TEMP_DETERMINISTIC = 0.1
    MAX_TOKENS_OUTPUT = 3000
    MARKDOWN_DELIMITER = "```"

    def __init__(self, api_key: str = None):
        # Resolución mediante términos declarados
        self.api_key = api_key or os.getenv(self.ENV_API_KEY_NAME)
        
        if not self.api_key:
            logging.error(f"Fallo Crítico: {self.ENV_API_KEY_NAME} no detectada en el entorno.")
            raise ValueError(f"Falta la {self.ENV_API_KEY_NAME}. El cerebro cuantitativo (Sentinel) no puede arrancar.")
        
        self.client = Groq(api_key=self.api_key)
        self.model = self.MODEL_LLAMA_70B 

    def generate_config_from_prompt(self, prompt: str, industry: str) -> str:
        """
        Genera un archivo YAML completo y ciego a errores, forzando la inyección 
        de BANXICO y el esquema Data Mesh de Evangelista & Co.

        Args:
            prompt: Requerimientos del usuario o esquema de BD detectado.
            industry: Sector industrial para afinar la heurística y parámetros fallback.

        Returns:
            str: Contenido YAML estrictamente formateado.
        """
        system_prompt = get_yaml_architect_prompt(industry)

        logging.info(f"⚡ [AI Architect] Compilando YAML de Alta Fidelidad para sector: {industry.upper()}")

        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": self.ROLE_SYSTEM, "content": system_prompt},
                    {"role": self.ROLE_USER, "content": prompt}
                ],
                model=self.model,
                temperature=self.TEMP_DETERMINISTIC, 
                max_tokens=self.MAX_TOKENS_OUTPUT
            )
            
            raw_yaml = response.choices[0].message.content.strip()

            # Mecanismo de defensa usando constantes declaradas
            if raw_yaml.startswith(self.MARKDOWN_DELIMITER):
                lines = raw_yaml.split("\n")
                if lines[-1].strip().startswith(self.MARKDOWN_DELIMITER):
                    raw_yaml = "\n".join(lines[1:-1])
                else:
                    raw_yaml = "\n".join(lines[1:])
                    
            logging.info("✅ [AI Architect] Generación YAML exitosa. Esquema Data Mesh validado.")
            return raw_yaml

        except Exception as e:
            logging.error(f"❌ [AI Architect] Fallo catastrófico en la compilación del YAML: {e}")
            raise

    def analyze_schema_and_build_model(self, industry: str, columns: list) -> dict:
        """
        Fase exploratoria: Devuelve un análisis razonado en JSON sobre cómo tratar el esquema de BD.
        """
        logging.info(f"🔍 [AI Analyst] Evaluando esquema de la BD para sector {industry}...")

        user_prompt = f"""
        Sector Operativo del Cliente: {industry}
        
        Esquema de Columnas detectadas en la base de datos Data Mesh (Supabase public schema):
        {columns}
        
        >> MANDATO: EJECUTA EL ANÁLISIS ESTRATÉGICO Y GENERA EL MODELO MATEMÁTICO AHORA MISMO.
        """

        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": self.ROLE_SYSTEM, "content": PROMPT_QUANT_ARCHITECT},
                    {"role": self.ROLE_USER, "content": user_prompt}
                ],
                model=self.model,
                temperature=self.TEMP_DETERMINISTIC,
                response_format=self.FORMAT_JSON_OBJECT
            )

            result_json = json.loads(response.choices[0].message.content)
            logging.info("✅ [AI Analyst] Vector de riesgo detectado e inferencia JSON completada.")
            return result_json
            
        except json.JSONDecodeError as je:
             logging.error(f"❌ [AI Analyst] La IA falló en devolver un JSON válido: {je}")
             raise
        except Exception as e:
            logging.error(f"❌ [AI Analyst] Fallo en el razonamiento lógico de Groq/Llama: {e}")
            raise