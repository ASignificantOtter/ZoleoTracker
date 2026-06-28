import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Generator, NamedTuple

import pandas as pd

from zoleotracker import config


class CheckinRow(NamedTuple):
    id: int
    file: str
    checkin: str
    location: str
    link: str


def create_db_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(config.DATABASE_PATH)
    return connection


@contextmanager
def db_connection() -> Generator[sqlite3.Connection, None, None]:
    connection = create_db_connection()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def create_table_if_not_exists(connection: sqlite3.Connection) -> None:
    connection.execute("""
        CREATE TABLE IF NOT EXISTS tracker (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file TEXT,
            checkin TEXT NOT NULL UNIQUE,
            location TEXT NOT NULL,
            link TEXT NOT NULL
        )
    """)


def table_exists(connection: sqlite3.Connection) -> bool:
    result = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='tracker'"
    ).fetchall()
    return len(result) > 0


def read_last_row(connection: sqlite3.Connection) -> list[CheckinRow]:
    rows = connection.execute("""
        SELECT *
        FROM tracker
        ORDER BY id DESC
        LIMIT 1
    """).fetchall()
    return [CheckinRow(*row) for row in rows]


def insert_rows(
    connection: sqlite3.Connection,
    query_values: list[tuple[str, str, str, str]],
) -> None:
    connection.executemany("""
        INSERT OR IGNORE INTO tracker (
            file,
            checkin,
            location,
            link
        )
        VALUES (?, ?, ?, ?)
    """, query_values)


def append_dataframe(
    connection: sqlite3.Connection,
    dataframe: pd.DataFrame,
) -> None:
    dataframe.to_sql(name='tracker', con=connection, if_exists='append', index=False)


def read_to_dataframe(connection: sqlite3.Connection) -> pd.DataFrame:
    dataframe = pd.read_sql(
        'SELECT * FROM tracker',
        connection,
        index_col='checkin',
        parse_dates=['checkin'],
    )
    return dataframe


def checkin_to_str(checkin: datetime) -> str:
    return checkin.strftime('%Y-%m-%d %H:%M:%S')
