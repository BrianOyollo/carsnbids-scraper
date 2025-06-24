import sqlite3
import os
from logger import setup_json_logger
from dotenv import load_dotenv


load_dotenv()
logger = setup_json_logger()

db_path = os.getenv('SQLITE_DB_PATH')


def init_db(db_path:str=None):
    if not db_path:
        db_path = 'carsnbids.db'

    logger.info(f'Initializing SQLite db at: {db_path}')
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        logger.info('Creating urls table')
        cur.execute(
        """
            CREATE TABLE IF NOT EXISTS urls(
                auction_id TEXT PRIMARY KEY,
                url TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
        )
        logger.info('URLs table successfully created')
        conn.commit()
    except Exception as e:
        logger.error(f"Error creating urls table: {e}", exc_info=True)
    finally:
        cur.close()
        conn.close()

init_db(db_path)