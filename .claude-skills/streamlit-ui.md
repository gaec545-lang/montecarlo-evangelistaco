# Streamlit UI Modification Rules

## TAB STRUCTURE - CRITICAL

### ALWAYS VERIFY TAB COUNT
```python
# Si hay 3 tabs, DEBE haber 3 variables:
tab1, tab2, tab3 = st.tabs(["A", "B", "C"])

# Y 3 bloques with:
with tab1:
    pass
with tab2:
    pass
with tab3:
    pass
```

## DEBUGGING PATTERN
```python
with tab3:
    st.write("🔍 Tab 3 loaded")
    try:
        # código real
    except Exception as e:
        st.error(f"ERROR: {e}")
```

## VALIDATION
```bash
streamlit run app/pages/3_⚙️_Admin_Panel.py
```
Verificar manualmente que TODOS los tabs se vean.

## FORBIDDEN
- ❌ NO borrar bloques `with tab3:`
- ❌ NO commitear sin probar en Streamlit
- ❌ NO asumir session_state keys existen