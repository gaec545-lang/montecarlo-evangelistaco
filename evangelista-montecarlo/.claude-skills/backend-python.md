# Backend Python Modification Rules

## WORKFLOW OBLIGATORIO

### STEP 1: READ FIRST
```bash
cat src/nombre_archivo.py
```
Entiende el código actual ANTES de modificar.

### STEP 2: IDENTIFY DEPENDENCIES
Si archivo A llama método de archivo B:
- Verificar que método existe en B
- Si no existe → Crearlo en B PRIMERO

### STEP 3: ADD TYPE HINTS CORRECTLY
```python
from typing import List, Dict, Optional, Any

def method(self, param: str) -> Optional[Dict]:
    pass
```

### STEP 4: VALIDATE IMMEDIATELY
```bash
python -c "from src.module import Class; print('✅')"
```

### STEP 5: COMMIT INCREMENTAL
```bash
git add src/file.py
git commit -m "fix: specific change"
```

## FORBIDDEN
- ❌ NO modificar sin leer primero
- ❌ NO usar List/Dict sin import typing
- ❌ NO llamar método que no existe
- ❌ NO commits masivos (10+ archivos)