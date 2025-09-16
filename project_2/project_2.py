import asyncio
import aiohttp
import aiosqlite
import pandas as pd
import logging
from bs4 import BeautifulSoup
import os

api_url = "https://api.tiki.vn/product-detail/api/v1/products/{}"
file_path = "products-0-200000.xlsx"
db_file = "crawl.db"
output_dir = "crawled_files"
header = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}
concurrency = 60
limit_connect = 50

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler("crawl_log.log", encoding="utf-8"),
        logging.StreamHandler()
    ],
)

# parse description của product và nối với nhau bằng 1 khoảng trắng " "
def clean_description(html_text):
    if not html_text:
        return ""
    soup = BeautifulSoup(html_text, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    return " ".join(text.split())

# Khởi tạo db và import thông tin product_id cần crawl từ file xlsx
async def init_db(file_path):
    df = pd.read_excel(file_path)
    ids = df["id"].tolist()
    async with aiosqlite.connect(db_file) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS products (
            batch_id INTEGER,
            product_id INTEGER PRIMARY KEY,
            status TEXT DEFAULT 'Pending',
            message TEXT,
            last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        await db.executemany(
            "INSERT OR IGNORE INTO products (product_id) VALUES (?)",
            [(id,) for id in ids]
        )
        await db.commit()
        await db.execute("""
            WITH t1 AS (
                SELECT 
                    product_id,
                    CAST((ROW_NUMBER() OVER (ORDER BY product_id) - 1) / 1000 AS INTEGER) AS batch_id
                FROM products
            )
            UPDATE products
            SET batch_id = (
                SELECT t1.batch_id
                FROM t1
                WHERE t1.product_id = products.product_id
            );
        """)
        await db.commit()
    logging.info(f"Đã insert thành công {len(ids)} product_id vào bảng products trong crawl.db")

async def fetch_product(session, sem, product_id):
    product = None
    url = api_url.format(product_id)
    async with sem:
        for attempt in range (1,4):
            try:
                async with session.get(url, headers=header, timeout=30) as response:
                    status_code = response.status
                    if status_code == 200:
                        try:
                            data = await response.json()
                            product = {
                                "id": data.get("id"),
                                "name": data.get("name"),
                                "url_key": data.get("url_key"),
                                "price": data.get("price"),
                                "description": clean_description(data.get("description", "")),
                                "images": ", ".join([img.get("base_url", "") for img in data.get("images", [])]) if data.get("images") else "",
                            }
                            status = "Success"
                            message = None
                            break
                        except Exception as e:
                            status = "Exception"
                            message = f"Lỗi parse JSON: {e}"
                            logging.exception(f"{message} - product id: {product_id}")
                            break
                    elif status_code == 404:
                        status = "Error"
                        message = "Lỗi HTTP 404: Không tim thấy product id"
                        logging.warning(f"{message} - product id: {product_id}")
                        break
                    else:
                        status = "Error"
                        message = f"Lỗi HTTP {status_code}"
                        logging.warning(f"{message} - product id: {product_id}, thử lại {attempt}/3")
                        if attempt < 3:
                            await asyncio.sleep(2**attempt)
                        else:
                            logging.warning(f"Crawl thất bại sau {attempt} lần thử lại - product id: {product_id} - {message}")
            except Exception as e:
                status = "Error"
                message = f"Lỗi exception {e}"
                logging.error(f"{message} - product id: {product_id}, thử lại {attempt}/3")
                if attempt < 3:
                    await asyncio.sleep(2**attempt)
                else:
                    logging.warning(f"Crawl thất bại sau {attempt} lần thử lại - product id: {product_id} - {message}")
    return product, status, message

async def process_batch(session, db, sem, batch_id, ids):
    tasks = [fetch_product(session, sem, id) for id in ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    updates = []
    products = []
    for product_id, result in zip(ids,results):
        if isinstance(result, Exception):
            updates.append(("Error", str(result), product_id))
        else:
            product, status, message = result
            updates.append((status, message, product_id))
            if product is not None:
                products.append(product)
    await db.executemany("UPDATE products SET status=?, message=?, last_update=CURRENT_TIMESTAMP WHERE product_id=?",updates)
    await db.commit()
    logging.info(f"Đã commit batch {batch_id} ({len(updates)} sản phẩm)")
    if products:
        try:
            out_file = os.path.join(output_dir, f"products_batch_{batch_id}_{len(products)}_ids.csv")
            df = pd.DataFrame(products)
            df.to_csv(out_file, index=False, encoding="utf-8")
            logging.info(f"Đã ghi {len(products)} sản phẩm vào file {out_file}")
        except Exception:
            logging.exception(f"Lỗi khi xuất file csv cho batch {batch_id}")

async def main():
    os.makedirs(output_dir, exist_ok=True)
    await init_db(file_path)
    sem = asyncio.Semaphore(concurrency)

    async with aiosqlite.connect(db_file) as db:
        # bật WAL để writer/reader hiệu quả hơn
        await db.execute("PRAGMA journal_mode = WAL;")
        await db.execute("PRAGMA synchronous = NORMAL;")
        conn = aiohttp.TCPConnector(limit=limit_connect)
        async with aiohttp.ClientSession(connector=conn) as session:
            while True:
                async with db.execute("SELECT DISTINCT batch_id FROM products WHERE status = 'Pending' ORDER BY batch_id LIMIT 1") as cursor:
                    row = await cursor.fetchone()
                if not row:
                    logging.info("Đã crawl hết sản phẩm")
                    break
                batch_id = row[0]
                async with db.execute("SELECT product_id FROM products WHERE status = 'Pending' AND batch_id=?",(batch_id,)) as cursor:
                    rows = await cursor.fetchall()
                ids = [r[0] for r in rows]
                logging.info(f"Bắt đầu crawl batch {batch_id} ({len(ids)} sản phẩm)")
                await process_batch(session, db, sem, batch_id, ids)
            logging.info("Hoàn thành crawl toàn bộ sản phẩm")

if __name__ == "__main__":
    asyncio.run(main())