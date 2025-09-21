from pathlib import Path
import logging

base_dir = Path(__file__).resolve().parent.parent
api_url = "https://api.tiki.vn/product-detail/api/v1/products/{}"
file_path = base_dir / "input" / "products-0-200000.xlsx"
db_file = base_dir / "data" / "crawl.db"
output_dir = base_dir / "output"
summary_file = base_dir / "logs" /"crawl_summary.txt"
log_file = base_dir / "logs" / "crawl_log.log"
header = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}
concurrency = 60
limit_connect = 45

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler()
    ],
)