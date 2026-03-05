import pandas as pd
import os
from typing import List, Optional, Dict


class ExcelConnector:
    """
    Lector de archivos Excel con limpieza automática
    
    Ejemplo:
        connector = ExcelConnector('data/costos_ejemplo.xlsx')
        sheets = connector.list_sheets()
        df = connector.read_sheet('Costos')
    """
    
    def __init__(self, file_path: str):
        """
        Inicializa conector
        
        Args:
            file_path: Ruta al archivo Excel
            
        Raises:
            FileNotFoundError: Si archivo no existe
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"❌ Archivo no encontrado: {file_path}")
        
        if not file_path.endswith(('.xlsx', '.xls')):
            raise ValueError(f"❌ Archivo debe ser .xlsx o .xls: {file_path}")
        
        self.file_path = file_path
        self.excel_file = pd.ExcelFile(file_path)
    
    def list_sheets(self) -> List[str]:
        """
        Lista todas las hojas del Excel
        
        Returns:
            Lista con nombres de hojas
        """
        return self.excel_file.sheet_names
    
    def read_sheet(self,
                   sheet_name: str,
                   skip_rows: int = 0,
                   header_row: int = 0) -> pd.DataFrame:
        """
        Lee una hoja específica
        
        Args:
            sheet_name: Nombre de la hoja
            skip_rows: Filas a saltear al inicio
            header_row: Fila donde están los headers (después de skip_rows)
            
        Returns:
            DataFrame limpio
        """
        if sheet_name not in self.list_sheets():
            available = ', '.join(self.list_sheets())
            raise ValueError(
                f"❌ Hoja '{sheet_name}' no existe. "
                f"Disponibles: {available}"
            )
        
        # Leer hoja
        df = pd.read_excel(
            self.file_path,
            sheet_name=sheet_name,
            skiprows=skip_rows,
            header=header_row
        )
        
        # Limpiar
        df = self.clean_dataframe(df)
        
        return df
    
    def read_all_sheets(self) -> Dict[str, pd.DataFrame]:
        """
        Lee todas las hojas
        
        Returns:
            Dict: {'nombre_hoja': DataFrame}
        """
        result = {}
        for sheet_name in self.list_sheets():
            result[sheet_name] = self.read_sheet(sheet_name)
        
        return result
    
    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpia DataFrame de problemas comunes
        
        Limpieza:
        - Elimina filas completamente vacías
        - Elimina columnas sin nombre o vacías
        - Strip espacios en strings
        - Convierte fechas
        
        Args:
            df: DataFrame a limpiar
            
        Returns:
            DataFrame limpio
        """
        # Hacer copia para no modificar original
        df = df.copy()
        
        # 1. Eliminar filas completamente vacías
        df = df.dropna(how='all')
        
        # 2. Eliminar columnas sin nombre
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        
        # 3. Eliminar columnas completamente vacías
        df = df.dropna(axis=1, how='all')
        
        # 4. Strip espacios en strings
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.strip()
        
        # 5. Convertir columnas de fecha
        for col in df.columns:
            if 'fecha' in col.lower() or 'date' in col.lower():
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                except:
                    pass
        
        # 6. Reset index
        df = df.reset_index(drop=True)
        
        return df
    
    def get_column_info(self, sheet_name: str) -> pd.DataFrame:
        """
        Obtiene información sobre columnas de una hoja
        
        Args:
            sheet_name: Nombre de la hoja
            
        Returns:
            DataFrame con info: columna, tipo, valores_nulos
        """
        df = self.read_sheet(sheet_name)
        
        info = []
        for col in df.columns:
            info.append({
                'columna': col,
                'tipo': str(df[col].dtype),
                'valores_nulos': df[col].isna().sum(),
                'valores_unicos': df[col].nunique()
            })
        
        return pd.DataFrame(info)
    
    def __repr__(self) -> str:
        """Representación string"""
        sheets = ', '.join(self.list_sheets())
        return f"<ExcelConnector: {os.path.basename(self.file_path)} | Hojas: {sheets}>"