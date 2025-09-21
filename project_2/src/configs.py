from pathlib import Path
import logging

base_dir = Path(__file__).resolve().parent.parent
api_url = "https://api.tiki.vn/product-detail/api/v1/products/{}"
file_path = base_dir / "input" / "products-0-200000.xlsx"
db_file = base_dir / "logs" / "crawl.db"
output_dir = base_dir / "output"
summary_file = base_dir / "logs" /"crawl_summary.txt"
header = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}
concurrency = 60
limit_connect = 38

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler("crawl_log.log", encoding="utf-8"),
        logging.StreamHandler()
    ],
)