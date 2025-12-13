FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Cloud Run sẽ inject PORT=8080
ENV PORT=8080

CMD ["functions-framework", "--target=hello_gcs", "--port=8080"]
