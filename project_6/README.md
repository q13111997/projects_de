# MongoDB → GCS → BigQuery Ingestion Pipeline

## 1. Data flow:
```
MongoDB 
↓
Python export dữ liệu ra các file jsonl
↓
Upload các file jsonl và file csv chứa dữ liệu từ project trước lên GCS Bucket
↓
Cloud Function trigger khi có file mới upload lên bucket
↓
Ingest dữ liệu từ file upload vào BigQuery Table
```

---

## 2. Project Structure

```
project_6/
├── README.md
├── ingestbq_function/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py
└── source/
    ├── export_file_summary.py
    └── output
        ├── ip_location
        │   └── IPLocation.csv
        ├── products_info
        │   └── products_info.csv
        └── summary
            ├── summary_1.jsonl
            ├── ...
            └── summary_43.jsonl
 
```

---

## 3. Deploy Cloud Function ingestbq

```
# Tạo repository chứa cloud function
gcloud artifacts repositories create cloud-run \
  --repository-format=docker \
  --location=us-central1 \
  --description="Repo for Cloud Run containers"

# Submit code cloud function
gcloud builds submit \
--tag us-central1-docker.pkg.dev/project-480502/cloud-run/ingestbq

# Deploy code cloud function
gcloud run deploy ingestbq \  
--image us-central1-docker.pkg.dev/project-480502/cloud-run/ingestbq \ 
--region us-central1 \  
--allow-unauthenticated
```

---

## 4. Tạo trigger

```
gcloud eventarc triggers create gcs-trigger \
  --location=us-central1 \
  --destination-run-service=ingestbq \
  --destination-run-region=us-central1 \
  --event-filters="type=google.cloud.storage.object.v1.finalized" \
  --event-filters="bucket=quannh_bucket" \
  --service-account="321473582268-compute@developer.gserviceaccount.com"
```