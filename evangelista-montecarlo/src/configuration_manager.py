"""
Configuration Manager para Evangelista Monte Carlo System
Autor: Evangelista & Co.
Versión: 1.0
"""

import yaml
import os
from typing import Dict, List, Tuple, Any, Optional


class ConfigurationManager:
    """
    Gestor de configuración con herencia de templates
    
    Carga archivos YAML de template (industria) y cliente,
    hace merge y proporciona acceso fácil a parámetros.
    """
    
    def __init__(self, template: str, client_config: str):
        """
        Inicializa el gestor de configuración
        
        Args:
            template: Ruta a archivo YAML de template (ej: 'templates/alimentos.yaml')
            client_config: Ruta a archivo YAML de configuración cliente
        """
        self.template_path = template
        self.client_config_path = client_config
        
        # Cargar archivos
        self.template = self._load_yaml(template)
        self.client = self._load_yaml(client_config)
        
        # Merge (cliente override template)
        self.config = self._merge_configs(self.template, self.client)
    
    def _load_yaml(self, filepath: str) -> dict:
        """
        Carga archivo YAML
        
        Args:
            filepath: Ruta al archivo
            
        Returns:
            Dict con contenido del YAML
            
        Raises:
            FileNotFoundError: Si archivo no existe
            yaml.YAMLError: Si YAML tiene errores de sintaxis
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"❌ Archivo no encontrado: {filepath}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
                if content is None:
                    raise ValueError(f"❌ Archivo YAML vacío: {filepath}")
                return content
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"❌ Error al parsear YAML en {filepath}: {e}")
    
    def _merge_configs(self, template: dict, client: dict) -> dict:
        """
        Merge recursivo: cliente override template
        
        Args:
            template: Dict del template
            client: Dict del cliente
            
        Returns:
            Dict merged
            
        Ejemplo:
            Template: {'a': 1, 'b': {'c': 2}}
            Client:   {'b': {'c': 3, 'd': 4}}
            Result:   {'a': 1, 'b': {'c': 3, 'd': 4}}
        """
        result = template.copy()
        
        for key, value in client.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Merge recursivo para dicts
                result[key] = self._merge_configs(result[key], value)
            else:
                # Override directo
                result[key] = value
        
        return result
    
    def get(self, path: str, default=None) -> Any:
        """
        Accede a configuración usando dot notation
        
        Args:
            path: Ruta con puntos (ej: 'business_parameters.precio_venta_unitario')
            default: Valor por defecto si no existe
        
        Returns:
            Valor encontrado o default
        
        Ejemplos:
            config.get('business_parameters.precio_venta_unitario')
            # >>> 45
            
            config.get('business_parameters.receta.harina')
            # >>> 0.5
        """
        keys = path.split('.')
        value = self.config
        
        try:
            for key in keys:
                if isinstance(value, dict):
                    value = value[key]
                else:
                    return default
            return value
        except (KeyError, TypeError):
            return default
    
    def get_variables(self) -> List[Dict]:
        """
        Retorna lista de variables adaptándose al nuevo YAML Builder.
        """
        # El YAML Builder nuevo guarda las variables como un diccionario.
        vars_dict = self.get('variables')
        if isinstance(vars_dict, dict):
            # Convierte el diccionario en la lista exacta que espera el motor
            return [{"name": k, **v} for k, v in vars_dict.items()]
            
        # Fallback por si hay archivos muy antiguos
        return self.get('common_variables', [])
    
    def get_business_model(self) -> str:
        """
        Retorna código del modelo de negocio soportando el nuevo formato dinámico.
        """
        bm = self.get('business_model')
        
        # Si viene del nuevo YAML Builder (String puro)
        if isinstance(bm, str):
            return bm
            
        # Si viene del modelo antiguo (Diccionario con llave 'template')
        if isinstance(bm, dict):
            return bm.get('template', '')
            
        return ''
    
    def get_distribution_config(self, variable_name: str) -> Dict:
        """
        Retorna configuración de distribución adaptando las llaves nuevas al motor viejo.
        """
        # 1. Buscar en el nuevo formato dinámico (YAML Builder)
        var_config = self.get(f'variables.{variable_name}')
        if var_config:
            # Traducimos las llaves para que el motor antiguo las entienda
            return {
                "type": var_config.get("distribution", "normal"),
                "fallback": var_config.get("params", {})
            }
            
        # 2. Buscar en configuraciones legacy
        custom = self.get(f'simulation.custom_distributions.{variable_name}')
        if custom:
            return custom
        
        default = self.get(f'default_distributions.{variable_name}')
        if default:
            return default
        
        raise ValueError(
            f"❌ No se encontró configuración de distribución para variable: {variable_name}"
        )
    
    def validate(self) -> tuple[bool, list[str]]:
        """
        Validador Universal Agnostico: 
        Solo exige la estructura maestra, no le importa la industria.
        """
        errors = []
        
        # 1. Validaciones estructurales mínimas
        if not self.get('client.id'):
            errors.append("Falta identificador del cliente (client.id)")
            
        if not self.get('simulation.iterations'):
            errors.append("Falta número de iteraciones (simulation.iterations)")
            
        if not self.get('variables'):
            errors.append("No hay variables de riesgo definidas en el modelo.")

        # 2. Eliminamos las restricciones "legacy" de la pastelería.
        # Ya no exigimos 'precio_venta_unitario' ni 'receta'. 
        # El modelo de negocio ahora se dicta por la función matemática dinámica.
        
        return len(errors) == 0, errors
    
    def to_dict(self) -> dict:
        """
        Retorna configuración completa (merged) como dict
        
        Returns:
            Dict con configuración completa
        """
        return self.config
    
    def __repr__(self) -> str:
        """Representación string del objeto"""
        client_name = self.get('client.name', 'Sin nombre')
        industry = self.get('client.industry', 'Sin industria')
        return f"<ConfigurationManager: {client_name} ({industry})>"
