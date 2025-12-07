from google.cloud import bigquery
import pandas as pd
import logging
from google.oauth2 import service_account
import os

# ===== CONFIG =====
PROJECT_ID = "my-de-476802"
DATASET = "quannh_dataset"
TABLE = "ip_location"

CREDENTIAL_FILE = "/home/quannh/Downloads/my-de-476802-5ae567e4b872.json"

# danh sách file CSV
CSV_FILES = [
    "./source_file/IPLocation_1.csv",
    "./source_file/IPLocation_2.csv",
    "./source_file/IPLocation_3.csv",
    "./source_file/IPLocation_4.csv",
]

# ===== Logging =====
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler('ingest_iplocation.txt', encoding="utf-8"),
        logging.StreamHandler()
    ],
)

# ===== BigQuery Client =====
logging.info("Bắt đầu kết nối đến BigQuery...")
creds = service_account.Credentials.from_service_account_file(CREDENTIAL_FILE)
client = bigquery.Client(project=PROJECT_ID, credentials=creds)

# ===== BigQuery Schema =====
schema = [
    bigquery.SchemaField("ip", "STRING"),
    bigquery.SchemaField("country_short", "STRING"),
    bigquery.SchemaField("country_long", "STRING"),
    bigquery.SchemaField("region", "STRING"),
    bigquery.SchemaField("city", "STRING"),
]

# ===== Job Config =====
job_config = bigquery.LoadJobConfig(
    schema=schema,
    write_disposition="WRITE_APPEND",       # append từng file
    source_format=bigquery.SourceFormat.CSV,
    skip_leading_rows=1,                    # bỏ header
)

table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"

logging.info(f"Bắt đầu đẩy dữ liệu vào bảng {table_id}")

# ===== Load từng file =====
for csv_file in CSV_FILES:
    if not os.path.exists(csv_file):
        logging.error(f"Không tìm thấy file {csv_file}")
        continue

    logging.info(f"Đang đọc file {csv_file}")

    # kiểm tra số dòng trước khi load (optional nhưng hữu ích)
    try:
        df = pd.read_csv(csv_file)
        logging.info(f"File {csv_file} chứa {len(df)} dòng")
    except Exception as e:
        logging.error(f"Thất bại khi đọc file {csv_file}: {e}")
        continue

    logging.info(f"Đang load file {csv_file} vào bảng {table_id}")

    with open(csv_file, "rb") as f:
        load_job = client.load_table_from_file(
            f,
            table_id,
            job_config=job_config
        )

    load_job.result()
    logging.info(f"Hòan thành load file {csv_file} vào bảng {table_id}")

# ===== Kiểm tra kết quả =====
table = client.get_table(table_id)
logging.info(f"Bảng {table_id} đã có {table.num_rows} dòng")

logging.info(f"Đã ingest thành công tất cả các file vào bảng {table_id}")
