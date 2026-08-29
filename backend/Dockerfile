FROM python:3.12-slim

WORKDIR /app

# PyMuPDF needs these at runtime to read the submitted PDFs.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Certificates print real student names, and Helvetica's WinAnsi encoding has
# no glyphs for ł, ą, ę, ś, ż, ń or ğ, ş, ı. DejaVu is what the certificate
# renderer looks for first; without it names fall back to transliteration.
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/

RUN mkdir -p /data/tmp

ENV REVIEW_STORAGE_ROOT=/data/tmp
ENV REVIEW_DB_PATH=/data/submissions.db

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# 30s rather than the usual 15: this container rebuilds the originality index
# from SQLite at startup before it binds a port, and on a loaded host a shorter
# window burns healthcheck attempts on an app that is simply still starting.
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
