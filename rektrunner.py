import os
import sys
import json
import requests
import time
import tweepy
from traceback import format_exc
import sqlite3
import logging
from config import base_url
from database import init_rekkage_db, init_pid_db

# module level logger used by functions
logger = logging.getLogger('RektBitmex')


def SetupLogging():
    """Return configured logger."""

    logger.setLevel(logging.INFO)

    fh = logging.FileHandler("rektbitmex.log")
    fh.setLevel(logging.INFO)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


def RunOnce(pid_file="rektbitmex.pid"):
    """Exit if another instance of this script is already running."""

    if os.path.exists(pid_file):
        try:
            with open(pid_file) as fh:
                existing_pid = int(fh.read().strip())
            os.kill(existing_pid, 0)
        except (OSError, ValueError):
            pass
        else:
            logger.info(
                "process '%s' is already running, exiting now", existing_pid
            )
            sys.exit(0)

    with open(pid_file, "w") as fh:
        fh.write(str(os.getpid()))


def gotRek(
    rekt_key,
    symbol,
    qty,
    price,
    position,
    side,
    db_path="rekt.sqlite",
):
    """Insert or update a liquidation record."""
    rc = False
    msg = []
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM rekkage WHERE rekt_key=?", (rekt_key,))
        row = c.fetchone()
        if row:
            logger.info("checking record %s " % rekt_key)
            rc = True
            if qty < row[2]:
                logger.info(
                    "Rekkord %s has decreased open fill qty from %s to %s "
                    % (rekt_key, row[2], qty)
                )
                try:
                    with conn:
                        c.execute(
                            "UPDATE Rekkage SET rekt_qty = ? "
                            "WHERE rekt_key = ?",
                            (qty, rekt_key),
                        )
                    logger.info(
                        "Rekkord %s has been updated from %s to %s "
                        % (rekt_key, row[2], qty)
                    )
                    msg = (
                        "Liquidation %s order for %s reduced size from %s "
                        "to %s" % (side, symbol, row[2], qty)
                    )
                    WriteRekage([msg])
                except BaseException:
                    logger.error(format_exc())
        else:
            logger.info("Rek %s does NOT exist" % rekt_key)
            try:
                with conn:
                    c.execute(
                        (
                            "INSERT INTO rekkage ("
                            "rekt_key, rekt_symbol, rekt_qty, "
                            "rekt_price, rekt_position, rekt_side, rekt_ts) "
                            "VALUES (?, ?, ?, ?, ?, ?, (CURRENT_TIMESTAMP))"
                        ),
                        (rekt_key, symbol, qty, price, position, side),
                    )
                    cur = conn.cursor()
                    cur.execute(
                        "SELECT * FROM rekkage WHERE rekt_key=?",
                        (rekt_key,),
                    )
                    for row in cur:
                        logger.info("Rekkord '%s' has been Added " % row[0])
            except BaseException:
                logger.error(format_exc())

    return rc


def getRekage(db_path="rekt.sqlite"):
    """Fetch liquidation information from BitMEX."""

    msgs = []
    url = base_url + "order/liquidations"

    try:
        r = requests.get(url, timeout=10)
    except BaseException:
        logger.error(format_exc())
        return ""

    if r.status_code != 200:
        logger.error("\nError %s while calling URL %s:\n" %
                     (r.status_code, url))
        return msgs

    if r.text == "null":
        logger.error("No content returned for URL %s" % url)
        return msgs

    data = json.loads(r.text)
    if data:
        logger.info(data)
        for rek in data:
            if rek["side"] == "Buy":
                position = "Short"
            else:
                position = "Long"
            rc = gotRek(
                rek["orderID"],
                rek["symbol"],
                rek["leavesQty"],
                rek["price"],
                position,
                rek["side"],
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


def WriteRekage(msgs):
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
        except BaseException:
            logger.error(format_exc())


if __name__ == "__main__":

    logger = SetupLogging()
    RunOnce()
    logger.info('Starting RektBitmex ...')
    init_rekkage_db()
    init_pid_db()
    SLEEPTIME = 5  # seconds

    run = None
    while run != 'n':
        logger.info("Updating Rekt List ...")
        rekts = getRekage()
        if rekts:
            WriteRekage(rekts)
        time.sleep(SLEEPTIME)
    logger.info('Closing RektBitmex ...')
