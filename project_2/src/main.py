import asyncio
from datetime import datetime
import aiohttp
import aiosqlite
import pandas as pd
import logging
from bs4 import BeautifulSoup
import os
from pathlib import Path


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
                # Lấy batch id để crawl
                async with db.execute("SELECT DISTINCT batch_id FROM products WHERE status = 'Pending' ORDER BY batch_id LIMIT 1") as cursor:
                    row = await cursor.fetchone()
                if not row:
                    logging.info("Đã crawl hết sản phẩm")
                    break
                batch_id = row[0]
                # Reset toàn bộ batch về Pending trước khi crawl
                await db.execute(
                    "UPDATE products SET status='Pending', message=NULL WHERE batch_id=?",
                    (batch_id,)
                )
                await db.commit()
                # Lấy danh sách sản product id trong batch để crawl
                async with db.execute("SELECT product_id FROM products WHERE status = 'Pending' AND batch_id=?",(batch_id,)) as cursor:
                    rows = await cursor.fetchall()
                ids = [r[0] for r in rows]
                logging.info(f"Bắt đầu crawl batch {batch_id} ({len(ids)} sản phẩm)")
                await process_batch(session, db, sem, batch_id, ids)
            logging.info("Hoàn thành crawl toàn bộ sản phẩm")
    await export_summary(db_file)

if __name__ == "__main__":
    asyncio.run(main())