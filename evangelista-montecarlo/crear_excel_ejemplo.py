import pandas as pd
from datetime import datetime, timedelta

# Crear datos de ejemplo
fechas = [datetime(2024, i, 15) for i in range(1, 7)]

data = []
# Datos de harina
for fecha in fechas:
    data.append({
        'Fecha': fecha,
        'Insumo': 'Harina',
        'Costo_kg': 18.5 + (fecha.month - 1) * 0.7
    })

# Datos de azúcar
for fecha in fechas:
    data.append({
        'Fecha': fecha,
        'Insumo': 'Azucar',
        'Costo_kg': 23.5 + (fecha.month - 1) * 0.7
    })

df = pd.DataFrame(data)

# Guardar
filepath = 'data/costos_ejemplo.xlsx'
df.to_excel(filepath, index=False, sheet_name='Costos')

print(f"✅ Archivo creado: {filepath}")
print(f"   Filas: {len(df)}")
print(f"\nPrimeras filas:")
print(df.head())