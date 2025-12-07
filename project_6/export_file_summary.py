from pymongo import MongoClient
from bson import ObjectId
import json
import logging
import os
import re

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler('export_jsonl.txt', encoding="utf-8"),
        logging.StreamHandler()
    ],
)

BQ_SCHEMA = {
    "_id": "STRING",
    "api_version": "STRING",

    "cart_products": {
        "type": "REPEATED",
        "fields": {
            "amount": "INT64",
            "currency": "STRING",
            "price": "STRING",
            "product_id": "INT64",
            "option": {
                "type": "REPEATED",
                "fields": {
                    "option_id": "INT64",
                    "option_label": "STRING",
                    "value_id": "INT64",
                    "value_label": "STRING",
                    "raw": "STRING"
                }
            }
        }
    },

    "cat_id": "STRING",
    "collect_id": "STRING",
    "collection": "STRING",
    "currency": "STRING",
    "current_url": "STRING",
    "device_id": "STRING",
    "email_address": "STRING",
    "ip": "STRING",
    "is_paypal": "BOOL",
    "key_search": "STRING",
    "local_time": "STRING",

    "option": {
        "type": "REPEATED",
        "fields": {
            "Kollektion": "STRING",
            "alloy": "STRING",
            "category_id": "STRING",
            "diamond": "STRING",
            "finish": "STRING",
            "kollektion_id": "STRING",
            "option_id": "STRING",
            "option_label": "STRING",
            "pearlcolor": "STRING",
            "price": "STRING",
            "quality": "STRING",
            "quality_label": "STRING",
            "shapediamond": "STRING",
            "stone": "STRING",
            "value_id": "STRING",
            "value_label": "STRING"
        }
    },

    "order_id": "STRING",
    "price": "STRING",
    "product_id": "STRING",
    "recommendation": "BOOL",
    "recommendation_clicked_position": "INT64",
    "recommendation_product_id": "STRING",
    "recommendation_product_position": "STRING",
    "referrer_url": "STRING",
    "resolution": "STRING",
    "show_recommendation": "STRING",
    "store_id": "STRING",
    "time_stamp": "INT64",
    "user_agent": "STRING",
    "user_id_db": "STRING",
    "utm_medium": "STRING",
    "utm_source": "STRING",
    "viewing_product_id": "STRING"
}


OID_PATTERN = re.compile(r'^[0-9a-fA-F]{24}$')

def to_string(v):
    if v is None:
        return None
    return str(v)

def convert_oid(v):
    if isinstance(v, ObjectId):
        return str(v)
    if isinstance(v, str) and OID_PATTERN.match(v):
        return v
    return v

def cast_value(value, typ):
    if value is None:
        return None

    if typ == "STRING":
        return to_string(value)

    if typ == "INT64":
        try: return int(value)
        except: return None

    if typ == "BOOL":
        return bool(value)

    return value


def normalize_doc(doc, schema):
    out = {}

    for field, field_schema in schema.items():

        # Field dạng primitive
        if isinstance(field_schema, str):
            val = doc.get(field)
            val = convert_oid(val)
            out[field] = cast_value(val, field_schema)
            continue

        # Field dạng RECORD
        if isinstance(field_schema, dict):

            # RECORD REPEATED
            if field_schema.get("type") == "REPEATED":
                arr = doc.get(field, [])
                if not isinstance(arr, list):
                    arr = [arr] if arr else []

                out[field] = []
                for item in arr:
                    if isinstance(item, dict):
                        out[field].append(
                            normalize_doc(item, field_schema["fields"])
                        )
                continue

            # RECORD bình thường
            sub = doc.get(field, {})
            if not isinstance(sub, dict):
                out[field] = None
            else:
                out[field] = normalize_doc(sub, field_schema["fields"])

    return out

client = MongoClient("mongodb://localhost:27017")
collection = client["glamira"]["summary"]

output_dir = "./output"
os.makedirs(output_dir, exist_ok=True)

batch_size = 1000000
cursor = collection.find({}, batch_size=50000, no_cursor_timeout=True)

file_idx = 1
write_count = 0

f = open(f"{output_dir}/summary_{file_idx}.jsonl", "w", encoding="utf-8")
logging.info(f"Bắt đầu ghi vào file summary_{file_idx}.jsonl")

for doc in cursor:
    norm = normalize_doc(doc, BQ_SCHEMA)
    f.write(json.dumps(norm, ensure_ascii=False) + "\n")
    write_count += 1

    if write_count % batch_size == 0:
        logging.info(f"Đã ghi {batch_size} docs vào file summary_{file_idx}.jsonl")
        f.close()

        file_idx += 1
        f = open(f"{output_dir}/summary_{file_idx}.jsonl", "w", encoding="utf-8")
        logging.info(f"Bắt đầu ghi vào file summary_{file_idx}.jsonl")

f.close()
cursor.close()
client.close()

logging.info(f"DONE. Exported {write_count} docs across {file_idx} files.")
