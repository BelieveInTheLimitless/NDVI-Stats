FROM python:3.12.3

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY input.json .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]