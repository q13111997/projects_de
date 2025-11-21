from pymongo import MongoClient
import ipaddress
import IP2Location
import csv
import logging
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent
output_dir = base_dir / "output"
log_file = base_dir / "logs" / "export_files_location_log.txt"
bin_file = base_dir / "input" / "IP-COUNTRY-REGION-CITY.BIN"
db_name = "glamira"
source_collection_name = "summary"
ip_collection_name = "distinct_ips"
ip_csv_batch_size = 1000000
product_url_batch_size = 1000000

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
    current_file_count = 0
    writer = None
    f = None
    # Load IP2Location BIN file
    ip2loc = IP2Location.IP2Location(bin_file)
    # Tạo cursor loop qua ip_collection
    cursor = ip_collection.find({}, {"_id": 1}).batch_size(batch_size)
    for doc in cursor:
        ip = doc["_id"]
        if f is None or current_file_count >= batch_size:
            if f is not None:
                f.close()
                logging.info(f"Đã ghi {current_file_count} dòng vào IPLocation_{file_index}.csv")
                file_index += 1
                current_file_count = 0
            f = open(output_dir / f"IPLocation_{file_index}.csv", "w", newline="", encoding="utf-8")
            writer = csv.DictWriter(f, fieldnames=["ip", "country_short", "country_long", "region", "city"])
            writer.writeheader()
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
        current_file_count += 1
        line_count += 1
    # --- Đóng file cuối cùng ---
    if f:
        f.close()
        logging.info(f"Đã ghi {current_file_count} dòng vào IPLocation_{file_index}.csv")
    logging.info(f"Đã export {line_count} IP ra {file_index} file csv.")

def main():
    collect_distinct_ip(source_collection, ip_collection_name)
    export_file_location(ip_collection, ip_csv_batch_size, output_dir)

main()