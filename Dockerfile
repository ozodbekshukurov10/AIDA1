# syntax=docker/dockerfile:1
FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

WORKDIR /app

RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN python3.11 -m pip install --upgrade pip

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

RUN curl -fsSL https://ollama.ai/install.sh | sh

COPY . .

EXPOSE 8000
EXPOSE 11434
EXPOSE 3000

CMD ["sh", "-c", "ollama serve & sleep 2 && python3 manage.py migrate && python3 manage.py runserver 0.0.0.0:8000"]
