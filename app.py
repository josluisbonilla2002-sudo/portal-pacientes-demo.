import os
import time
import random
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# Twilio (opcional para OTP por WhatsApp/SMS)
USE_TWILIO = os.getenv("USE_TWILIO", "no").lower() in ["1","true","yes","y","on"]
if USE_TWILIO:
    try:
        from twilio.rest import Client
    except Exception as _e:
        USE_TWILIO = False

st.set_page_config(page_title="Portal de Pacientes - Surgimed", page_icon="🩺", layout="centered")

# --------- CONFIG ---------
DATA_PATH = os.getenv("DATA_XLSX", "datos_pacientes.xlsx")  # Ruta al Excel/CSV
ADMIN_PASS = os.getenv("ADMIN_PASS")  # Contraseña admin opcional
REQUIRE_DOB = os.getenv("REQUIRE_DOB", "auto")  # "yes", "no" o "auto"
BRAND_NAME = os.getenv("BRAND_NAME", "Surgimed | DrBonillaBariatra")
LOGO_PATH = os.getenv("LOGO_PATH", "assets/logo.png")
PRIMARY_COLOR = os.getenv("PRIMARY_COLOR", "#E60046")

# --------- STYLES ---------
def load_styles():
    try:
        with open("styles.css", "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass

load_styles()

# Header
st.image(LOGO_PATH, width=300)
st.markdown(f"<h2 style='margin-top:-0.5rem'>{BRAND_NAME}</h2>", unsafe_allow_html=True)
st.caption("Portal privado de pacientes · Datos de evolución metabólica y ponderal")

# --------- CARGA DE DATOS ---------
@st.cache_data
def load_data(path):
    # Detecta CSV o Excel
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        df = pd.read_csv(path)
    else:
        df = pd.read_excel(path, engine="openpyxl")
    df.columns = [c.strip().lower() for c in df.columns]
    # Tipos
    if "fecha" in df.columns:
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    if "cedula" in df.columns:
        df["cedula"] = df["cedula"].astype(str).str.strip()
    # IMC calculado si no existe y hay talla y peso
    if "imc" not in df.columns and set(["talla_m","peso_kg"]).issubset(df.columns):
        with pd.option_context('mode.use_inf_as_na', True):
            df["imc"] = (df["peso_kg"] / (df["talla_m"]**2)).round(1)
    # Normaliza dob si existe
    if "dob" in df.columns:
        df["dob"] = pd.to_datetime(df["dob"], errors="coerce").dt.date
    # Normaliza telefono si existe
    if "telefono" in df.columns:
        df["telefono"] = df["telefono"].astype(str).str.replace(" ", "").str.replace("-", "")
    return df

try:
    data = load_data(DATA_PATH)
except Exception as e:
    st.error(f"❌ No pude leer el archivo de datos en '{DATA_PATH}'.\n\nDetalle: {e}")
    st.stop()

required = {"cedula","fecha","peso_kg"}
missing = required - set(data.columns)
if missing:
    st.error(f"❌ Faltan columnas requeridas en el dataset: {', '.join(sorted(missing))}")
    st.info("Columnas mínimas: cedula, fecha, peso_kg. Opcionales: nombres, talla_m, imc, dob, glucemia_mg_dl, hdl_mg_dl, trigliceridos_mg_dl, email, telefono.")
    st.stop()

has_dob_col = "dob" in data.columns
must_ask_dob = (REQUIRE_DOB.lower() == "yes") or (REQUIRE_DOB.lower() == "auto" and has_dob_col)

# --------- SIDEBAR ---------
st.sidebar.title("Opciones")
admin_mode = False
if ADMIN_PASS:
    with st.sidebar.expander("🔐 Modo administrador"):
        admin_input = st.text_input("Contraseña admin", type="password")
        if admin_input:
            if admin_input == ADMIN_PASS:
                admin_mode = True
                st.sidebar.success("Admin activo")
            else:
                st.sidebar.error("Contraseña incorrecta")

st.sidebar.markdown("---")
st.sidebar.caption("Soporte: info@surgimed.ec")

# --------- LOGIN + OTP ---------
st.markdown("## Acceso seguro")
with st.form("login_form"):
    cedula = st.text_input("Número de cédula", placeholder="Ej. 1712345678")
    telefono = st.text_input("WhatsApp / Teléfono (incluye código país, p. ej. +593...)", placeholder="+5939XXXXXXXX")
    dob_value = None
    if must_ask_dob:
        dob_value = st.date_input("Fecha de nacimiento (si se solicita)", value=None, format="YYYY-MM-DD")
    send_code = st.form_submit_button("Enviar código de verificación")

if "otp_sent" not in st.session_state:
    st.session_state.otp_sent = False
if "otp_code" not in st.session_state:
    st.session_state.otp_code = None
if "otp_expires" not in st.session_state:
    st.session_state.otp_expires = 0
if "auth_ok" not in st.session_state:
    st.session_state.auth_ok = False
if "authed_cedula" not in st.session_state:
    st.session_state.authed_cedula = None

def send_otp(to_number: str):
    code = f"{random.randint(100000, 999999)}"
    st.session_state.otp_code = code
    st.session_state.otp_expires = time.time() + 300  # 5 minutos
    message_text = f"Surgimed: tu código de verificación es {code}. Válido por 5 minutos."
    if USE_TWILIO:
        sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        token = os.getenv("TWILIO_AUTH_TOKEN", "")
        from_num = os.getenv("TWILIO_FROM", "")  # e.g., whatsapp:+14155238886  o  +1XXXX
        if not (sid and token and from_num):
            st.warning("Twilio no está configurado (faltan variables de entorno). Enviado en modo DEMO (no se envía por red).")
        else:
            try:
                client = Client(sid, token)
                # Detecta si es WhatsApp o SMS
                if to_number.strip().lower().startswith("whatsapp:"):
                    _to = to_number.strip()
                else:
                    # Si usas WhatsApp, exige el prefijo 'whatsapp:'
                    _to = to_number.strip()
                client.messages.create(from_=from_num, to=_to, body=message_text)
                return True
            except Exception as e:
                st.error(f"Error enviando OTP via Twilio: {e}")
                return False
    # DEMO: mostrar el código localmente (solo desarrollo)
    with st.expander("Modo DEMO (solo desarrollo) – ver código OTP"):
        st.code(message_text)
    return True

if send_code:
    if not cedula:
        st.warning("Ingresa una cédula válida.")
    elif must_ask_dob and dob_value is None and has_dob_col:
        st.warning("Selecciona tu fecha de nacimiento.")
    else:
        # Validar que cédula exista
        df_p = data.query("cedula == @cedula").copy()
        if df_p.empty:
            st.error("No se encontraron registros para esa cédula.")
        else:
            # Validar DOB si corresponde
            if must_ask_dob and has_dob_col:
                match = df_p["dob"].dropna().astype(str).str.strip().unique()
                if len(match) > 0 and str(dob_value) not in match:
                    st.error("Fecha de nacimiento no coincide con nuestros registros.")
                else:
                    if telefono:
                        if send_otp(telefono):
                            st.success("Código enviado. Revisa tu WhatsApp/SMS.")
                            st.session_state.otp_sent = True
                            st.session_state.authed_cedula = cedula
                    else:
                        st.info("Ingresa tu número de WhatsApp/Teléfono para recibir el código.")
            else:
                if telefono:
                    if send_otp(telefono):
                        st.success("Código enviado. Revisa tu WhatsApp/SMS.")
                        st.session_state.otp_sent = True
                        st.session_state.authed_cedula = cedula
                else:
                    st.info("Ingresa tu número de WhatsApp/Teléfono para recibir el código.")

if st.session_state.otp_sent and not st.session_state.auth_ok:
    st.markdown("### Verificación")
    code_in = st.text_input("Código de 6 dígitos", max_chars=6)
    if st.button("Validar código"):
        if not st.session_state.otp_code:
            st.error("No hay un código generado.")
        elif time.time() > st.session_state.otp_expires:
            st.error("El código expiró. Solicita uno nuevo.")
            st.session_state.otp_sent = False
        elif code_in.strip() == st.session_state.otp_code:
            st.session_state.auth_ok = True
            st.success("Verificación correcta.")
        else:
            st.error("Código incorrecto.")

# --------- CONTENIDO PROTEGIDO ---------
if st.session_state.auth_ok and st.session_state.authed_cedula:
    cedula_ok = st.session_state.authed_cedula
    df_p = data.query("cedula == @cedula_ok").copy().sort_values("fecha")
    nombre_cols = [c for c in ["nombres","nombre","paciente"] if c in df_p.columns]
    nombre = df_p[nombre_cols[0]].iloc[0] if nombre_cols else "Paciente"
    st.markdown("---")
    st.subheader(f"👤 {nombre}")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Registros", len(df_p))
    with col2:
        if "imc" in df_p.columns and df_p["imc"].notna().any():
            st.metric("IMC último", f"{df_p['imc'].dropna().iloc[-1]:.1f}")
        else:
            st.metric("IMC último", "—")
    with col3:
        last_date = df_p["fecha"].dropna().iloc[-1] if df_p["fecha"].notna().any() else None
        st.metric("Última actualización", last_date.date().isoformat() if pd.notna(last_date) else "—")

    st.markdown("### 📋 Últimas mediciones")
    preferred_cols = ["fecha","peso_kg","imc","talla_m","glucemia_mg_dl","hdl_mg_dl","trigliceridos_mg_dl"]
    cols_present = [c for c in preferred_cols if c in df_p.columns]
    st.dataframe(df_p[cols_present].tail(12).reset_index(drop=True), use_container_width=True)

    st.markdown("### 📈 Evolución")
    if df_p["peso_kg"].notna().sum() > 0 and df_p["fecha"].notna().sum() > 0:
        fig = plt.figure()
        plt.plot(df_p["fecha"], df_p["peso_kg"], marker="o")
        plt.title("Peso (kg) en el tiempo")
        plt.xlabel("Fecha"); plt.ylabel("Peso (kg)")
        plt.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)
        st.pyplot(fig)
    if "imc" in df_p.columns and df_p["imc"].notna().sum() > 0:
        fig2 = plt.figure()
        plt.plot(df_p["fecha"], df_p["imc"], marker="o")
        plt.title("IMC en el tiempo")
        plt.xlabel("Fecha"); plt.ylabel("IMC")
        plt.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)
        st.pyplot(fig2)
    elif "talla_m" in df_p.columns and df_p["talla_m"].notna().any():
        t = df_p["talla_m"].ffill().bfill()
        imc_calc = df_p["peso_kg"] / (t**2)
        fig2 = plt.figure()
        plt.plot(df_p["fecha"], imc_calc, marker="o")
        plt.title("IMC (calculado) en el tiempo")
        plt.xlabel("Fecha"); plt.ylabel("IMC")
        plt.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)
        st.pyplot(fig2)

    for var, label in [("glucemia_mg_dl","Glucemia (mg/dL)"), ("hdl_mg_dl","HDL (mg/dL)"), ("trigliceridos_mg_dl","Triglicéridos (mg/dL)")]:
        if var in df_p.columns and df_p[var].notna().sum() > 0 and df_p["fecha"].notna().sum() > 0:
            figv = plt.figure()
            plt.plot(df_p["fecha"], df_p[var], marker="o")
            plt.title(f"{label} en el tiempo")
            plt.xlabel("Fecha"); plt.ylabel(label)
            plt.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)
            st.pyplot(figv)

# --------- PANEL ADMIN ---------
if admin_mode:
    st.markdown("---")
    st.header("👨‍⚕️ Panel Admin")
    st.caption("Solo visible con contraseña admin (variable de entorno ADMIN_PASS).")
    st.write("Vista general del dataset (primeras 200 filas):")
    st.dataframe(data.head(200), use_container_width=True)
    st.download_button("⬇️ Descargar CSV completo", data=data.to_csv(index=False).encode("utf-8"), file_name="datos_pacientes_export.csv", mime="text/csv")

st.markdown(f"""
---
**Privacidad**
- Acceso con verificación por OTP (WhatsApp/SMS) {'(Twilio habilitado)' if USE_TWILIO else '(DEMO local si Twilio no está configurado)'}.
- Si tu hoja contiene `dob`, puedes exigir fecha de nacimiento (`REQUIRE_DOB=yes` o `auto`).
- HTTPS recomendado tras un reverse proxy (Nginx/Caddy).

**Marca**
- Cambia colores y logo con variables de entorno o reemplazando `assets/logo.png`.
""")