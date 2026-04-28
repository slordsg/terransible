import sqlite3
from collections.abc import Generator

from app.db.conn import connect


def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

