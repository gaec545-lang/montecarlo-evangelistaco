import os
import json
from groq import Groq
import logging

# ==============================================================================
# MEGA-PROMPT (ARQUITECTURA DE ALTA DENSIDAD COGNITIVA PARA FINANZAS)
# MODELO: Llama-3.3-70b-versatile (Temperatura: 0.1 - Rigor Matemático)
# ==============================================================================

PROMPT_QUANT_ARCHITECT = r"""
Eres el "Socio Director de Riesgos Cuantitativos" de Evangelista & Co. Tu mandato absoluto es analizar esquemas de bases de datos de clientes, detectar el vector de mayor fuga de capital y construir el código matemático para nuestra simulación de riesgo Monte Carlo.

No eres un asistente virtual. Eres un auditor financiero y desarrollador de algoritmos.

### REGLAS ABSOLUTAS DE EXTRACCIÓN Y LÓGICA (ZERO-HALLUCINATION POLICY)
1. Cero Suposiciones: Selecciona la columna que represente el mayor riesgo financiero (ej. 'Desviacion_Costo_Pct', 'Margen_Real', 'Dias_Retraso'). Si no hay una evidente, elige la que afecte el flujo de caja.
2. Conservadurismo Financiero: Genera una media y desviación estándar iniciales lógicas para la industria del cliente.
3. Precisión Quirúrgica (Python): Escribe una función de Python puro llamada `modelo_dinamico(variables, params)`. Esta función debe extraer el riesgo de `variables`, multiplicarlo o aplicarlo contra el `presupuesto_base` de `params`, y retornar el IMPACTO FINANCIERO en valor monetario (float).
4. Chain of Thought (CoT): Antes de escupir los parámetros, DEBES razonar tu análisis paso a paso en el campo `_razonamiento_cuantitativo`.

### FORMATO DE SALIDA DE EJECUCIÓN (JSON STRICT SCHEMA)
Tu respuesta debe ser EXCLUSIVAMENTE un objeto JSON válido. Sin delimitadores Markdown (```json), sin saludos, sin texto adicional. Cualquier desviación de este formato colapsará la simulación.

Estructura obligatoria:
{
    "_razonamiento_cuantitativo": "<Tu análisis paso a paso: Por qué elegiste esa columna específica, cómo calculaste los parámetros estadísticos y la lógica matemática detrás de la función de Python.>",
    "variable_riesgo": "<nombre_exacto_de_la_columna_de_la_lista>",
    "distribucion": "normal",
    "media": -10.0,
    "desviacion": 5.0,
    "presupuesto_base": 10000000,
    "python_code": "def modelo_dinamico(variables, params):\n    riesgo = variables.get('TU_VARIABLE', 0)\n    presupuesto = params.get('presupuesto_base', 0)\n    # Logica de impacto\n    return presupuesto * (riesgo / 100.0)"
}
"""

class AIFinancialAgent:
    def __init__(self, api_key: str = None):
        # Tomamos la llave directamente del parámetro o del secreto de entorno
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Falta la GROQ_API_KEY. El cerebro cuantitativo no puede iniciar.")
        
        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile" # El mismo motor potente de tu web

    def analyze_schema_and_build_model(self, industry: str, columns: list) -> dict:
        logging.info(f"AI Agent analizando esquema para sector {industry}...")

        user_prompt = f"""
        Sector del Cliente: {industry}
        Columnas detectadas en la base de datos (Supabase):
        {columns}
        
        >> EJECUTA EL ANÁLISIS ESTRATÉGICO Y GENERA EL MODELO AHORA:
        """

        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": PROMPT_QUANT_ARCHITECT},
                    {"role": "user", "content": user_prompt}
                ],
                model=self.model,
                temperature=0.1, # Temperatura baja para código determinista
                response_format={"type": "json_object"}
            )

            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logging.error(f"Fallo en el razonamiento de Groq/Llama: {e}")
            raise
