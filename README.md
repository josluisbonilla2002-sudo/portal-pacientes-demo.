# Portal de Pacientes (Brand + OTP)

App Streamlit con branding (logo/colores) y verificación OTP por WhatsApp/SMS (Twilio).

## 1) Requisitos
- Python 3.10+
- `pip install -r requirements.txt`
- Datos en `datos_pacientes.xlsx` o CSV (puedes reemplazar por el tuyo)

## 2) Variables de entorno recomendadas
```bash
export DATA_XLSX="datos_pacientes.xlsx"     # ruta a tu Excel/CSV
export ADMIN_PASS="TuClaveAdmin"            # activa panel admin
export REQUIRE_DOB="auto"                   # yes | no | auto
export USE_TWILIO="yes"                     # habilita envío real con Twilio
export TWILIO_ACCOUNT_SID="ACxxxx"
export TWILIO_AUTH_TOKEN="xxxx"
export TWILIO_FROM="whatsapp:+14155238886"  # o +1XXXXXXXXXX para SMS
export BRAND_NAME="Surgimed | DrBonillaBariatra"
export LOGO_PATH="assets/logo.png"
export PRIMARY_COLOR="#E60046"
```

## 3) Ejecutar
```bash
streamlit run app.py
```
Abre: http://localhost:8501

## 4) Docker
```bash
docker build -t portal-pacientes-brand-otp .

docker run -it --rm -p 8501:8501   -e DATA_XLSX="/app/datos_pacientes.xlsx"   -e ADMIN_PASS="TuClaveAdmin"   -e REQUIRE_DOB="auto"   -e USE_TWILIO="yes"   -e TWILIO_ACCOUNT_SID="ACxxxx"   -e TWILIO_AUTH_TOKEN="xxxx"   -e TWILIO_FROM="whatsapp:+14155238886"   -e BRAND_NAME="Surgimed | DrBonillaBariatra"   -e LOGO_PATH="/app/assets/logo.png"   -e PRIMARY_COLOR="#E60046"   -v $(pwd)/datos_pacientes.xlsx:/app/datos_pacientes.xlsx   portal-pacientes-brand-otp
```

## 5) Datos
Mínimo: `cedula`, `fecha`, `peso_kg`.
Opcionales: `nombres`, `talla_m`, `imc`, `dob` (fecha nacimiento), `glucemia_mg_dl`, `hdl_mg_dl`, `trigliceridos_mg_dl`, `telefono` (para OTP).

## 6) Seguridad
- OTP 6 dígitos, 5 min de validez.
- DOB opcional como segundo factor.
- Recomendado: HTTPS con Nginx/Caddy.