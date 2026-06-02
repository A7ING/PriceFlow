FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    dbus dbus-x11 \
    && rm -rf /var/lib/apt/lists/*

ENV DBUS_SESSION_BUS_ADDRESS=/dev/null
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium --with-deps
RUN playwright install-deps firefox
RUN python -m camoufox fetch

COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]