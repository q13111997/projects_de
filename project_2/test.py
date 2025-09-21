import asyncio
import aiohttp
import aiosqlite
import csv
from pathlib import Path

api_url = "https://api.tiki.vn/product-detail/api/v1/products/{}"
output_file = Path("products.csv")

# Tập product_id đã xử lý để tránh duplicate
seen_ids = set()

async def fetch_product(session, sem, product_id):
    url = api_url.format(product_id)
    async with sem:
        try:
            async with session.get(url, timeout=30) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return product_id, data
                else:
                    return product_id, None
        except Exception as e:
            return product_id, e

async def process_batch(session, sem, ids, writer):
    tasks = []
    for pid in ids:
        if pid not in seen_ids:   # check duplicate ở code
            seen_ids.add(pid)
            tasks.append(fetch_product(session, sem, pid))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for pid, result in results:
        if isinstance(result, dict):  # thành công
            # Ghi ra file ngay
            writer.writerow([pid, result.get("name"), result.get("price")])
        elif isinstance(result, Exception):
            print(f"❌ Error for {pid}: {result}")
        else:
            print(f"⚠️ No data for {pid}")

async def main(all_ids, chunk_size=100):
    sem = asyncio.Semaphore(10)  # giới hạn concurrency
    async with aiohttp.ClientSession() as session:
        with open(output_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # Nếu file mới thì ghi header
            if f.tell() == 0:
                writer.writerow(["product_id", "name", "price"])

            # Chia chunk
            for i in range(0, len(all_ids), chunk_size):
                chunk = all_ids[i:i+chunk_size]
                await process_batch(session, sem, chunk, writer)
