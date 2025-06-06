import argparse
import os
import sys
import json
import requests
import time
import tweepy
from traceback import format_exc
import sqlite3
import logging
from logging.handlers import RotatingFileHandler
import atexit
from dataclasses import dataclass
from typing import List

from config import base_url
from database import init_rekkage_db, init_pid_db

# module level logger used by functions
logger = logging.getLogger("RektBitmex")


@dataclass
class LiquidationRecord:
    """Represent a liquidation event."""

    order_id: str
    symbol: str
    qty: int
    price: float
    position: str
    side: str


def SetupLogging(log_level: str = "INFO") -> logging.Logger:
    """Return configured logger."""

    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)

    fh = RotatingFileHandler(
        "rektbitmex.log", maxBytes=1024 * 1024, backupCount=5
    )
    fh.setLevel(level)

    ch = logging.StreamHandler()
    ch.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


def RunOnce(pid_file: str = "rektbitmex.pid") -> None:
    """Exit if another instance of this script is already running."""

    if os.path.exists(pid_file):
        try:
            with open(pid_file) as fh:
                existing_pid = int(fh.read().strip())
            os.kill(existing_pid, 0)
        except (OSError, ValueError):
            # Stale PID file
            try:
                os.remove(pid_file)
            except OSError:
                pass
        else:
            logger.info(
                "process '%s' is already running, exiting now", existing_pid
            )
            sys.exit(0)

    with open(pid_file, "w") as fh:
        fh.write(str(os.getpid()))

    def cleanup() -> None:
        try:
            os.remove(pid_file)
        except OSError:
            pass

    atexit.register(cleanup)


def gotRek(record: LiquidationRecord, db_path: str = "rekt.sqlite") -> bool:
    """Insert or update a liquidation record."""

    rc = False
    msg: List[str] = []
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM rekkage WHERE rekt_key=?", (record.order_id,))
        row = c.fetchone()
        if row:
            logger.info("checking record %s " % record.order_id)
            rc = True
            if record.qty < row[2]:
                logger.info(
                    "Rekkord %s has decreased open fill qty from %s to %s "
                    % (record.order_id, row[2], record.qty)
                )
                try:
                    with conn:
                        c.execute(
                            "UPDATE Rekkage SET rekt_qty = ? "
                            "WHERE rekt_key = ?",
                            (record.qty, record.order_id),
                        )
                    logger.info(
                        "Rekkord %s has been updated from %s to %s "
                        % (record.order_id, row[2], record.qty)
                    )
                    msg = (
                        "Liquidation %s order for %s reduced size from %s "
                        "to %s"
                        % (record.side, record.symbol, row[2], record.qty)
                    )
                    WriteRekage([msg])
                except Exception:
                    logger.error(format_exc())
        else:
            logger.info("Rek %s does NOT exist" % record.order_id)
            try:
                with conn:
                    c.execute(
                        (
                            "INSERT INTO rekkage ("
                            "rekt_key, rekt_symbol, rekt_qty, "
                            "rekt_price, rekt_position, rekt_side, rekt_ts) "
                            "VALUES (?, ?, ?, ?, ?, ?, (CURRENT_TIMESTAMP))"
                        ),
                        (
                            record.order_id,
                            record.symbol,
                            record.qty,
                            record.price,
                            record.position,
                            record.side,
                        ),
                    )
                    cur = conn.cursor()
                    cur.execute(
                        "SELECT * FROM rekkage WHERE rekt_key=?",
                        (record.order_id,),
                    )
                    for row in cur:
                        logger.info("Rekkord '%s' has been Added " % row[0])
            except Exception:
                logger.error(format_exc())

    return rc


def getRekage(
    db_path: str = "rekt.sqlite", bitmex_url: str = base_url
) -> List[str]:
    """Fetch liquidation information from BitMEX."""

    msgs: List[str] = []
    url = bitmex_url + "order/liquidations"

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Error fetching URL %s: %s", url, exc)
        return msgs

    if r.text == "null":
        logger.error("No content returned for URL %s", url)
        return msgs

    try:
        data = json.loads(r.text)
    except ValueError as exc:
        logger.error("Invalid JSON from %s: %s", url, exc)
        return msgs

    if data:
        logger.info(data)
        for rek in data:
            position = "Short" if rek["side"] == "Buy" else "Long"
            rc = gotRek(
                LiquidationRecord(
                    rek["orderID"],
                    rek["symbol"],
                    rek["leavesQty"],
                    rek["price"],
                    position,
                    rek["side"],
                ),
                db_path=db_path,
            )
            if not rc and float(rek["leavesQty"]) > 0:
                msgs.append(
                    "Liquidated %s position on %s. Limit %s order for %s @ %s "
                    "created on www.bitmex.com"
                    % (
                        position,
                        rek["symbol"],
                        rek["side"],
                        rek["leavesQty"],
                        rek["price"],
                    )
                )
    return msgs


def WriteRekage(msgs: List[str]) -> None:
    """Send liquidation messages to Twitter."""

    if msgs is None or len(msgs) == 0:
        return

    # Consumer keys and access tokens
    # Read credentials from environment variables
    app_key = os.getenv('TWITTER_APP_KEY')
    app_secret = os.getenv('TWITTER_APP_SECRET')
    access_token = os.getenv('TWITTER_ACCESS_TOKEN')
    access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

    if not all([app_key, app_secret, access_token, access_token_secret]):
        logger.warning(
            "Twitter credentials not fully configured; skipping tweet"
        )
        return

    auth = tweepy.OAuthHandler(app_key, app_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    for msg in msgs:
        try:
            logger.info("Sending twitter update '%s' " % msg)
            api.update_status(msg)
        except Exception:
            logger.error(format_exc())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RektBitmex liquidation tracker")
    parser.add_argument(
        "--db-path", default="rekt.sqlite", help="Path to SQLite database"
    )
    parser.add_argument(
        "--base-url", default=base_url, help="BitMEX API base URL"
    )
    parser.add_argument(
        "--sleep-time",
        type=int,
        default=int(os.getenv("REKT_SLEEP_TIME", "5")),
        help="Polling interval in seconds",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single iteration and exit",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    logger = SetupLogging(args.log_level)
    RunOnce()
    logger.info("Starting RektBitmex ...")
    init_rekkage_db(db_path=args.db_path)
    init_pid_db(db_path=args.db_path)

    while True:
        logger.info("Updating Rekt List ...")
        rekts = getRekage(db_path=args.db_path, bitmex_url=args.base_url)
        if rekts:
            WriteRekage(rekts)
        if args.once:
            break
        time.sleep(args.sleep_time)
    logger.info("Closing RektBitmex ...")
