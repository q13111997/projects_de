from google.cloud import bigquery
import logging
import os

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("bq_load.txt", encoding="utf-8"),
        logging.StreamHandler()
    ],
)

# ===== CONFIG =====
PROJECT_ID = "my-de-476802"
DATASET = "quannh_dataset"
TABLE = "summary"
BUCKET = "my_de_project_bucket"
OUTPUT_DIR = "./output"

client = bigquery.Client(project=PROJECT_ID)

def load_one_file(local_path):
    fname = os.path.basename(local_path)
    gs_path = f"gs://{BUCKET}/{fname}"

    logging.info(f"Đang upload file {fname} → {gs_path} lên GCS")
    os.system(f"gsutil cp {local_path} {gs_path}")

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition="WRITE_APPEND",
        ignore_unknown_values=True
    )

    logging.info(f"Bắt đầu load file {fname} vào bảng {PROJECT_ID}.{DATASET}.{TABLE}")
    load_job = client.load_table_from_uri(
        gs_path,
        f"{DATASET}.{TABLE}",
        job_config=job_config
    )

    result = load_job.result()
    logging.info(f"Hoàn thành load file {fname} - {result.output_rows} dòng")

if __name__ == "__main__":
    files = [os.path.join(OUTPUT_DIR, x) for x in os.listdir(OUTPUT_DIR) if x.endswith(".jsonl")]
    files.sort()

    for f in files:
        load_one_file(f)

    logging.info(f"Đã ingest thành công toàn bộ file vào bảng {PROJECT_ID}.{DATASET}.{TABLE}")
