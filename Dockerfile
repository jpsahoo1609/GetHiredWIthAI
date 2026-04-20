FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && pip install --no-cache-dir -r requirements.txt
COPY script.py .
EXPOSE 8080
CMD ["streamlit", "run", "script.py", "--server.port=8080", "--server.address=0.0.0.0"]
