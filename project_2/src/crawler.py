import asyncio
from datetime import datetime
import aiosqlite
import pandas as pd
import logging
import os
from .configs import api_url, header, output_dir, summary_file
from .db import
from .utils import clean_description

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
                        break # không retry vì không có product id
                    else:
                        status = "Error"
                        message = f"Lỗi HTTP {status_code}"
                        logging.warning(f"{message} - product id: {product_id}, thử lại {attempt}/3")
                        if attempt < 3:
                            await asyncio.sleep(2**attempt + attempt)
                        else:
                            logging.warning(f"Crawl thất bại sau {attempt} lần thử lại - product id: {product_id} - {message}")
            except Exception as e:
                status = "Error"
                message = f"Lỗi exception {e}"
                logging.error(f"{message} - product id: {product_id}, thử lại {attempt}/3")
                if attempt < 3:
                    await asyncio.sleep(2**attempt + attempt)
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
            df = df.drop_duplicates(subset=["id"],keep="first") # tránh duplicate thông tin sản phẩm trong batch trước khi ghi ra file
            df.to_csv(out_file, index=False, encoding="utf-8")
            logging.info(f"Đã ghi {len(products)} sản phẩm vào file {out_file}")
        except Exception:
            logging.exception(f"Lỗi khi xuất file csv cho batch {batch_id}")


async def export_summary(db_file):
    async with aiosqlite.connect(db_file) as db:
        async with db.execute("""
            SELECT
                status
                ,message
                ,COUNT(1) total
            FROM PRODUCTS
            GROUP BY status, message
        """) as cursor:
            status_count = await cursor.fetchall()

        async with db.execute("SELECT MIN(last_update) min_time, MAX(last_update) max_time FROM products") as cursor:
            min_time, max_time = await cursor.fetchone()

        start_time = datetime.fromisoformat(min_time)
        end_time = datetime.fromisoformat(max_time)
        duration = end_time - start_time

        with open(summary_file, "w", encoding="utf-8") as f:
            f.write("CRAWL JOB SUMMARY:\n")
            f.write(f"Tổng thời gian crawl 200k sản phẩm: {duration}\n")
            f.write("Tổng hợp kết quả theo status:\n")
            for status, message, count in status_count:
                f.write(f"- {status} - {message}: {count}\n")
    logging.info(f"Đã tổng hợp kết quả crawl vào file {summary_file}")