FROM python:3.9
WORKDIR /app
COPY main.py .
COPY requirements.txt .
RUN pip install -r requirements.txt
CMD ["python", "-u", "main.py"]
