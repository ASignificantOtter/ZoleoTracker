import sqlite3
from datetime import datetime

import pytest

from zoleotracker import databaseSQL


@pytest.fixture
def in_memory_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    databaseSQL.create_table_if_not_exists(conn)
    yield conn
    conn.close()


def test_table_exists_after_create(in_memory_db):
    assert databaseSQL.table_exists(in_memory_db)


def test_table_does_not_exist_before_create():
    conn = sqlite3.connect(":memory:")
    assert not databaseSQL.table_exists(conn)
    conn.close()


def test_insert_and_read_last_row(in_memory_db):
    databaseSQL.insert_rows(
        in_memory_db,
        [("subject", "2023-08-01 10:00:00", "47.6 N, 122.3 W", "http://maps.example.com")],
    )
    in_memory_db.commit()

    rows = databaseSQL.read_last_row(in_memory_db)

    assert len(rows) == 1
    assert rows[0].checkin == "2023-08-01 10:00:00"
    assert rows[0].location == "47.6 N, 122.3 W"
    assert rows[0].link == "http://maps.example.com"


def test_read_last_row_returns_most_recent(in_memory_db):
    databaseSQL.insert_rows(
        in_memory_db,
        [
            ("sub", "2023-07-01 10:00:00", "loc1", "http://a"),
            ("sub", "2023-08-01 10:00:00", "loc2", "http://b"),
        ],
    )
    in_memory_db.commit()

    rows = databaseSQL.read_last_row(in_memory_db)

    assert len(rows) == 1
    assert rows[0].checkin == "2023-08-01 10:00:00"


def test_read_last_row_returns_empty_when_no_data(in_memory_db):
    rows = databaseSQL.read_last_row(in_memory_db)
    assert rows == []


def test_insert_ignores_duplicate_checkin(in_memory_db):
    row = ("subject", "2023-08-01 10:00:00", "loc", "http://maps")
    databaseSQL.insert_rows(in_memory_db, [row, row])
    in_memory_db.commit()

    all_rows = in_memory_db.execute("SELECT * FROM tracker").fetchall()
    assert len(all_rows) == 1


def test_checkin_to_str():
    dt = datetime(2023, 8, 1, 10, 0, 0)
    assert databaseSQL.checkin_to_str(dt) == "2023-08-01 10:00:00"


def test_checkin_row_named_fields(in_memory_db):
    databaseSQL.insert_rows(
        in_memory_db,
        [("sub", "2023-08-01 00:00:00", "loc", "http://link")],
    )
    in_memory_db.commit()

    row = databaseSQL.read_last_row(in_memory_db)[0]

    assert isinstance(row, databaseSQL.CheckinRow)
    assert row.file == "sub"
    assert row.checkin == "2023-08-01 00:00:00"
    assert row.location == "loc"
    assert row.link == "http://link"
