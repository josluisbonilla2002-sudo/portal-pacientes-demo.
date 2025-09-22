FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ./
COPY styles.css ./
COPY assets ./assets
COPY datos_pacientes.xlsx ./

EXPOSE 8501

ENV DATA_XLSX="/app/datos_pacientes.xlsx"
# ENV ADMIN_PASS="CambiaEstaClave"
# ENV REQUIRE_DOB="auto"  # yes | no | auto
# ENV USE_TWILIO="no"
# ENV TWILIO_ACCOUNT_SID=""
# ENV TWILIO_AUTH_TOKEN=""
# ENV TWILIO_FROM="whatsapp:+14155238886"  # o numero SMS, ej +1XXXXXXXXXX
# ENV BRAND_NAME="Surgimed | DrBonillaBariatra"
# ENV LOGO_PATH="/app/assets/logo.png"
# ENV PRIMARY_COLOR="#E60046"

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--browser.gatherUsageStats=false"]