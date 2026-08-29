FROM python:3.12-slim

WORKDIR /app

# Fonts, and nothing else. Certificates print real student names, and
# Helvetica's WinAnsi encoding has no glyphs for ł, ą, ę, ś, ż, ń or ğ, ş, ı —
# without a Unicode face those names fall back to transliteration.
#
# Notably NOT libgl1/libglib2.0-0. Those are the OpenCV recipe and get pasted
# into any Dockerfile that touches images. Reading the wheels' ELF headers says
# otherwise: PyMuPDF links only libc, libstdc++ and its own bundled libmupdf,
# and Pillow vendors all 26 of its dependencies. libgl1 alone pulled in llvm19,
# mesa, libdrm and libvulkan — hundreds of megabytes to render nothing.
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
