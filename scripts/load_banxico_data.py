"""
Script de carga de datos BANXICO - VERSIÓN CORREGIDA
Códigos de series actualizados a 2026
"""

import os
import sys
from datetime import datetime, timedelta
import logging

# Agregar path al proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from supabase import create_client
import requests

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# ============================================================
# CONFIGURACIÓN DE SERIES BANXICO (CÓDIGOS CORRECTOS 2026)
# ============================================================

SERIES_BANXICO = {
    'TIIE': {
        'codigo': 'SF43878',  # TIIE 28 días (CORREGIDO)
        'nombre': 'TIIE 28 días',
        'descripcion': 'Tasa de Interés Interbancaria de Equilibrio a 28 días'
    },
    'USD_MXN': {
        'codigo': 'SF43718',  # Tipo de cambio FIX (CORREGIDO)
        'nombre': 'Tipo de Cambio FIX',
        'descripcion': 'Tipo de cambio para solventar obligaciones en dólares'
    },
    'CETES_28': {
        'codigo': 'SF43936',  # CETES 28 días
        'nombre': 'CETES 28 días',
        'descripcion': 'Tasa de rendimiento de CETES a 28 días'
    },
    'INPC': {
        'codigo': 'SP1',  # INPC General (CORREGIDO - serie más simple)
        'nombre': 'INPC General',
        'descripcion': 'Índice Nacional de Precios al Consumidor'
    }
}

# URL base de la API de BANXICO
BANXICO_API_BASE = "https://www.banxico.org.mx/SieAPIRest/service/v1/series"

def get_banxico_token():
    """Obtiene token de BANXICO desde secrets."""
    try:
        return st.secrets.get("BANXICO_TOKEN")
    except:
        return os.getenv("BANXICO_TOKEN")

def get_supabase_client():
    """Crea cliente de Supabase."""
    try:
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY")
    except:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError("Faltan SUPABASE_URL o SUPABASE_KEY en secrets.toml")
    
    return create_client(url, key)

def fetch_banxico_data(serie_codigo: str, fecha_inicio: str, fecha_fin: str, token: str):
    """
    Descarga datos de BANXICO.
    
    API Endpoint:
    https://www.banxico.org.mx/SieAPIRest/service/v1/series/{serie}/datos/{fecha_inicio}/{fecha_fin}
    
    Formato fecha: YYYY-MM-DD
    """
    url = f"{BANXICO_API_BASE}/{serie_codigo}/datos/{fecha_inicio}/{fecha_fin}"
    
    headers = {
        'Bmx-Token': token,
        'Accept': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extraer serie de datos
            series = data.get('bmx', {}).get('series', [])
            if not series:
                return None
            
            # Primera serie (debería ser la única)
            serie_data = series[0].get('datos', [])
            
            return serie_data
        
        elif response.status_code == 404:
            logging.warning(f"   ⚠️  Serie {serie_codigo}: No encontrada (404)")
            return None
        
        elif response.status_code == 401:
            logging.error(f"   ❌ Serie {serie_codigo}: Token inválido (401)")
            return None
        
        else:
            logging.error(f"   ❌ Serie {serie_codigo}: HTTP {response.status_code}")
            return None
    
    except requests.exceptions.Timeout:
        logging.error(f"   ❌ Serie {serie_codigo}: Timeout")
        return None
    
    except Exception as e:
        logging.error(f"   ❌ Serie {serie_codigo}: Error {str(e)}")
        return None

def insert_to_supabase(supabase, variable: str, datos: list, fuente: str = "BANXICO"):
    """
    Inserta datos en Supabase.
    
    Args:
        supabase: Cliente de Supabase
        variable: Nombre de la variable (ej: 'TIIE', 'USD_MXN')
        datos: Lista de dicts con formato BANXICO: [{'fecha': 'DD/MM/YYYY', 'dato': 'X.XX'}]
        fuente: Fuente de datos (default: 'BANXICO')
    """
    registros_insertados = 0
    
    for punto in datos:
        try:
            # Parsear fecha (formato BANXICO: DD/MM/YYYY)
            fecha_str = punto.get('fecha')
            valor_str = punto.get('dato')
            
            if not fecha_str or not valor_str:
                continue
            
            # Convertir fecha DD/MM/YYYY → YYYY-MM-DD
            dia, mes, anio = fecha_str.split('/')
            fecha_iso = f"{anio}-{mes}-{dia}"
            
            # Convertir valor (puede venir como string)
            try:
                valor = float(valor_str.replace(',', ''))
            except:
                continue
            
            # Insertar en Supabase (upsert para evitar duplicados)
            supabase.table('saas_variables_exogenas').upsert({
                'variable': variable,
                'fecha': fecha_iso,
                'valor': valor,
                'fuente': fuente
            }, on_conflict='variable,fecha').execute()
            
            registros_insertados += 1
        
        except Exception as e:
            logging.debug(f"      Error en registro: {e}")
            continue
    
    return registros_insertados

def main():
    """Pipeline principal de carga."""
    
    # 1. Obtener credenciales
    token = get_banxico_token()
    if not token:
        logging.error("❌ BANXICO_TOKEN no encontrado en secrets.toml")
        sys.exit(1)
    
    # 2. Conectar a Supabase
    try:
        supabase = get_supabase_client()
        logging.info("✅ Conectado a Supabase")
    except Exception as e:
        logging.error(f"❌ Error conectando a Supabase: {e}")
        sys.exit(1)
    
    # 3. Definir rango de fechas (últimos 24 meses)
    fecha_fin = datetime.now()
    fecha_inicio = fecha_fin - timedelta(days=730)  # ~24 meses
    
    fecha_inicio_str = fecha_inicio.strftime('%Y-%m-%d')
    fecha_fin_str = fecha_fin.strftime('%Y-%m-%d')
    
    logging.info(f"Descargando 24 meses: {fecha_inicio_str} → {fecha_fin_str}")
    
    # 4. Descargar cada serie
    total_registros = 0
    
    for variable, config in SERIES_BANXICO.items():
        logging.info(f"  📡 Descargando {variable} (serie {config['codigo']})...")
        
        datos = fetch_banxico_data(
            serie_codigo=config['codigo'],
            fecha_inicio=fecha_inicio_str,
            fecha_fin=fecha_fin_str,
            token=token
        )
        
        if datos:
            registros = insert_to_supabase(supabase, variable, datos)
            logging.info(f"     ✅ {variable}: {registros} registros insertados")
            total_registros += registros
        else:
            logging.warning(f"     ⚠️  {variable}: Sin datos (verificar código de serie)")
    
    # 5. Resumen
    logging.info("")
    logging.info("=" * 50)
    logging.info(f"Carga completada: {total_registros} registros nuevos en saas_variables_exogenas")
    
    if total_registros == 0:
        logging.warning("\n⚠️  ADVERTENCIA: No se insertaron registros.")
        logging.warning("Posibles causas:")
        logging.warning("1. Token BANXICO inválido o expirado")
        logging.warning("2. Códigos de series incorrectos")
        logging.warning("3. API de BANXICO temporalmente no disponible")
        logging.info("\n💡 Ejecuta: python scripts/load_mock_data.py (para usar datos de prueba)")

if __name__ == "__main__":
    main()