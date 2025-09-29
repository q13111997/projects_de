from pathlib import Path
import logging
from configparser import ConfigParser

base_dir = Path(__file__).resolve().parent.parent
api_url = "https://api.tiki.vn/product-detail/api/v1/products/{}"
file_path = base_dir / "input" / "products-0-200000.xlsx"
output_dir = base_dir / "output"
summary_file = base_dir / "logs" /"crawl_summary.txt"
log_file = base_dir / "logs" / "crawl_log.log"
db_config = base_dir / "src" / "database.ini"
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

def load_config(filename=db_config, section='postgresql'):
    parser = ConfigParser()
    parser.read(filename)

    # get section, default to postgresql
    config = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            config[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))

    return config