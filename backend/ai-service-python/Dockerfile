FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Bind 0.0.0.0 so the Fly proxy can reach the app (not just localhost).
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
