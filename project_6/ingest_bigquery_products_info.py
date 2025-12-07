from google.cloud import bigquery
import pandas as pd
import logging
from google.oauth2 import service_account

# ===== CONFIG =====
PROJECT_ID = "my-de-476802"
DATASET = "quannh_dataset"
TABLE = "products_info"

csv_file = "./source_file/products_info.csv"
credential_file = "/home/quannh/Downloads/my-de-476802-5ae567e4b872.json"

# ===== Logging =====
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler('ingest_products_info.txt', encoding="utf-8"),
        logging.StreamHandler()
    ],
)

# ===== BigQuery Client =====
logging.info("Bắt đầu kết nối đến BigQuery...")
creds = service_account.Credentials.from_service_account_file(credential_file)
client = bigquery.Client(project=PROJECT_ID, credentials=creds)

# ===== Load CSV =====
logging.info(f"Đang đọc file {csv_file}")
df = pd.read_csv(csv_file)

logging.info(f"File {csv_file} có {len(df)} dòng")

# ===== BigQuery Schema =====
schema = [
    bigquery.SchemaField("product_id", "STRING"),
    bigquery.SchemaField("name", "STRING"),
    bigquery.SchemaField("product_type", "STRING"),
    bigquery.SchemaField("sku", "STRING"),
    bigquery.SchemaField("price", "FLOAT"),
    bigquery.SchemaField("min_price", "FLOAT"),
    bigquery.SchemaField("max_price", "FLOAT"),
    bigquery.SchemaField("qty", "INTEGER"),
    bigquery.SchemaField("collection_id", "STRING"),
    bigquery.SchemaField("collection", "STRING"),
    bigquery.SchemaField("category", "STRING"),
    bigquery.SchemaField("category_name", "STRING"),
    bigquery.SchemaField("store_code", "STRING"),
    bigquery.SchemaField("gender", "STRING"),
]

# ===== Job Config =====
job_config = bigquery.LoadJobConfig(
    schema=schema,
    write_disposition="WRITE_TRUNCATE",
    source_format=bigquery.SourceFormat.CSV,
    skip_leading_rows=1,
)

table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"

logging.info(f"Bắt đầu ingest dữ liệu vào bảng {table_id}")

with open(csv_file, "rb") as f:
    load_job = client.load_table_from_file(
        f,
        table_id,
        job_config=job_config
    )

load_job.result()

logging.info(f"Hoàn thành ingest dữ liệu vào bảng {table_id}")

table = client.get_table(table_id)
logging.info(f"Bảng {table_id} hiện có {table.num_rows} dòng")
