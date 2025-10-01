import asyncio
import pandas as pd
import logging
import asyncpg
from configparser import ConfigParser
from src.configs import file_path, db_config

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

async def init_db(file_path):
    df = pd.read_excel(file_path)
    ids = [(int(x),) for x in df["id"].tolist()]
    params = load_config()
    conn = await connect_db(params)
    if conn is None:
        logging.error("Không thể tạo bảng vì lỗi kết nối tới database PostgreSQL")
        return
    await conn.execute("""
            CREATE TABLE IF NOT EXISTS product_info_stg (
                id INT,
                name TEXT,
                url_key TEXT,
                price NUMERIC(15,2),
                description TEXT,
                images TEXT  
            )
            """)
    await conn.execute("""
            CREATE TABLE IF NOT EXISTS product_info (
                id INT PRIMARY KEY,
                name TEXT,
                url_key TEXT,
                price NUMERIC(15,2),
                description TEXT,
                images TEXT  
            )
            """)
    await conn.execute("""
            CREATE TABLE IF NOT EXISTS product_list (
                batch_id INTEGER,
                product_id INTEGER PRIMARY KEY,
                status TEXT DEFAULT 'Pending',
                message TEXT,
                last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
    logging.info('Tạo thành công bảng product_info và product_list!')
    count_id = await conn.fetchval("SELECT COUNT(*) FROM product_list")
    logging.info(f'Bảng product_list hiện có {count_id} product_id')
    if count_id != len(ids):
        await conn.execute("TRUNCATE TABLE product_list RESTART IDENTITY")
        logging.info('Đã xóa dữ liệu trong bảng product_list')
        await conn.copy_records_to_table(
            "product_list",
            records=ids,
            columns=["product_id"]
        )
        logging.info('Insert dữ liệu thành công vào bảng product_list')
        await conn.execute("""
                WITH t1 AS (
                    SELECT 
                        product_id,
                        CAST((ROW_NUMBER() OVER (ORDER BY product_id) - 1) / 1000 AS INTEGER) AS batch_id
                    FROM product_list
                )
                UPDATE product_list p
                SET batch_id = t1.batch_id
                FROM t1
                WHERE p.product_id = t1.product_id;
            """)
        logging.info('Đã tạo batch_id cho bảng product_list')
    else:
        logging.info('Bảng product_list đã có đủ dữ liệu, bỏ qua insert')
    await conn.close()

async def connect_db(params, retries=3, delay=5):
    for attemp in range(1,retries+1):
        try:
            db_conn = await asyncpg.connect(**params)
            logging.info("Kết nối database PostgreSQL thành công!")
            return db_conn
        except (asyncpg.InvalidPasswordError,asyncpg.InvalidCatalogNameError) as e:
            logging.error(f"Lỗi kết nối không thể khắc phục: {e}")
            return None
        except Exception as e:
            logging.warning(f"Kết nối tới database PostgreSQL thất bại lân {attemp}: {e}")
            if attemp < retries:
                logging.info(f"Thử lại sau {delay} giây...")
                await asyncio.sleep(delay)
            else:
                logging.error(f"Đã thử kết nối lại {retries} lần, không thể kết nối tới database PostgreSQL")
                return None