import sys
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rektrunner import gotRek, getRekage, requests  # noqa: E402
from database import init_rekkage_db, init_pid_db  # noqa: E402


def test_init_tables(tmp_path):
    db_file = tmp_path / "test.sqlite"
    init_rekkage_db(db_path=str(db_file))
    init_pid_db(db_path=str(db_file))
    with sqlite3.connect(db_file) as conn:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cur.fetchall()}
    assert "rekkage" in tables
    assert "rekt_PID" in tables


def test_gotRek_insert_update(tmp_path):
    db_file = tmp_path / "test.sqlite"
    init_rekkage_db(db_path=str(db_file))

    # Insert new record
    inserted = gotRek(
        "key1",
        "XBTUSD",
        100,
        5000.0,
        "Long",
        "Buy",
        db_path=str(db_file),
    )
    assert inserted is False  # new record
    with sqlite3.connect(db_file) as conn:
        cur = conn.cursor()
        cur.execute("SELECT rekt_qty FROM rekkage WHERE rekt_key='key1'")
        qty = cur.fetchone()[0]
    assert qty == 100

    # Update existing with reduced quantity
    updated = gotRek(
        "key1",
        "XBTUSD",
        50,
        5000.0,
        "Long",
        "Buy",
        db_path=str(db_file),
    )
    assert updated is True
    with sqlite3.connect(db_file) as conn:
        cur = conn.cursor()
        cur.execute("SELECT rekt_qty FROM rekkage WHERE rekt_key='key1'")
        qty = cur.fetchone()[0]
    assert qty == 50


def test_getRekage_success(monkeypatch, tmp_path):
    db_file = tmp_path / "test.sqlite"
    init_rekkage_db(db_path=str(db_file))

    class FakeResponse:
        status_code = 200
        text = (
            '[{"orderID":"1","symbol":"XBTUSD","leavesQty":10,"price":1000,'
            '"side":"Buy"}]'
        )

    def fake_get(url, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(requests, "get", fake_get)
    msgs = getRekage(db_path=str(db_file))
    assert msgs == [
        (
            "Liquidated Short position on XBTUSD. Limit Buy order for 10 @ "
            "1000 created on www.bitmex.com"
        )
    ]
