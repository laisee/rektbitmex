import logging
import sqlite3

logger = logging.getLogger(__name__)

REKT_TABLE = "rekkage"
PID_TABLE = "rekt_PID"


def init_rekkage_db(db_path="rekt.sqlite"):
    """Create the rekkage table if it does not exist."""
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute(f"CREATE TABLE IF NOT EXISTS {REKT_TABLE} ("
                  "rekt_key TEXT PRIMARY KEY,"
                  " rekt_symbol TEXT,"
                  " rekt_qty INTEGER,"
                  " rekt_price REAL,"
                  " rekt_position TEXT,"
                  " rekt_side TEXT,"
                  " rekt_ts TEXT"
                  ")")
        conn.commit()


def init_pid_db(db_path="rekt.sqlite"):
    """Create the rekt_PID table if it does not exist."""
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute(f"CREATE TABLE IF NOT EXISTS {PID_TABLE} ("
                  "rekt_PID TEXT PRIMARY KEY"
                  ")")
        conn.commit()
