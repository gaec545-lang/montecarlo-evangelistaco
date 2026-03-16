# ==============================================================================
# INYECCIÓN DE ENRUTAMIENTO
# ==============================================================================
import sys
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '../..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import re
import json
import base64
import hashlib
import bcrypt
import streamlit as st
import pandas as pd
from typing import Optional, Tuple
from supabase import create_client, Client

# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA
# ==============================================================================
st.set_page_config(page_title="Sentinel | Admin", page_icon="⚙️", layout="wide")

st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none !important;}
        .stButton>button { border: 1px solid #D4AF37; background-color: transparent; }
        .stButton>button:hover { border: 1px solid #1A1A2E; color: #1A1A2E; }
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] label, [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] strong { color: #FFFFFF !important; }
        div[data-baseweb="base-input"], div[data-baseweb="select"] > div {
            background-color: #FFFFFF !important; border: 1px solid #D4AF37 !important; border-radius: 4px;
        }
        div[data-baseweb="base-input"] input, div[data-baseweb="select"] div {
            color: #1A1A2E !important; -webkit-text-fill-color: #1A1A2E !important;
        }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. BARRERA DE SEGURIDAD
# ==============================================================================
if not st.session_state.get('authenticated', False) or st.session_state.get('role') not in ["Consultor", "Admin"]:
    st.warning("⚠️ Acceso denegado. Área exclusiva para la Dirección y Consultores Estratégicos.")
    st.page_link("streamlit_app.py", label="⬅️ Volver al Portal de Acceso", icon="🚪")
    st.stop()

with st.sidebar:
    st.image("assets/logoEvangelistaCo.png", width=180)
    st.markdown("<h3 style='text-align: center; color: #D4AF37;'>Sentinel</h3>", unsafe_allow_html=True)
    st.markdown("---")
    st.info(f"**Usuario:** {st.session_state.get('username')}\n**Rol:** 🔬 {st.session_state.get('role')}")
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.role = None
        st.switch_page("streamlit_app.py")
    st.markdown("---")
    st.page_link("streamlit_app.py", label="⬅️ Volver al Dashboard", icon="📊")
    st.markdown("---")
    st.caption("© 2026 Evangelista & Co.")

# ==============================================================================
# 3. SUPABASE CLIENT
# ==============================================================================
_url = os.getenv("SUPABASE_URL") or (st.secrets.get("SUPABASE_URL") if hasattr(st, "secrets") else None)
_key = os.getenv("SUPABASE_KEY") or (st.secrets.get("SUPABASE_KEY") if hasattr(st, "secrets") else None)

@st.cache_resource
def init_supabase(url: str, key: str) -> Optional[Client]:
    if not url or not key:
        return None
    try:
        return create_client(url, key)
    except Exception:
        return None

supabase = init_supabase(_url, _key)

st.title("⚙️ Panel de Control Institucional")
st.markdown("*Evangelista & Co. | Infraestructura de Decision Intelligence*")
st.markdown("---")

if not supabase:
    st.error("⛔ ALERTA ESTRUCTURAL: Faltan credenciales de Supabase.")
    st.info("💡 Ve a Streamlit Cloud > Settings > Secrets y añade SUPABASE_URL y SUPABASE_KEY.")
    st.stop()

# ==============================================================================
# 4. UTILIDADES DE ENCRIPTACIÓN (Fernet — AES-128-CBC + HMAC-SHA256)
# ==============================================================================
def _get_fernet():
    """Obtiene instancia Fernet con clave derivada de secrets."""
    try:
        from cryptography.fernet import Fernet
        raw = (
            os.getenv("ENCRYPTION_KEY")
            or (st.secrets.get("ENCRYPTION_KEY") if hasattr(st, "secrets") else None)
            or (_key or "sentinel-evangelista-fallback-2026")
        )
        key_bytes = hashlib.sha256(raw.encode()).digest()         # 32 bytes
        fernet_key = base64.urlsafe_b64encode(key_bytes)         # Fernet espera base64
        return Fernet(fernet_key)
    except ImportError:
        return None


def encrypt_value(plaintext: str) -> str:
    """Encripta un string. Devuelve string encriptado o el original si falla."""
    if not plaintext:
        return ""
    f = _get_fernet()
    if f is None:
        return plaintext
    return f.encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    """Desencripta un string. Devuelve string plano o el original si falla."""
    if not ciphertext:
        return ""
    f = _get_fernet()
    if f is None:
        return ciphertext
    try:
        return f.decrypt(ciphertext.encode()).decode()
    except Exception:
        return ciphertext   # Almacenado sin encriptar (compatibilidad)

# ==============================================================================
# 5. UTILIDADES DE VALIDACIÓN
# ==============================================================================
def validar_url(url: str) -> bool:
    return bool(re.match(r'^https?://.+\..+', url.strip()))


def validar_headers_json(headers_str: str) -> Tuple[bool, str]:
    if not headers_str.strip():
        return True, ""
    try:
        parsed = json.loads(headers_str)
        if not isinstance(parsed, dict):
            return False, "Los headers deben ser un objeto JSON (clave: valor)."
        return True, ""
    except json.JSONDecodeError as e:
        return False, f"JSON inválido: {e}"

# ==============================================================================
# 6. TEST DE CONEXIÓN
# ==============================================================================
def probar_conexion_api(
    endpoint: str,
    auth_method: str,
    token: str,
    headers_str: str
) -> Tuple[bool, str]:
    """
    Realiza un GET al endpoint con la autenticación indicada.

    Returns:
        (success, mensaje)
    """
    try:
        import requests as _req
        headers: dict = {}

        # Parsear headers adicionales
        if headers_str.strip():
            try:
                headers = json.loads(headers_str)
            except Exception:
                return False, "❌ Error: headers JSON inválido."

        # Inyectar credenciales
        if auth_method == "bearer":
            headers["Authorization"] = f"Bearer {token}"
        elif auth_method == "api_key":
            headers["X-API-Key"] = token
        elif auth_method == "basic_auth":
            encoded = base64.b64encode(token.encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"
        elif auth_method == "oauth2":
            headers["Authorization"] = f"Bearer {token}"

        resp = _req.get(endpoint, headers=headers, timeout=10)
        if resp.status_code < 400:
            return True, f"✅ Conexión exitosa (HTTP {resp.status_code})"
        return False, f"❌ Error HTTP {resp.status_code}: {resp.text[:120]}"

    except ImportError:
        return False, "❌ Falta el paquete 'requests'. Añádelo a requirements.txt."
    except Exception as e:
        return False, f"❌ {type(e).__name__}: {str(e)[:200]}"


DB_PORTS = {
    "postgresql": 5432,
    "mysql": 3306,
    "sqlserver": 1433,
    "oracle": 1521,
    "sqlite": 0,
}

DB_DRIVERS = {
    "postgresql": "postgresql+psycopg2",
    "mysql":      "mysql+pymysql",
    "sqlserver":  "mssql+pyodbc",
    "oracle":     "oracle+cx_oracle",
    "sqlite":     "sqlite",
}


def probar_conexion_sql(
    db_type: str,
    host: str,
    port: int,
    usuario: str,
    password: str,
    nombre: str,
    esquema: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Ejecuta SELECT 1 contra la base de datos especificada.

    Returns:
        (success, mensaje)
    """
    try:
        from sqlalchemy import create_engine, text as sa_text

        if db_type == "sqlite":
            conn_str = f"sqlite:///{nombre}"
        elif db_type == "postgresql":
            conn_str = f"postgresql+psycopg2://{usuario}:{password}@{host}:{port}/{nombre}"
        elif db_type == "mysql":
            conn_str = f"mysql+pymysql://{usuario}:{password}@{host}:{port}/{nombre}"
        elif db_type == "sqlserver":
            conn_str = (
                f"mssql+pyodbc://{usuario}:{password}@{host}:{port}/{nombre}"
                "?driver=ODBC+Driver+17+for+SQL+Server"
            )
        elif db_type == "oracle":
            conn_str = f"oracle+cx_oracle://{usuario}:{password}@{host}:{port}/{nombre}"
        else:
            return False, f"❌ Tipo de BD no soportado: {db_type}"

        engine = create_engine(conn_str, pool_pre_ping=True, connect_args={"connect_timeout": 10})
        with engine.connect() as conn:
            if esquema and db_type == "postgresql":
                conn.execute(sa_text(f"SET search_path TO {esquema}"))
            result = conn.execute(sa_text("SELECT 1")).fetchone()
            if result and result[0] == 1:
                return True, "✅ Conexión SQL exitosa"
        return False, "❌ Query de prueba no retornó resultado esperado."

    except ImportError as e:
        pkg = str(e).split("'")[1] if "'" in str(e) else str(e)
        return False, f"❌ Driver no instalado: {pkg}. Añádelo a requirements.txt."
    except Exception as e:
        return False, f"❌ {type(e).__name__}: {str(e)[:300]}"

# ==============================================================================
# 7. CARGA DE DATOS
# ==============================================================================
# ==============================================================================
# HELPERS DE GESTIÓN DE USUARIOS
# ==============================================================================

ROLE_MAP_CONS = {
    "Consultor Estratégico": "Consultor",
    "Admin":                 "Admin",
    "Partner":               "Consultor",
}


def _hash_password(plaintext: str) -> str:
    """Hashea la contraseña con bcrypt (12 rounds). Retorna string UTF-8."""
    return bcrypt.hashpw(plaintext.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def _username_exists(username: str) -> bool:
    """Retorna True si el username ya existe en saas_users."""
    try:
        res = supabase.table("saas_users").select("id").eq("username", username).execute()
        return bool(res.data)
    except Exception:
        return False


def _email_exists(email: str) -> bool:
    """Retorna True si el email ya existe en saas_users."""
    try:
        res = supabase.table("saas_users").select("id").eq("email", email).execute()
        return bool(res.data)
    except Exception:
        return False


def _validate_credentials(username: str, password: str, confirm: str) -> list[str]:
    """Retorna lista de errores de validación de credenciales (vacía = OK)."""
    errors: list[str] = []
    if not username.strip():
        errors.append("El nombre de usuario es obligatorio.")
    elif len(username.strip()) < 3:
        errors.append("El usuario debe tener al menos 3 caracteres.")
    elif not re.match(r'^[a-z0-9_\.]+$', username.strip().lower()):
        errors.append("El usuario solo puede tener letras minúsculas, números, _ y .")
    if not password:
        errors.append("La contraseña es obligatoria.")
    elif len(password) < 8:
        errors.append("La contraseña debe tener al menos 8 caracteres.")
    if password and password != confirm:
        errors.append("Las contraseñas no coinciden.")
    return errors


def _create_system_user(
    username: str,
    password: str,
    nombre_completo: str,
    email: str,
    role: str,
    client_id: str | None = None,
    created_by: str | None = None,  # reservado para uso futuro si se agrega la columna
) -> None:
    """Inserta un nuevo usuario en saas_users. Lanza excepción si falla."""
    supabase.table("saas_users").insert({
        "username":        username.strip().lower(),
        "password_hash":   _hash_password(password),
        "nombre_completo": nombre_completo.strip(),
        "email":           email.strip().lower(),
        "role":            role,
        "client_id":       client_id,
        "is_active":       True,
    }).execute()


def load_consultores() -> list:
    try:
        return supabase.table("saas_consultores").select("*").order("nombre").execute().data or []
    except Exception:
        return []


def load_clientes() -> list:
    try:
        return supabase.table("saas_clientes").select("*").order("nombre_comercial").execute().data or []
    except Exception:
        return []


def load_asignaciones() -> list:
    try:
        return supabase.table("saas_asignaciones").select("*").execute().data or []
    except Exception:
        return []


def load_credenciales() -> list:
    try:
        return supabase.table("saas_credenciales_bd").select("*").order("created_at", desc=True).execute().data or []
    except Exception:
        return []


def contar_asignaciones_cliente(cliente_id: str) -> int:
    try:
        res = supabase.table("saas_asignaciones").select("id").eq("cliente_id", cliente_id).execute()
        return len(res.data) if res.data else 0
    except Exception:
        return 0

# ==============================================================================
# 8. PESTAÑAS
# ==============================================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "👔 Consultores",
    "🏢 Clientes",
    "🔗 Asignaciones",
    "🔐 Credenciales BD",
    "🧠 Cerebro Estocástico (YAML)",
])

# ──────────────────────────────────────────────────────────────────────────────
# TAB 1: CONSULTORES
# ──────────────────────────────────────────────────────────────────────────────
with tab1:
    st.subheader("Gestión de Consultores")

    # ── Crear ─────────────────────────────────────────────────────────────────
    with st.expander("➕ Registrar Nuevo Consultor", expanded=False):
        with st.form("form_nuevo_consultor"):
            st.markdown("**Perfil**")
            c1, c2, c3 = st.columns(3)
            n_nombre = c1.text_input("Nombre Completo")
            n_email  = c2.text_input("Correo Corporativo")
            n_rol    = c3.selectbox("Rol", ["Consultor Estratégico", "Admin", "Partner"])

            st.markdown("**🔑 Credenciales de Acceso al Sistema**")
            ca, cb, cc = st.columns(3)
            n_user  = ca.text_input("Usuario de Login", placeholder="ej. jgarcia")
            n_pass  = cb.text_input("Contraseña", type="password")
            n_pass2 = cc.text_input("Confirmar Contraseña", type="password")

            if st.form_submit_button("Registrar Consultor y Crear Acceso"):
                errors: list[str] = []
                if not n_nombre.strip():
                    errors.append("El nombre completo es obligatorio.")
                if not n_email.strip():
                    errors.append("El correo es obligatorio.")
                errors += _validate_credentials(n_user, n_pass, n_pass2)

                if errors:
                    for err in errors:
                        st.error(f"❌ {err}")
                else:
                    username_clean = n_user.strip().lower()
                    if _username_exists(username_clean):
                        st.error(f"❌ El usuario `{username_clean}` ya existe en el sistema.")
                    else:
                        try:
                            # 1. Crear perfil de consultor
                            supabase.table("saas_consultores").insert({
                                "nombre": n_nombre.strip(),
                                "email":  n_email.strip().lower(),
                                "rol":    n_rol,
                                "activo": True,
                            }).execute()

                            # 2. Crear acceso al sistema
                            _create_system_user(
                                username=username_clean,
                                password=n_pass,
                                nombre_completo=n_nombre.strip(),
                                email=n_email.strip().lower(),
                                role=ROLE_MAP_CONS.get(n_rol, "Consultor"),
                                created_by=st.session_state.get("username", "admin"),
                            )
                            st.success(
                                f"✅ **{n_nombre}** registrado correctamente.  \n"
                                f"Usuario de acceso: `{username_clean}` | Rol: `{ROLE_MAP_CONS.get(n_rol,'Consultor')}`"
                            )
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

    # ── Listar ────────────────────────────────────────────────────────────────
    st.markdown("##### Consultores Registrados")
    ROLES_CONS = ["Consultor Estratégico", "Admin", "Partner"]

    for c in load_consultores():
        cid    = c.get("id")
        activo = c.get("activo", True)
        estado = "🔓 Activo" if activo else "🔒 Bloqueado"

        col_info, col_edit, col_blk, col_del = st.columns([4, 1, 1, 1])
        col_info.markdown(
            f"**{c.get('nombre','—')}** · {c.get('email','—')}  \n"
            f"{c.get('rol','—')} · {estado}"
        )

        if col_edit.button("✏️", key=f"e_c_{cid}", help="Editar"):
            st.session_state[f"edit_c_{cid}"] = not st.session_state.get(f"edit_c_{cid}", False)
            st.session_state.pop(f"del_c_{cid}", None)

        if col_blk.button("🔓" if not activo else "🔒", key=f"blk_c_{cid}", help="Bloquear/Desbloquear"):
            try:
                supabase.table("saas_consultores").update({"activo": not activo}).eq("id", cid).execute()
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

        if col_del.button("🗑️", key=f"d_c_{cid}", help="Eliminar"):
            st.session_state[f"del_c_{cid}"] = not st.session_state.get(f"del_c_{cid}", False)
            st.session_state.pop(f"edit_c_{cid}", None)

        # Formulario edición inline
        if st.session_state.get(f"edit_c_{cid}"):
            with st.form(key=f"fe_c_{cid}"):
                e1, e2, e3 = st.columns(3)
                ed_nombre = e1.text_input("Nombre", value=c.get("nombre", ""))
                ed_email  = e2.text_input("Email",  value=c.get("email", ""))
                cur_rol   = c.get("rol", "Consultor Estratégico")
                idx_rol   = ROLES_CONS.index(cur_rol) if cur_rol in ROLES_CONS else 0
                ed_rol    = e3.selectbox("Rol", ROLES_CONS, index=idx_rol)
                s1, s2    = st.columns(2)
                if s1.form_submit_button("💾 Guardar"):
                    try:
                        supabase.table("saas_consultores").update({
                            "nombre": ed_nombre.strip(),
                            "email":  ed_email.strip().lower(),
                            "rol":    ed_rol,
                        }).eq("id", cid).execute()
                        st.session_state.pop(f"edit_c_{cid}", None)
                        st.success("✅ Actualizado.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                if s2.form_submit_button("Cancelar"):
                    st.session_state.pop(f"edit_c_{cid}", None)
                    st.rerun()

        # Confirmación eliminación
        if st.session_state.get(f"del_c_{cid}"):
            st.warning(f"⚠️ Esta acción NO se puede deshacer.")
            confirmar = st.checkbox(f"Confirmo eliminar a **{c.get('nombre')}**", key=f"chk_c_{cid}")
            d1, d2 = st.columns(2)
            if d1.button("🗑️ Sí, eliminar", key=f"yes_c_{cid}", disabled=not confirmar, type="primary"):
                try:
                    supabase.table("saas_consultores").delete().eq("id", cid).execute()
                    st.session_state.pop(f"del_c_{cid}", None)
                    st.success("✅ Eliminado.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            if d2.button("❌ Cancelar", key=f"no_c_{cid}"):
                st.session_state.pop(f"del_c_{cid}", None)
                st.rerun()

        st.markdown("<hr style='margin:4px 0; border-color:#f0f0f0;'>", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# TAB 2: CLIENTES
# ──────────────────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Portafolio de Clientes")

    INDUSTRIAS = [
        "Construcción", "Real Estate", "Manufactura", "Tecnología",
        "Servicios Financieros", "Salud", "Retail", "Energía", "Educación", "Otro",
    ]

    # ── Crear ─────────────────────────────────────────────────────────────────
    with st.expander("➕ Dar de Alta Cliente", expanded=False):
        with st.form("form_nuevo_cliente"):
            c1, c2 = st.columns(2)
            n_nc      = c1.text_input("Nombre Comercial")
            n_rfc     = c2.text_input("RFC")
            c3, c4 = st.columns(2)
            n_ind     = c3.selectbox("Industria", INDUSTRIAS)
            n_contact = c4.text_input("Contacto Principal")
            n_email_c = st.text_input("Email de Contacto")

            st.markdown("**🔑 Acceso al Portal (Vista Ejecutivo)**")
            st.caption("El cliente podrá ver el semáforo y reportes con estas credenciales.")
            ca, cb, cc = st.columns(3)
            n_cl_user  = ca.text_input("Usuario de Login", placeholder="ej. cliente_empresa")
            n_cl_pass  = cb.text_input("Contraseña", type="password")
            n_cl_pass2 = cc.text_input("Confirmar Contraseña", type="password")

            if st.form_submit_button("Dar de Alta y Crear Acceso"):
                errors: list[str] = []
                if not n_nc.strip():
                    errors.append("El nombre comercial es obligatorio.")
                # Validar credenciales solo si se proporcionaron
                crear_acceso = bool(n_cl_user.strip() or n_cl_pass or n_cl_pass2)
                if crear_acceso:
                    cred_errors = _validate_credentials(n_cl_user, n_cl_pass, n_cl_pass2)
                    errors.extend(cred_errors)
                    if not errors and _username_exists(n_cl_user.strip().lower()):
                        errors.append(f"El usuario '{n_cl_user.strip().lower()}' ya existe.")
                    if not errors and n_email_c.strip() and _email_exists(n_email_c.strip().lower()):
                        errors.append(f"El email '{n_email_c.strip().lower()}' ya está en uso en saas_users.")

                if errors:
                    for err in errors:
                        st.warning(err)
                else:
                    try:
                        # 1️⃣ Insertar en saas_clientes y recuperar UUID
                        res_cli = supabase.table("saas_clientes").insert({
                            "nombre_comercial": n_nc.strip(),
                            "rfc":              n_rfc.strip().upper(),
                            "industria":        n_ind,
                            "contacto":         n_contact.strip(),
                            "email_contacto":   n_email_c.strip().lower(),
                            "estatus":          "Activo",
                        }).execute()

                        new_client_id = res_cli.data[0]["id"] if res_cli.data else None

                        # 2️⃣ Crear usuario Ejecutivo si se proporcionaron credenciales
                        if crear_acceso and new_client_id:
                            nombre_completo = n_contact.strip() or n_nc.strip()
                            _create_system_user(
                                username=n_cl_user,
                                password=n_cl_pass,
                                nombre_completo=nombre_completo,
                                email=n_email_c.strip().lower() or f"{n_cl_user.strip().lower()}@cliente.local",
                                role="Ejecutivo",
                                client_id=str(new_client_id),
                                created_by=st.session_state.get("username", "admin-panel"),
                            )
                            st.success(f"✅ Cliente **{n_nc}** dado de alta con acceso de portal creado para **{n_cl_user.strip().lower()}**.")
                        else:
                            st.success(f"✅ {n_nc} dado de alta (sin acceso de portal).")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    # ── Listar ────────────────────────────────────────────────────────────────
    st.markdown("##### Clientes en Portafolio")

    for cl in load_clientes():
        clid   = cl.get("id")
        activo = cl.get("estatus", "Activo") == "Activo"
        estado = "🟢 Activo" if activo else "🔴 Bloqueado"

        col_info, col_edit, col_blk, col_del = st.columns([4, 1, 1, 1])
        col_info.markdown(
            f"**{cl.get('nombre_comercial','—')}** · {cl.get('industria','—')}  \n"
            f"RFC: {cl.get('rfc','—')} · {cl.get('contacto','—')} · {estado}"
        )

        if col_edit.button("✏️", key=f"e_cl_{clid}", help="Editar"):
            st.session_state[f"edit_cl_{clid}"] = not st.session_state.get(f"edit_cl_{clid}", False)
            st.session_state.pop(f"del_cl_{clid}", None)

        if col_blk.button("🟢" if not activo else "🔴", key=f"blk_cl_{clid}", help="Activar/Bloquear"):
            try:
                nuevo = "Activo" if not activo else "Inactivo"
                supabase.table("saas_clientes").update({"estatus": nuevo}).eq("id", clid).execute()
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

        if col_del.button("🗑️", key=f"d_cl_{clid}", help="Eliminar"):
            st.session_state[f"del_cl_{clid}"] = not st.session_state.get(f"del_cl_{clid}", False)
            st.session_state.pop(f"edit_cl_{clid}", None)

        if st.session_state.get(f"edit_cl_{clid}"):
            with st.form(key=f"fe_cl_{clid}"):
                e1, e2 = st.columns(2)
                ed_nc  = e1.text_input("Nombre Comercial", value=cl.get("nombre_comercial", ""))
                cur_ind = cl.get("industria", "Otro")
                idx_ind = INDUSTRIAS.index(cur_ind) if cur_ind in INDUSTRIAS else len(INDUSTRIAS) - 1
                ed_ind  = e2.selectbox("Industria", INDUSTRIAS, index=idx_ind)
                e3, e4 = st.columns(2)
                ed_cont = e3.text_input("Contacto", value=cl.get("contacto", ""))
                ed_eml  = e4.text_input("Email",    value=cl.get("email_contacto", ""))
                s1, s2  = st.columns(2)
                if s1.form_submit_button("💾 Guardar"):
                    try:
                        supabase.table("saas_clientes").update({
                            "nombre_comercial": ed_nc.strip(),
                            "industria":        ed_ind,
                            "contacto":         ed_cont.strip(),
                            "email_contacto":   ed_eml.strip().lower(),
                        }).eq("id", clid).execute()
                        st.session_state.pop(f"edit_cl_{clid}", None)
                        st.success("✅ Actualizado.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                if s2.form_submit_button("Cancelar"):
                    st.session_state.pop(f"edit_cl_{clid}", None)
                    st.rerun()

        if st.session_state.get(f"del_cl_{clid}"):
            n_asig = contar_asignaciones_cliente(clid)
            msg_asig = f"⚠️ Este cliente tiene **{n_asig} asignación(es)** activa(s) que también serán eliminadas." if n_asig else ""
            if msg_asig:
                st.warning(msg_asig)
            st.error("⚠️ Esta acción NO se puede deshacer.")
            confirmar = st.checkbox(
                f"Confirmo eliminar **{cl.get('nombre_comercial')}** y TODAS sus asignaciones",
                key=f"chk_cl_{clid}"
            )
            d1, d2 = st.columns(2)
            if d1.button("🗑️ Sí, eliminar", key=f"yes_cl_{clid}", disabled=not confirmar, type="primary"):
                try:
                    supabase.table("saas_asignaciones").delete().eq("cliente_id", clid).execute()
                    supabase.table("saas_clientes").delete().eq("id", clid).execute()
                    st.session_state.pop(f"del_cl_{clid}", None)
                    st.success("✅ Cliente y asignaciones eliminados.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            if d2.button("❌ Cancelar", key=f"no_cl_{clid}"):
                st.session_state.pop(f"del_cl_{clid}", None)
                st.rerun()

        st.markdown("<hr style='margin:4px 0; border-color:#f0f0f0;'>", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# TAB 3: ASIGNACIONES
# ──────────────────────────────────────────────────────────────────────────────
with tab3:
    st.subheader("Asignación Estratégica")

    cons_t3    = load_consultores()
    cli_t3     = load_clientes()
    dcons_t3   = {c["nombre"]: c["id"] for c in cons_t3 if c.get("activo", True)}
    dcli_t3    = {c["nombre_comercial"]: c["id"] for c in cli_t3 if c.get("estatus", "Activo") == "Activo"}
    id_to_cons = {c["id"]: c["nombre"] for c in cons_t3}
    id_to_cli  = {c["id"]: c["nombre_comercial"] for c in cli_t3}

    # ── Crear ─────────────────────────────────────────────────────────────────
    if dcons_t3 and dcli_t3:
        with st.expander("➕ Nueva Asignación", expanded=False):
            with st.form("form_nueva_asig"):
                sel_c = st.selectbox("Consultor (activos)", list(dcons_t3.keys()))
                sel_cl = st.selectbox("Cliente (activos)",   list(dcli_t3.keys()))
                if st.form_submit_button("Vincular Cuenta"):
                    # Verificar duplicado
                    try:
                        dup = supabase.table("saas_asignaciones").select("id").match({
                            "consultor_id": dcons_t3[sel_c],
                            "cliente_id":   dcli_t3[sel_cl],
                        }).execute()
                        if dup.data:
                            st.error("❌ Ya existe una asignación entre este consultor y cliente.")
                        else:
                            supabase.table("saas_asignaciones").insert({
                                "consultor_id": dcons_t3[sel_c],
                                "cliente_id":   dcli_t3[sel_cl],
                            }).execute()
                            st.success("✅ Asignación creada.")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
    else:
        st.warning("Se necesita al menos 1 consultor y 1 cliente activos.")

    # ── Listar ────────────────────────────────────────────────────────────────
    st.markdown("##### Asignaciones Activas")
    asigs = load_asignaciones()

    if not asigs:
        st.info("No hay asignaciones registradas.")

    for asig in asigs:
        aid      = asig.get("id")
        c_nom    = id_to_cons.get(asig.get("consultor_id"), "—")
        cl_nom   = id_to_cli.get(asig.get("cliente_id"), "—")

        col_info, col_edit, col_del = st.columns([5, 1, 1])
        col_info.markdown(f"**{c_nom}** → {cl_nom}")

        if col_edit.button("✏️", key=f"e_a_{aid}", help="Reasignar"):
            st.session_state[f"edit_a_{aid}"] = not st.session_state.get(f"edit_a_{aid}", False)
            st.session_state.pop(f"del_a_{aid}", None)

        if col_del.button("🗑️", key=f"d_a_{aid}", help="Eliminar"):
            st.session_state[f"del_a_{aid}"] = not st.session_state.get(f"del_a_{aid}", False)
            st.session_state.pop(f"edit_a_{aid}", None)

        if st.session_state.get(f"edit_a_{aid}"):
            with st.form(key=f"fe_a_{aid}"):
                cons_list = list(dcons_t3.keys())
                cli_list  = list(dcli_t3.keys())
                idx_c  = cons_list.index(c_nom)  if c_nom  in cons_list else 0
                idx_cl = cli_list.index(cl_nom)  if cl_nom in cli_list  else 0
                new_c  = st.selectbox("Nuevo Consultor", cons_list, index=idx_c)
                new_cl = st.selectbox("Nuevo Cliente",   cli_list,  index=idx_cl)
                s1, s2 = st.columns(2)
                if s1.form_submit_button("💾 Guardar Reasignación"):
                    if new_c == c_nom and new_cl == cl_nom:
                        st.error("❌ Debes cambiar al menos un campo.")
                    else:
                        # Verificar duplicado
                        try:
                            dup = supabase.table("saas_asignaciones").select("id").match({
                                "consultor_id": dcons_t3[new_c],
                                "cliente_id":   dcli_t3[new_cl],
                            }).execute()
                            if dup.data:
                                st.error("❌ Ya existe esa asignación.")
                            else:
                                supabase.table("saas_asignaciones").update({
                                    "consultor_id": dcons_t3[new_c],
                                    "cliente_id":   dcli_t3[new_cl],
                                }).eq("id", aid).execute()
                                st.session_state.pop(f"edit_a_{aid}", None)
                                st.success("✅ Reasignado.")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                if s2.form_submit_button("Cancelar"):
                    st.session_state.pop(f"edit_a_{aid}", None)
                    st.rerun()

        if st.session_state.get(f"del_a_{aid}"):
            confirmar = st.checkbox(f"Confirmo eliminar asignación **{c_nom} → {cl_nom}**", key=f"chk_a_{aid}")
            d1, d2 = st.columns(2)
            if d1.button("🗑️ Sí, eliminar", key=f"yes_a_{aid}", disabled=not confirmar, type="primary"):
                try:
                    supabase.table("saas_asignaciones").delete().eq("id", aid).execute()
                    st.session_state.pop(f"del_a_{aid}", None)
                    st.success("✅ Asignación eliminada.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            if d2.button("❌ Cancelar", key=f"no_a_{aid}"):
                st.session_state.pop(f"del_a_{aid}", None)
                st.rerun()

        st.markdown("<hr style='margin:4px 0; border-color:#f0f0f0;'>", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# TAB 4: CREDENCIALES BD — CONEXIONES VERSÁTILES
# ──────────────────────────────────────────────────────────────────────────────
with tab4:
    st.subheader("Conexión al Data Mesh del Cliente")

    cli_t4     = load_clientes()
    dcli_t4    = {c["nombre_comercial"]: c["id"] for c in cli_t4}
    id_to_cli4 = {c["id"]: c["nombre_comercial"] for c in cli_t4}

    AUTH_METHODS = {
        "bearer":     "Bearer Token",
        "api_key":    "API Key (header X-API-Key)",
        "basic_auth": "Basic Auth (usuario:contraseña)",
        "oauth2":     "OAuth 2.0 (token pre-obtenido)",
    }
    AUTH_KEYS   = list(AUTH_METHODS.keys())
    AUTH_LABELS = list(AUTH_METHODS.values())

    DB_LABELS = {
        "postgresql": "PostgreSQL",
        "mysql":      "MySQL",
        "sqlserver":  "SQL Server",
        "oracle":     "Oracle",
        "sqlite":     "SQLite (archivo local)",
    }
    DB_KEYS   = list(DB_LABELS.keys())

    if not dcli_t4:
        st.info("Registre clientes en la pestaña Clientes primero.")
    else:
        # ── NUEVA CREDENCIAL ──────────────────────────────────────────────────
        with st.expander("➕ Agregar Nueva Credencial", expanded=False):

            # Radio FUERA del form para cambio dinámico de campos
            metodo = st.radio(
                "Método de Conexión",
                ["api_rest", "sql_directo"],
                format_func=lambda x: "🌐 API REST / GraphQL" if x == "api_rest" else "🗄️ Base de Datos (SQL Directo)",
                horizontal=True,
                key="nc_metodo",
            )

            cliente_nc = st.selectbox("Cliente", list(dcli_t4.keys()), key="nc_cliente")

            # ── CAMPOS API ────────────────────────────────────────────────────
            if metodo == "api_rest":
                endpoint_v = st.text_input(
                    "Endpoint Base", placeholder="https://api.empresa.com/v1/data", key="nc_endpoint"
                )
                col_am, col_tok = st.columns(2)
                auth_label = col_am.selectbox("Método de Autenticación", AUTH_LABELS, key="nc_auth_label")
                auth_key_v = AUTH_KEYS[AUTH_LABELS.index(auth_label)]
                token_v    = col_tok.text_input(
                    "Token / API Key / usuario:contraseña", type="password", key="nc_token",
                    help="Para Basic Auth: escribe 'usuario:contraseña'"
                )
                headers_v  = st.text_area(
                    "Headers adicionales (JSON, opcional)",
                    placeholder='{"X-Tenant": "mi-empresa", "Accept": "application/json"}',
                    height=80,
                    key="nc_headers",
                )

                col_test, col_save = st.columns(2)

                if col_test.button("🔍 Probar Conexión API", key="nc_test_api"):
                    if not endpoint_v.strip():
                        st.error("❌ El endpoint es obligatorio.")
                    elif not validar_url(endpoint_v):
                        st.error("❌ El endpoint debe ser una URL válida (http/https).")
                    else:
                        ok, msg = probar_conexion_api(endpoint_v, auth_key_v, token_v, headers_v)
                        if ok:
                            st.success(msg)
                        else:
                            st.error(msg)

                if col_save.button("💾 Guardar Credencial API", key="nc_save_api"):
                    errors = []
                    if not endpoint_v.strip():
                        errors.append("El endpoint es obligatorio.")
                    elif not validar_url(endpoint_v):
                        errors.append("URL inválida (debe comenzar con http/https).")
                    if not token_v.strip():
                        errors.append("El token / API Key no puede estar vacío.")
                    hdrs_ok, hdrs_msg = validar_headers_json(headers_v)
                    if not hdrs_ok:
                        errors.append(hdrs_msg)

                    if errors:
                        for err in errors:
                            st.error(f"❌ {err}")
                    else:
                        try:
                            supabase.table("saas_credenciales_bd").insert({
                                "cliente_id":        dcli_t4[cliente_nc],
                                "metodo_conexion":   "api_rest",
                                "api_endpoint":      endpoint_v.strip(),
                                "api_auth_method":   auth_key_v,
                                "api_token_encrypted": encrypt_value(token_v),
                                "api_headers_json":  headers_v.strip() or None,
                            }).execute()
                            st.success(f"✅ Credencial API guardada para {cliente_nc}.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

            # ── CAMPOS SQL ────────────────────────────────────────────────────
            else:
                # Callback para actualizar puerto según tipo DB
                def _update_port():
                    db_t = st.session_state.get("nc_db_type", "postgresql")
                    st.session_state["nc_db_port"] = DB_PORTS.get(db_t, 5432)

                db_label = st.selectbox(
                    "Tipo de Base de Datos",
                    [DB_LABELS[k] for k in DB_KEYS],
                    key="nc_db_label",
                    on_change=_update_port,
                )
                db_type_v = DB_KEYS[[DB_LABELS[k] for k in DB_KEYS].index(db_label)]
                # Guardar en session_state para que el callback funcione
                st.session_state["nc_db_type"] = db_type_v

                if db_type_v != "sqlite":
                    c1, c2 = st.columns([3, 1])
                    host_v = c1.text_input("Host / URL del servidor", key="nc_db_host")
                    port_v = c2.number_input(
                        "Puerto",
                        min_value=0, max_value=65535,
                        value=st.session_state.get("nc_db_port", DB_PORTS.get(db_type_v, 5432)),
                        key="nc_db_port",
                    )
                    c3, c4 = st.columns(2)
                    user_v = c3.text_input("Usuario (solo lectura)", key="nc_db_user")
                    pass_v = c4.text_input("Contraseña", type="password", key="nc_db_pass")
                    c5, c6 = st.columns(2)
                    nombre_v  = c5.text_input("Nombre de Base de Datos", key="nc_db_nombre")
                    esquema_v = c6.text_input(
                        "Esquema (opcional)",
                        key="nc_db_esquema",
                        placeholder="public" if db_type_v == "postgresql" else "",
                        help="Opcional. Usado en PostgreSQL (search_path) y Oracle (schema)." if db_type_v in ("postgresql", "oracle") else "No aplica para este motor.",
                        disabled=db_type_v not in ("postgresql", "oracle"),
                    )
                else:
                    host_v = port_v = user_v = pass_v = esquema_v = ""
                    nombre_v = st.text_input("Ruta del archivo SQLite", key="nc_db_nombre", placeholder="/data/mi_bd.sqlite")

                # Advertencia de puerto no estándar
                if db_type_v != "sqlite" and port_v and port_v != DB_PORTS.get(db_type_v, 0):
                    st.warning(f"⚠️ Puerto no estándar. {DB_LABELS[db_type_v]} usa típicamente {DB_PORTS.get(db_type_v)}.")

                col_test, col_save = st.columns(2)

                if col_test.button("🔍 Probar Conexión SQL", key="nc_test_sql"):
                    if not nombre_v.strip():
                        st.error("❌ El nombre de la BD es obligatorio.")
                    elif db_type_v != "sqlite" and not host_v.strip():
                        st.error("❌ El host es obligatorio.")
                    else:
                        with st.spinner("Probando conexión…"):
                            ok, msg = probar_conexion_sql(
                                db_type_v,
                                host_v,
                                int(port_v) if port_v else 0,
                                user_v,
                                pass_v,
                                nombre_v,
                                esquema_v.strip() or None,
                            )
                        if ok:
                            st.success(msg)
                        else:
                            st.error(msg)

                if col_save.button("💾 Guardar Credencial SQL", key="nc_save_sql"):
                    errors = []
                    if not nombre_v.strip():
                        errors.append("El nombre de la BD es obligatorio.")
                    if db_type_v != "sqlite":
                        if not host_v.strip():
                            errors.append("El host es obligatorio.")
                        if not user_v.strip():
                            errors.append("El usuario es obligatorio.")
                        if not pass_v.strip():
                            errors.append("La contraseña es obligatoria.")
                        if not (1 <= int(port_v or 0) <= 65535):
                            errors.append("El puerto debe estar entre 1 y 65535.")

                    if errors:
                        for err in errors:
                            st.error(f"❌ {err}")
                    else:
                        try:
                            supabase.table("saas_credenciales_bd").insert({
                                "cliente_id":           dcli_t4[cliente_nc],
                                "metodo_conexion":      "sql_directo",
                                "db_type":              db_type_v,
                                "db_host":              host_v.strip(),
                                "db_port":              int(port_v) if port_v else None,
                                "db_usuario":           user_v.strip(),
                                "db_password_encrypted": encrypt_value(pass_v),
                                "db_nombre":            nombre_v.strip(),
                                "db_esquema":           esquema_v.strip() or None,
                            }).execute()
                            st.success(f"✅ Credencial SQL guardada para {cliente_nc}.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

        # ── LISTAR CREDENCIALES ───────────────────────────────────────────────
        st.markdown("##### Credenciales Registradas")
        creds = load_credenciales()

        if not creds:
            st.info("No hay credenciales registradas.")

        for cr in creds:
            crid    = cr.get("id")
            metodo_cr = cr.get("metodo_conexion", "sql_directo")
            cli_nm  = id_to_cli4.get(cr.get("cliente_id"), "—")
            icono   = "🌐" if metodo_cr == "api_rest" else "🗄️"

            if metodo_cr == "api_rest":
                detalle = cr.get("api_endpoint", "—")
                sub     = AUTH_METHODS.get(cr.get("api_auth_method", ""), cr.get("api_auth_method", ""))
            else:
                db_t  = cr.get("db_type", "")
                detalle = f"{cr.get('db_host','—')}:{cr.get('db_port','—')} / {cr.get('db_nombre','—')}"
                sub     = DB_LABELS.get(db_t, db_t)

            col_info, col_edit, col_del = st.columns([5, 1, 1])
            col_info.markdown(
                f"{icono} **{cli_nm}** · `{metodo_cr.replace('_',' ').upper()}`  \n"
                f"`{detalle}` · {sub}"
            )

            if col_edit.button("✏️", key=f"e_cr_{crid}", help="Editar"):
                st.session_state[f"edit_cr_{crid}"] = not st.session_state.get(f"edit_cr_{crid}", False)
                st.session_state.pop(f"del_cr_{crid}", None)

            if col_del.button("🗑️", key=f"d_cr_{crid}", help="Eliminar"):
                st.session_state[f"del_cr_{crid}"] = not st.session_state.get(f"del_cr_{crid}", False)
                st.session_state.pop(f"edit_cr_{crid}", None)

            # Edición inline
            if st.session_state.get(f"edit_cr_{crid}"):
                with st.form(key=f"fe_cr_{crid}"):
                    if metodo_cr == "api_rest":
                        st.markdown("**Editar Credencial API**")
                        ed_ep = st.text_input("Endpoint", value=cr.get("api_endpoint", ""))
                        ea1, ea2 = st.columns(2)
                        cur_am = cr.get("api_auth_method", "bearer")
                        idx_am = AUTH_KEYS.index(cur_am) if cur_am in AUTH_KEYS else 0
                        ed_am  = ea1.selectbox("Auth", AUTH_LABELS, index=idx_am)
                        ed_tk  = ea2.text_input("Nuevo Token (dejar vacío = sin cambio)", type="password")
                        ed_hd  = st.text_area("Headers JSON", value=cr.get("api_headers_json", "") or "", height=70)
                        s1, s2 = st.columns(2)
                        if s1.form_submit_button("💾 Guardar"):
                            hdrs_ok, hdrs_msg = validar_headers_json(ed_hd)
                            if not hdrs_ok:
                                st.error(f"❌ {hdrs_msg}")
                            else:
                                upd = {
                                    "api_endpoint":    ed_ep.strip(),
                                    "api_auth_method": AUTH_KEYS[AUTH_LABELS.index(ed_am)],
                                    "api_headers_json": ed_hd.strip() or None,
                                }
                                if ed_tk.strip():
                                    upd["api_token_encrypted"] = encrypt_value(ed_tk)
                                try:
                                    supabase.table("saas_credenciales_bd").update(upd).eq("id", crid).execute()
                                    st.session_state.pop(f"edit_cr_{crid}", None)
                                    st.success("✅ Actualizado.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
                        if s2.form_submit_button("Cancelar"):
                            st.session_state.pop(f"edit_cr_{crid}", None)
                            st.rerun()
                    else:
                        st.markdown("**Editar Credencial SQL**")
                        cur_dt = cr.get("db_type", "postgresql")
                        idx_dt = DB_KEYS.index(cur_dt) if cur_dt in DB_KEYS else 0
                        ed_dt  = st.selectbox("Tipo de BD", [DB_LABELS[k] for k in DB_KEYS], index=idx_dt)
                        db_type_ed = DB_KEYS[[DB_LABELS[k] for k in DB_KEYS].index(ed_dt)]
                        e1, e2 = st.columns([3, 1])
                        ed_host = e1.text_input("Host", value=cr.get("db_host", ""))
                        ed_port = e2.number_input("Puerto", value=int(cr.get("db_port") or DB_PORTS.get(db_type_ed, 5432)))
                        e3, e4 = st.columns(2)
                        ed_user = e3.text_input("Usuario", value=cr.get("db_usuario", ""))
                        ed_pass = e4.text_input("Nueva Contraseña (vacío = sin cambio)", type="password")
                        e5, e6 = st.columns(2)
                        ed_nom  = e5.text_input("Nombre BD", value=cr.get("db_nombre", ""))
                        ed_esq  = e6.text_input("Esquema", value=cr.get("db_esquema", "") or "")
                        s1, s2  = st.columns(2)
                        if s1.form_submit_button("💾 Guardar"):
                            upd = {
                                "db_type":    db_type_ed,
                                "db_host":    ed_host.strip(),
                                "db_port":    int(ed_port),
                                "db_usuario": ed_user.strip(),
                                "db_nombre":  ed_nom.strip(),
                                "db_esquema": ed_esq.strip() or None,
                            }
                            if ed_pass.strip():
                                upd["db_password_encrypted"] = encrypt_value(ed_pass)
                            try:
                                supabase.table("saas_credenciales_bd").update(upd).eq("id", crid).execute()
                                st.session_state.pop(f"edit_cr_{crid}", None)
                                st.success("✅ Actualizado.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                        if s2.form_submit_button("Cancelar"):
                            st.session_state.pop(f"edit_cr_{crid}", None)
                            st.rerun()

            # Eliminación
            if st.session_state.get(f"del_cr_{crid}"):
                confirmar = st.checkbox(f"Confirmo eliminar credencial `{metodo_cr}` de **{cli_nm}**", key=f"chk_cr_{crid}")
                d1, d2 = st.columns(2)
                if d1.button("🗑️ Sí, eliminar", key=f"yes_cr_{crid}", disabled=not confirmar, type="primary"):
                    try:
                        supabase.table("saas_credenciales_bd").delete().eq("id", crid).execute()
                        st.session_state.pop(f"del_cr_{crid}", None)
                        st.success("✅ Credencial eliminada.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                if d2.button("❌ Cancelar", key=f"no_cr_{crid}"):
                    st.session_state.pop(f"del_cr_{crid}", None)
                    st.rerun()

            st.markdown("<hr style='margin:4px 0; border-color:#f0f0f0;'>", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# TAB 5: YAML BUILDER
# ──────────────────────────────────────────────────────────────────────────────
with tab5:
    st.subheader("Motor de Lógica Multivariada (YAML Architect)")

    cli_t5  = load_clientes()
    dcli_t5 = {c["nombre_comercial"]: c["id"] for c in cli_t5}

    if not dcli_t5:
        st.info("Registre clientes primero.")
    else:
        cliente_yaml          = st.selectbox("Seleccione Cliente a Modelar", list(dcli_t5.keys()))
        cliente_id_seleccionado = dcli_t5[cliente_yaml]

        st.markdown("#### 1. Inferencia Cognitiva (Llama 3)")
        contexto_operativo = st.text_area(
            "Contexto de Riesgo (Input para IA)",
            value=(
                f"Genera el modelo estocástico para {cliente_yaml}. "
                "Tablas disponibles: 'fact_compras' (costos), 'fact_proyectos' (ingresos)."
            ),
            height=80,
        )

        if st.button("🤖 Arquitectar Cerebro Estocástico (Llama 3)"):
            with st.spinner("Invocando a Llama 3…"):
                try:
                    groq_key = os.getenv("GROQ_API_KEY") or (
                        st.secrets.get("GROQ_API_KEY") if hasattr(st, "secrets") else None
                    )
                    if not groq_key:
                        st.error("⛔ No se encontró GROQ_API_KEY en secretos.")
                    else:
                        from src.ai_agent import AIFinancialAgent
                        agent    = AIFinancialAgent(api_key=groq_key)
                        nuevo_yaml = agent.generate_config_from_prompt(
                            prompt=contexto_operativo, industry="General"
                        )
                        st.session_state["yaml_editor"] = nuevo_yaml
                        st.success("✅ Arquitectura generada.")
                except Exception as e:
                    st.error(f"Fallo en la inferencia: {e}")

        st.markdown("#### 2. Código Fuente Estocástico")
        try:
            res_yaml = (
                supabase.table("saas_configuraciones_yaml")
                .select("*")
                .eq("cliente_id", cliente_id_seleccionado)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            yaml_actual = res_yaml.data[0]["yaml_content"] if res_yaml.data else ""
        except Exception:
            yaml_actual = ""

        if "yaml_editor" not in st.session_state or st.session_state.get("last_cli") != cliente_id_seleccionado:
            st.session_state["yaml_editor"] = yaml_actual
            st.session_state["last_cli"]    = cliente_id_seleccionado

        nuevo_yaml_txt = st.text_area(
            "Código Fuente del Cerebro (YAML)",
            value=st.session_state["yaml_editor"],
            height=400,
        )

        if st.button("💾 Inyectar Modelo a Producción"):
            if nuevo_yaml_txt:
                try:
                    supabase.table("saas_configuraciones_yaml").insert({
                        "cliente_id":   cliente_id_seleccionado,
                        "yaml_content": nuevo_yaml_txt,
                        "es_activo":    True,
                    }).execute()
                    st.success("✅ Modelo guardado en el Data Mesh.")
                    st.session_state["yaml_editor"] = nuevo_yaml_txt
                except Exception as e:
                    st.error(f"Error al guardar: {e}")
