import asyncio
import aiohttp
import logging
import os
import asyncpg
from src.db import init_db
from src.crawler import fetch_product, process_batch, export_summary
from src.configs import output_dir, file_path, concurrency, limit_connect, load_config

async def main():
    os.makedirs(output_dir, exist_ok=True)
    await init_db(file_path)
    sem = asyncio.Semaphore(concurrency)
    params = load_config()
    db_conn = await asyncpg.connect(**params)
    conn = aiohttp.TCPConnector(limit=limit_connect)
    async with aiohttp.ClientSession(connector=conn) as session:
        while True:
            # Lấy batch id để crawl
            row = db_conn.fetchrow("SELECT DISTINCT batch_id FROM products WHERE status = 'Pending' ORDER BY batch_id LIMIT 1")
            if not row:
                logging.info("Đã crawl hết sản phẩm")
                break
            batch_id = row[0]
            # Reset toàn bộ batch về Pending trước khi crawl
            await db_conn.execute("UPDATE products SET status='Pending', message=NULL WHERE batch_id=?",(batch_id,))
            # Lấy danh sách sản product id trong batch để crawl
            rows = db_conn.fetch("SELECT product_id FROM products WHERE status = 'Pending' AND batch_id=?",(batch_id,))
            ids = [r[0] for r in rows]
            logging.info(f"Bắt đầu crawl batch {batch_id} ({len(ids)} sản phẩm)")
            await process_batch(session, db_conn, sem, batch_id, ids)

        # Bắt đầu crawl lại các sản phẩm lỗi tạm thời (Error nhưng không phải 404)
        logging.info("Bắt đầu crawl lại các sản phẩm lỗi khác 404")
        rows = db_conn.fetch("""
            SELECT product_id 
            FROM products 
            WHERE status='Error' AND message NOT LIKE '%404%'
        """)
        retry_ids = [r[0] for r in rows]

        if retry_ids:
            await db_conn.executemany(
                "UPDATE products SET status='Pending', message=NULL WHERE product_id=?",
                [(pid,) for pid in retry_ids]
            )
            await db_conn.commit()
            batch_id = f"retry_error"
            await process_batch(session, db_conn, sem, batch_id, retry_ids)
        else:
            logging.info("Không còn sản phẩm crawl lỗi khác 404")
        logging.info("Hoàn thành crawl toàn bộ sản phẩm")
    await export_summary(db_conn)

if __name__ == "__main__":
    asyncio.run(main())