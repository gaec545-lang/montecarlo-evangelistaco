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
        Retorna lista de variables definidas en template
        
        Returns:
            Lista de dicts con info de cada variable
        """
        return self.get('common_variables', [])
    
    def get_business_model(self) -> str:
        """
        Retorna código del modelo de negocio como string
        
        Returns:
            String con código Python del modelo
        """
        return self.get('business_model.template', '')
    
    def get_distribution_config(self, variable_name: str) -> Dict:
        """
        Retorna configuración de distribución para una variable
        
        Busca primero en custom_distributions del cliente,
        luego en default_distributions del template
        
        Args:
            variable_name: Nombre de la variable (ej: 'precio_harina')
            
        Returns:
            Dict con configuración de distribución
            
        Raises:
            ValueError: Si no encuentra configuración
        """
        # 1. Buscar en cliente
        custom = self.get(f'simulation.custom_distributions.{variable_name}')
        if custom:
            return custom
        
        # 2. Buscar en template
        default = self.get(f'default_distributions.{variable_name}')
        if default:
            return default
        
        # 3. No encontrado
        raise ValueError(
            f"❌ No se encontró configuración de distribución para variable: {variable_name}"
        )
    
    def validate(self) -> Tuple[bool, List[str]]:
        """
        Valida que configuración esté completa
        
        Returns:
            (is_valid, [error_messages])
        """
        errors = []
        
        # Validación 1: Industria especificada
        industry = self.get('client.industry')
        if not industry:
            errors.append("Cliente no especifica 'industry'")
        
        # Validación 2: Template tiene estructura mínima
        if not self.get('industry.name'):
            errors.append("Template no tiene 'industry.name'")
        
        if not self.get('common_variables'):
            errors.append("Template no tiene 'common_variables'")
        
        # Validación 3: Parámetros de negocio requeridos
        required_params = self.get('business_model.parameters_required', [])
        for param in required_params:
            if self.get(f'business_parameters.{param}') is None:
                errors.append(
                    f"Parámetro requerido faltante: business_parameters.{param}"
                )
        
        # Validación 4: Cada variable tiene distribución
        variables = self.get_variables()
        for var in variables:
            var_name = var.get('name')
            if var_name:
                try:
                    self.get_distribution_config(var_name)
                except ValueError as e:
                    errors.append(str(e))
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
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