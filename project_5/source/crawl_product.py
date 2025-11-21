from datetime import datetime
from pymongo import MongoClient
from pathlib import Path
import pandas as pd
import sqlite3
import aiosqlite
import logging
import aiohttp
import re
import json
import asyncio
import random

base_dir = Path(__file__).resolve().parent.parent
output_dir = base_dir / "output"
log_file = base_dir / "logs" / "crawl_log.txt"
mongodb_db = "glamira"
mongodb_collection = "summary"
sqlite_db = 'data.db'
batch_size = 1000
concurrency = 30

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Mobile/15E148 Safari/604.1",
]

top_level_domain = ['co.uk', 'com', 'ae', 'africa', 'at', 'az', 'be', 'bg', 'ca', 'ch', 'cl', 'cn', 'cz', 'de', 'dk', 'ee',
                    'es', 'fi', 'fr', 'hk', 'hn', 'hr', 'hu', 'ie', 'in', 'is', 'it', 'jp', 'kr', 'lt', 'lv', 'md', 'nl',
                    'no', 'pl', 'pt', 'ro', 'rs', 'se', 'sg', 'si', 'sk', 'vn', 'co.id', 'co.nz', 'co.th', 'co.za',
                    # 'com.ar', 'com.au', 'com.bo', 'com.br', 'com.co', 'com.do', 'com.ec', 'com.gt', 'com.kw',
                    # 'com.mt', 'com.mx', 'com.my', 'com.pa', 'com.pe', 'com.ph', 'com.pr', 'com.py', 'com.sv', 'com.tr',
                    # 'com.tw', 'com.ua', 'com.uy'
                    ]

domain = "https://www.glamira."
sub_domain = "/catalog/product/view/id/"

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler()
    ],
)

def collect_product_ids(mongodb_db, mongodb_collection, sqlite_db, batch_size):
    # KẾT NỐI MONGODB
    client = MongoClient("mongodb://localhost:27017/")
    db = client[mongodb_db]
    collection = db[mongodb_collection]

    # SQLite
    sqlite_conn = sqlite3.connect(sqlite_db)
    sqlite_cursor = sqlite_conn.cursor()

    # Tối ưu tốc độ insert
    sqlite_cursor.execute("PRAGMA journal_mode = WAL;")
    sqlite_cursor.execute("PRAGMA synchronous = OFF;")
    sqlite_cursor.execute("PRAGMA temp_store = MEMORY;")
    sqlite_cursor.execute("PRAGMA cache_size = -200000;")

    sqlite_cursor.execute("DROP TABLE IF EXISTS product_ids")
    sqlite_cursor.execute("""
        CREATE TABLE product_ids (
            product_id TEXT,
            status TEXT DEFAULT 'Pending',
            message TEXT
        )
    """)
    sqlite_conn.commit()
    logging.info(f"Tạo thành công bảng product_ids trong sqlite")

    logging.info(f"Bắt đầu lấy danh sách product ids...")
    pipeline = [
        {
            "$match": {
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
            }
        },
        {
            "$group": {
                "_id": "$product_id"
            }
        }
    ]
    cursor = collection.aggregate(pipeline, batchSize=batch_size)

    # Insert batch vào SQLite
    sqlite_batch = []
    for doc in cursor:
        product_id = str(doc["_id"])
        sqlite_batch.append((product_id,))

        if len(sqlite_batch) >= batch_size:
            logging.info(f"Bắt đầu insert batch {batch_size} product_id vào bảng product_ids trong sqlite")
            sqlite_cursor.executemany(
                "INSERT INTO product_ids (product_id) VALUES (?)",
                sqlite_batch
            )
            sqlite_conn.commit()
            sqlite_batch = []
            logging.info(f"Insert thành công batch {batch_size} product_id vào bảng product_ids trong sqlite")
    # Insert batch còn lại
    if sqlite_batch:
        sqlite_cursor.executemany(
            "INSERT INTO product_ids (product_id) VALUES (?)",
            sqlite_batch
        )
        sqlite_conn.commit()
        logging.info(f"Insert thành công batch {len(sqlite_batch)} product_id vào bảng product_ids trong sqlite")

    sqlite_conn.close()

def clean_react_data(raw):
    raw = raw.replace("undefined", "null")
    raw = re.sub(r"(\w+)\s*:", r'"\1":', raw)
    raw = re.sub(r":\s*'([^']*)'", r': "\1"', raw)
    raw = re.sub(r",\s*}", "}", raw)
    raw = re.sub(r",\s*]", "]", raw)
    return raw

async def parse_html(html):
    pattern = re.compile(r"var\s+react_data\s*=\s*(\{.*?\});", re.DOTALL)
    match = pattern.search(html)
    if not match:
        return None
    json_text = match.group(1)
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError:
        data = json.loads(clean_react_data(json_text))
    fields = [
        "product_id", "name", "product_type", "sku",
        "price", "min_price", "max_price", "qty",
        "collection_id", "collection", "category",
        "category_name", "store_code", "gender"
    ]
    data = {f: data.get(f) for f in fields}
    return data

async def fetch_product(session, sem, product_id, domain, sub_domain, top_level_domains):
    product = None
    async with sem:
        for tld in top_level_domains:  # thử từng TLD
            url = f"{domain}{tld}{sub_domain}{product_id}"
            for attempt in range(1, 4):
                try:
                    await asyncio.sleep(random.uniform(1.0, 1.5))
                    async with session.get(
                            url,
                            headers={
                                "User-Agent": random.choice(user_agents),
                                "Accept-Language": "en-US,en;q=0.9",
                                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                                "Connection": "keep-alive",
                            },
                            timeout=10
                    ) as response:
                        status_code = response.status
                        if status_code == 200:
                            try:
                                html = await response.text()
                                data = await parse_html(html)
                                status = "Success"
                                message = f"Crawl thành công từ {url}"
                                return data, status, message
                            except Exception as e:
                                status = "Exception"
                                message = f"Lỗi parse JSON: {e} trên {url}"
                                logging.exception(f"{message} - product id: {product_id}")
                                return None, status, message
                        elif status_code == 404:
                            status = "Error"
                            message = f"Lỗi HTTP 404 trên {url}"
                            logging.warning(f"{message} - product id: {product_id}, thử TLD khác nếu có")
                            break  # thử tld tiếp theo
                        else:
                            status = "Error"
                            message = f"Lỗi HTTP {status_code} trên {url}"
                            logging.warning(f"{message} - product id: {product_id}, thử lại {attempt}/3")
                            if attempt < 3:
                                await asyncio.sleep(2 ** attempt + attempt)
                            else:
                                logging.warning(f"Crawl thất bại sau {attempt} lần thử lại - product id: {product_id} - {message}")
                except Exception as e:
                    status = "Error"
                    message = f"Lỗi exception {e} trên {url}"
                    logging.error(f"{message} - product id: {product_id}, thử lại {attempt}/3")
                    if attempt < 3:
                        await asyncio.sleep(2 ** attempt + attempt)
                    else:
                        logging.warning(f"Crawl thất bại sau {attempt} lần thử lại - product id: {product_id} - {message}")
    return None, status, message

async def fetch_product(session, sem, product_id, domain, sub_domain, top_level_domains):
    product = None
    async with sem:
        for tld in top_level_domains:  # thử từng TLD
            url = f"{domain}{tld}{sub_domain}{product_id}"
            for attempt in range(1, 4):
                try:
                    async with session.get(
                        url,
                        headers={
                            "User-Agent": random.choice(user_agents),
                            "Accept-Language": "en-US,en;q=0.9",
                            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                            "Connection": "keep-alive",
                        },
                        timeout=30
                    ) as response:
                        status_code = response.status
                        if status_code == 200:
                            try:
                                html = await response.text()
                                data = await parse_html(html)
                                status = "Success"
                                message = f"Crawl thành công từ {url}"
                                return data, status, message
                            except Exception as e:
                                status = "Exception"
                                message = f"Lỗi parse JSON: {e} trên {url}"
                                logging.exception(f"{message} - product id: {product_id}")
                                return None, status, message
                        elif status_code == 404:
                            status = "Error"
                            message = f"Lỗi HTTP 404 trên {url}"
                            logging.warning(f"{message} - product id: {product_id}, thử TLD khác nếu có")
                            break  # thử tld tiếp theo
                        else:
                            status = "Error"
                            message = f"Lỗi HTTP {status_code} trên {url}"
                            logging.warning(f"{message} - product id: {product_id}, thử lại {attempt}/3")
                            if attempt < 3:
                                await asyncio.sleep(2 ** attempt + attempt)
                            else:
                                logging.warning(f"Crawl thất bại sau {attempt} lần thử lại - product id: {product_id} - {message}")
                except Exception as e:
                    status = "Error"
                    message = f"Lỗi exception {e} trên {url}"
                    logging.error(f"{message} - product id: {product_id}, thử lại {attempt}/3")
                    if attempt < 3:
                        await asyncio.sleep(2 ** attempt + attempt)
                    else:
                        logging.warning(f"Crawl thất bại sau {attempt} lần thử lại - product id: {product_id} - {message}")
    return None, status, message

async def process_batch(session, db, sem, ids, domain, sub_domain, top_level_domains):
    tasks = [fetch_product(session, sem, pid, domain, sub_domain, top_level_domains) for pid in ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    updates = []
    products = []
    for product_id, result in zip(ids, results):
        if isinstance(result, Exception):
            updates.append(("Error", str(result), product_id))
        else:
            data, status, message = result
            updates.append((status, message, product_id))
            if data is not None:
                products.append(data)
    await db.executemany(
        "UPDATE product_ids SET status=?, message=? WHERE product_id=?",
        updates
    )
    await db.commit()
    logging.info(f"Đã commit batch {len(updates)} sản phẩm")
    if products:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_file = output_dir / f"products_batch_{len(products)}_ids_{timestamp}.csv"
        df = pd.DataFrame(products)
        try:
            df.to_csv(out_file, index=False, encoding="utf-8")
            logging.info(f"Đã ghi {len(products)} sản phẩm vào file {out_file}")
        except Exception:
            logging.exception(f"Lỗi khi xuất file csv {out_file}")

def merge_files(output_dir):
    with open(f"{output_dir}/products_info.csv",'w',encoding="utf-8") as out_file:
        first = True
        for file in output_dir.glob("products_batch_*.csv"):
            with open(file,"r",encoding="utf-8") as in_file:
                if first:
                    out_file.write(in_file.read())
                    first = False
                else:
                    next(in_file)
                    out_file.write(in_file.read())
    logging.info(f"Đã merge toàn bộ file product_batch_*.csv vào 1 file products_info.csv")
    for file in output_dir.glob("products_batch_*.csv"):
        try:
            file.unlink()
        except Exception as e:
            logging.warning(f"Không xóa được {file}: {e}")
    print(f"Đã xóa các file product_batch_*.csv")

async def main():
    # collect_product_ids(mongodb_db, mongodb_collection, sqlite_db, batch_size)

    sem = asyncio.Semaphore(concurrency)
    async with aiosqlite.connect(sqlite_db) as db:
        async with aiohttp.ClientSession() as session:
            while True:
                async with db.execute(
                    "SELECT product_id FROM product_ids WHERE status = 'Pending' LIMIT ?",
                    (batch_size,)
                ) as cursor:
                    rows = await cursor.fetchall()
                ids = [r[0] for r in rows]
                if not ids:
                    logging.info("Không còn product_id pending. Hoàn thành crawl toàn bộ sản phẩm.")
                    break
                logging.info(f"Bắt đầu crawl batch {len(ids)} sản phẩm")
                await process_batch(session, db, sem, ids, domain, sub_domain, top_level_domain)

    merge_files(output_dir)

if __name__ == "__main__":
    asyncio.run(main())
