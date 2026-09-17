FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libdmtx0b \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    python-multipart \
    PyMuPDF \
    opencv-python-headless \
    pylibdmtx \
    numpy

COPY main.py .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
