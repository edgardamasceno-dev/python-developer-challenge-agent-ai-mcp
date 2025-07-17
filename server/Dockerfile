FROM python:3.11-slim

WORKDIR /app

COPY . /app

# Instale dependências essenciais (ajuste requirements.txt depois)
RUN pip install --no-cache-dir fastapi uvicorn

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 