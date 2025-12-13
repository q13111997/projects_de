import functions_framework
from google.cloud import storage, bigquery, firestore
from flask import Flask
import os

PROJECT_ID = "project-480502"
DATASET = "quannh_dataset"

storage_client = None
bq_client = None
fs = None

# Flask app để Cloud Run có cái mà listen
app = Flask(__name__)


def get_clients():
    global storage_client, bq_client, fs
    if storage_client is None:
        storage_client = storage.Client()
    if bq_client is None:
        bq_client = bigquery.Client()
    if fs is None:
        fs = firestore.Client()
    return storage_client, bq_client, fs


def already_processed(fs, event_id: str) -> bool:
    doc = fs.collection("gcs_event_log").document(event_id).get()
    return doc.exists


def mark_processed(fs, event_id: str):
    fs.collection("gcs_event_log").document(event_id).set({"processed": True})


# CLOUD EVENT HANDLER
@functions_framework.cloud_event
def hello_gcs(cloud_event):
    storage_client, bq_client, fs = get_clients()

    event_id = cloud_event["id"]
    data = cloud_event.data

    bucket_name = data["bucket"]
    file_path = data["name"]

    print(f"Triggered: {file_path}")
    print(f"Event ID: {event_id}")

    if already_processed(fs, event_id):
        print("Duplicate event -> SKIP")
        return "SKIPPED"

    mark_processed(fs, event_id)

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_path)
    if not blob.exists():
        print("File missing → stop retry")
        return "NOFILE"

    # ROUTING
    if file_path.startswith("ingest_files/summary/") and file_path.endswith(".jsonl"):
        load_jsonl(bq_client, bucket_name, file_path, f"{PROJECT_ID}.{DATASET}.summary")

    elif file_path.startswith("ingest_files/ip_location/") and file_path.endswith(".csv"):
        load_csv(bq_client, bucket_name, file_path, f"{PROJECT_ID}.{DATASET}.ip_location")

    elif file_path.startswith("ingest_files/products_info/") and file_path.endswith(".csv"):
        load_csv(bq_client, bucket_name, file_path, f"{PROJECT_ID}.{DATASET}.products_info")

    else:
        print("Pattern mismatch → skip")
        return "IGNORED"

    print("DONE ingest")
    return "OK"


def load_jsonl(bq_client, bucket_name, file_path, table):
    uri = f"gs://{bucket_name}/{file_path}"
    cfg = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition="WRITE_APPEND",
        ignore_unknown_values=True,
    )
    bq_client.load_table_from_uri(uri, table, job_config=cfg).result()
    print("Loaded JSONL")


def load_csv(bq_client, bucket_name, file_path, table):
    uri = f"gs://{bucket_name}/{file_path}"
    cfg = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        write_disposition="WRITE_APPEND",
    )
    bq_client.load_table_from_uri(uri, table, job_config=cfg).result()
    print("Loaded CSV")


# ---- Cloud Run bắt buộc phải có route HTTP ----
@app.route("/", methods=["GET"])
def index():
    return "Cloud Run event receiver OK"
