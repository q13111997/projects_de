from google.cloud import bigquery
from google.oauth2 import service_account
import csv

project_id = "my-de-476802"
dataset = "quannh_dataset"
tables = ["summary","ip_location","products_info"]

credential_file = "/home/quannh/Downloads/my-de-476802-5ae567e4b872.json"

credential = service_account.Credentials.from_service_account_file(credential_file)
client = bigquery.Client(project=project_id, credentials=credential)

def extract_fields(fields, parent_name=""):
    for field in fields:
        full_name = f"{parent_name}.{field.name}" if parent_name else field.name
        is_nested = "YES" if field.field_type == "RECORD" else "NO"

        rows.append({
            "name": full_name,
            "type": field.field_type,
            "mode": field.mode,
            "description": field.description or "",
            "is_nested": is_nested
        })

        # Nếu là RECORD thì đệ quy xuống các cấp sâu hơn
        if field.field_type == "RECORD" and field.fields:
            extract_fields(field.fields, full_name)

for table in tables:
    table_id = f"{project_id}.{dataset}.{table}"
    schema = client.get_table(table_id).schema

    rows = []
    extract_fields(schema)

    with open(f"schema_{table}.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "type", "mode", "description", "is_nested"])
        writer.writeheader()
        writer.writerows(rows)
