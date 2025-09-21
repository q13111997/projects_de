import pandas as pd
import aiosqlite
import logging
from datetime import datetime
from src import configs

# Khởi tạo db và import thông tin product_id cần crawl từ file xlsx
async def init_db(file_path):
    df = pd.read_excel(file_path)
    ids = df["id"].tolist()
    async with aiosqlite.connect(configs.db_file) as db:
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
