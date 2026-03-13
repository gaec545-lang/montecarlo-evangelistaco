# Database & Secrets Management Rules

## SECRETS VALIDATION FIRST

### ALWAYS CHECK SECRETS EXIST
```bash
cat .streamlit/secrets.toml
```

Required keys:
- DATABASE_URL
- ENCRYPTION_KEY
- GROQ_API_KEY

## CONNECTION MANAGER RULES

### RETURN TYPES EXPLICIT
```python
def save(...) -> bool:
    try:
        # logic
        return True
    except:
        return False

def get(...) -> Optional[Dict]:
    try:
        return {"url": ..., "key": ...}
    except:
        return None
```

### ADD DEBUGGING ALWAYS
```python
print(f"🔍 Saving client: {client_id}")
result = save_api_connection(...)
print(f"✅ Result: {result}")
```

### VALIDATE SAVE WORKED
```python
# After save
test = get_client_connection(client_id)
if not test:
    raise Exception("Save failed!")
```

## FORBIDDEN
- ❌ NO asumir secrets existen
- ❌ NO silent failures (siempre print/log)
- ❌ NO modificar sin agregar debug