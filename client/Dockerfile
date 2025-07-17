FROM python:3.11-slim

WORKDIR /app

COPY . /app

# Instala todas as dependências do requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "main.py"] 