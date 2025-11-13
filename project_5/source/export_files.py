from pymongo import MongoClient
import ipaddress
import IP2Location
import csv
import logging
import glob
import os
import pandas as pd
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent
output_dir = base_dir / "output"
log_file = base_dir / "logs" / "process_log.txt"
bin_file = base_dir / "input" / "IP-COUNTRY-REGION-CITY.BIN"
db_name = "glamira"
source_collection_name = "summary"
ip_collection_name = "distinct_ips"
ip_csv_batch_size = 1000000
url_csv_batch_size = 1000000
dedup_url_csv_batch_size = 1000000

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler()
    ],
)

# KẾT NỐI MONGODB
client = MongoClient("mongodb://localhost:27017/")
db = client[db_name]
source_collection = db[source_collection_name]
ip_collection = db[ip_collection_name]

def collect_distinct_ip(source, target):
    logging.info(f"Bắt đầu lấy danh sách disticnt ip...")
    pipeline = [
        {"$sort": {"ip": 1}},  # tận dụng index ip
        {"$group": {"_id": "$ip"}},  # gom distinct IP
        {"$merge": {
            "into": target,
            "on": "_id",
            "whenMatched": "keepExisting",  # bỏ qua IP trùng
            "whenNotMatched": "insert"      # chèn IP mới
        }}
    ]
    source.aggregate(pipeline, allowDiskUse=True)
    logging.info(f"Hoàn tất merge distinct IPs vào collection {target}.")

    all_ips = list(ip_collection.find({}, {"_id": 1}))
    count_deleted = 0
    for doc in all_ips:
        ip = doc["_id"]
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            ip_collection.delete_one({"_id": ip})
            count_deleted += 1
    logging.info(f"Đã xóa {count_deleted} IP không hợp lệ trong collection distinct_ips.")

# FUNCTION EXPORT FILE THÔNG TIN LOCATION DỰA TRÊN IP
def export_file_location(ip_collection, batch_size, output_dir):
    file_index = 1
    line_count = 0
    writer = None
    f = None
    # Load IP2Location BIN file
    ip2loc = IP2Location.IP2Location(bin_file)
    # Tạo cursor loop qua ip_collection
    cursor = ip_collection.find({}, {"_id": 1}).batch_size(batch_size)
    for doc in cursor:
        ip = doc["_id"]
        # Nếu line_count đạt đến batch_size thì đóng file hiện tại, mở file mới
        if line_count % batch_size == 0:
            if line_count > 0:
                logging.info(f"Đã ghi {line_count - (file_index - 1) * batch_size} dòng vào IPLocation_{file_index}.csv")
            if writer:
                f.close()
            f = open(output_dir / f"IPLocation_{file_index}.csv", "w", newline="", encoding="utf-8")
            writer = csv.DictWriter(f, fieldnames=["ip", "country_short", "country_long", "region", "city"])
            writer.writeheader()
            file_index += 1
        try:
            rec = ip2loc.get_all(ip)
            writer.writerow({
                "ip": ip,
                "country_short": rec.country_short,
                "country_long": rec.country_long,
                "region": rec.region,
                "city": rec.city,
            })
        except Exception as e:
            logging.info(f"Lỗi lookup IP {ip} - {e}")
        line_count += 1
    # --- Đóng file cuối cùng ---
    if f:
        f.close()
    logging.info(f"Đã export {line_count} IP ra {file_index} file csv.")

# FUNCTION EXPORT FILE THÔNG TIN PRODUCT_ID VÀ URL (CHUWA
def export_product_url(collection, batch_size, output_dir):
    file_index = 1
    total_written = 0
    seen = set() # để lọc trùng product_id, url
    logging.info(f"Bắt đầu lấy thông tin product_id, url...")
    cursor = collection.find(
        {
            "collection": {
                "$in": [
                    "view_product_detail",
                    "select_product_option",
                    "select_product_option_quality",
                    "add_to_cart_action",
                    "product_detail_recommendation_visible",
                    "product_detail_recommendation_noticed",
                    "product_view_all_recommend_clicked"
                ]
            }
        },
        {
            "collection": 1,
            "product_id": 1,
            "viewing_product_id": 1,
            "current_url": 1,
            "referrer_url": 1
        }
    ).batch_size(batch_size)

    for rec in cursor:
        collection_name = rec.get("collection")
        product_id = None
        url = None
        if collection_name in (
                "view_product_detail",
                "select_product_option",
                "select_product_option_quality",
                "add_to_cart_action",
                "product_detail_recommendation_visible"
        ):
            product_id = rec.get("product_id")
            url = rec.get("current_url")
        elif collection_name == "product_detail_recommendation_noticed":
            product_id = rec.get("product_id") or rec.get("viewing_product_id")
            url = rec.get("current_url")
        elif collection_name == "product_view_all_recommend_clicked":
            product_id = rec.get("viewing_product_id")
            url = rec.get("referrer_url")
        if not product_id or not url:
            continue  # bỏ dòng trống
        seen.add((product_id, url))
        while len(seen) >= batch_size:
            with open(output_dir / f"Products_url_{file_index}.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["product_id", "url"])
                for i, (product_id, url) in enumerate(seen):
                    if i >= batch_size:
                        break
                    writer.writerow([product_id, url])
            logging.info(f"Đã ghi {len(seen):,} dòng vào file products_url_{file_index}.csv")
            file_index += 1
            seen = set(list(seen)[batch_size:])
    if seen:
        with open(output_dir / f"Products_url_{file_index}.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["product_id", "url"])
            for product_id, url in seen:
                writer.writerow([product_id, url])
        logging.info(f"Đã ghi {len(seen):,} dòng vào file products_url_{file_index}.csv")
        seen.clear()
    logging.info(f"Đã export toàn bộ product_id, url ra {file_index} file csv.")

def dedup_products_url(files_pattern, batch_size, output_dir):
    files = glob.glob(f"{output_dir}/{files_pattern}")
    seen = set()
    buffer = []
    file_index = 1
    for f in files:
        logging.info(f"Đang xử lý file: {f}")
        df = pd.read_csv(f)
        # tạo key cho global dedup
        df["key"] = df["product_id"].astype(str) + "|" + df["url"]
        df = df[~df["key"].isin(seen)]
        seen.update(df["key"])
        buffer.extend(df[["product_id", "url"]].to_records(index=False))
        while len(buffer) >= batch_size:
            with open(output_dir / f"Products_url_deduped_{file_index}.csv", "w", newline="", encoding="utf-8") as f_out:
                writer = csv.writer(f_out)
                writer.writerow(["product_id", "url"])
                for row in buffer[:batch_size]:
                    writer.writerow(row)
            logging.info(f"Đã ghi {batch_size} dòng vào Products_url_deduped_{file_index}.csv")
            file_index += 1
            buffer = buffer[batch_size:]  # giữ lại phần dư < batch_size
    if buffer:
        with open(output_dir / f"Products_url_deduped_{file_index}.csv", "w", newline="", encoding="utf-8") as f_out:
            writer = csv.writer(f_out)
            writer.writerow(["product_id", "url"])
            for row in buffer:
                writer.writerow(row)
        logging.info(f"Đã ghi {len(buffer)} dòng vào Products_url_deduped_{file_index}.csv")
        file_index += 1
    logging.info(f"Dedup file Products_url thành công. Tổng số file xuất ra: {file_index - 1}, tổng số dòng duy nhất: {len(seen):,}")

    for f in files:
        os.remove(f)
        logging.info(f"Đã xóa file {f}")

def main():
    #collect_distinct_ip(source_collection, ip_collection_name)
    #export_file_location(ip_collection, ip_csv_batch_size, output_dir)
    export_product_url(source_collection, url_csv_batch_size, output_dir)
    #dedup_products_url("Products_url_*.csv",dedup_url_csv_batch_size, output_dir)

main()