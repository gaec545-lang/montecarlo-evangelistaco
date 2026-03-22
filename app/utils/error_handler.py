"""
Manejo de errores amigable para Sentinel.
Convierte excepciones técnicas en mensajes ejecutivos.
Evangelista & Co. — nunca exponer stack traces de BD al usuario final.
"""

import streamlit as st
from typing import Callable, Any, Tuple


def safe_db_operation(
    operation: Callable,
    success_message: str,
    error_code: str = "DB-ERR",
    context: str = "",
) -> Tuple[bool, Any]:
    """
    Envuelve una operación de BD en try/except con mensajes amigables.

    Args:
        operation: Callable sin argumentos (usar lambda si es necesario)
        success_message: Mensaje a mostrar al usuario si tiene éxito
        error_code: Código de error corto para soporte técnico (ej: "CLI-001")
        context: Contexto interno para logging en session_state

    Returns:
        (success: bool, result: Any)
    """
    try:
        result = operation()
        st.success(success_message)
        return True, result

    except Exception as e:
        error_type = type(e).__name__

        # Guardar detalle técnico en session_state (no visible en UI por defecto)
        st.session_state[f"_last_error_{error_code}"] = {
            "type": error_type,
            "message": str(e),
            "context": context,
        }

        # Mensaje amigable para todos los roles
        st.error(
            f"⚠️ No fue posible completar la operación.  \n"
            f"Código de referencia: **{error_code}**  \n"
            f"Si el problema persiste, contacta al administrador técnico."
        )

        # Detalle técnico solo para Admin
        if st.session_state.get("role") == "Admin":
            with st.expander("🔧 Detalles técnicos (solo visible para Admin)"):
                st.code(f"{error_type}: {str(e)}", language="python")

        return False, None


def show_db_error(exc: Exception, error_code: str = "DB-ERR") -> None:
    """
    Muestra un error de BD de forma amigable.
    Reemplaza el patrón: except Exception as e: st.error(f"Error: {e}")

    Args:
        exc: La excepción capturada
        error_code: Código de referencia para soporte técnico
    """
    error_type = type(exc).__name__

    # Guardar en session_state para debugging
    st.session_state[f"_last_error_{error_code}"] = {
        "type": error_type,
        "message": str(exc),
    }

    # Mensaje amigable
    st.error(
        f"⚠️ Operación no completada. Código: **{error_code}**  \n"
        f"Si el problema persiste, contacta al administrador técnico."
    )

    # Detalle solo para Admin
    if st.session_state.get("role") == "Admin":
        with st.expander("🔧 Detalles técnicos (solo Admin)"):
            st.code(f"{error_type}: {str(exc)}", language="python")
