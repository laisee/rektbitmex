import os
import sys
import json
import requests
import time
import tweepy
from time import gmtime, strftime
from traceback import format_exc
import sqlite3
import subprocess
import logging
from config import base_url
from database import init_rekkage_db, init_pid_db

# module level logger used by functions
logger = logging.getLogger('RektBitmex')


"""Setup logging with file and console output."""
def SetupLogging():
   """Return configured logger."""
   global logger
   # configure logger with file and console handlers
   logger.setLevel(logging.INFO)

   # create file handler which logs messages
   fh = logging.FileHandler('rektbitmex.log')
   fh.setLevel(logging.INFO)

   # create console handler 
   ch = logging.StreamHandler()
   ch.setLevel(logging.INFO)
   # create formatter and add it to the handlers
   formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
   fh.setFormatter(formatter)
   ch.setFormatter(formatter)
   # add the handlers to the logger
   logger.addHandler(fh)
   logger.addHandler(ch)
   return logger

"""Exit if another instance of this script is already running."""
def RunOnce():
    """Check for another running instance and exit if found."""
    script_name = os.path.basename(__file__)
    l = subprocess.getstatusoutput("ps aux | grep -e '%s' | grep -v grep | awk '{print $2}'| awk '{print $2}'" % script_name)
    if l[1]:
        logger.info("process '%s' is already running, exiting now" % script_name)
        sys.exit(0);

"""Insert or update a liquidation record."""
def gotRek(rekt_key, symbol, qty, price, position, side, db_path="rekt.sqlite"):
    rc = False
    msg = []
    table_name = 'rekkage'
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute(
            "SELECT * FROM {tn} WHERE {idf}='{rekt_key}'".format(
                tn=table_name, idf='rekt_key', rekt_key=rekt_key
            )
        )
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
                            "UPDATE Rekkage SET rekt_qty = %s WHERE rekt_key = '%s' "
                            % (qty, rekt_key)
                        )
                    logger.info(
                        "Rekkord %s has been updated from %s to %s "
                        % (rekt_key, row[2], qty)
                    )
                    msg = (
                        "Liquidation %s order for %s reduced size from %s to %s"
                        % (side, symbol, row[2], qty)
                    )
                    WriteRekage([msg])
                except BaseException:
                    logger.error(format_exc())
        else:
            logger.info("Rek %s does NOT exist" % rekt_key)
            try:
                with conn:
                    c.execute(
                        "INSERT INTO {tn} (rekt_key,rekt_symbol,rekt_qty,rekt_price,rekt_position,rekt_side,rekt_ts) VALUES ('{rekt_key}','{rekt_symbol}',{rekt_qty},{rekt_price},'{rekt_position}','{rekt_side}',(CURRENT_TIMESTAMP))".format(
                            tn=table_name,
                            rekt_key=rekt_key,
                            rekt_symbol=symbol,
                            rekt_qty=qty,
                            rekt_price=price,
                            rekt_position=position,
                            rekt_side=side,
                        )
                    )
                    cur = conn.cursor()
                    cur.execute(
                        "SELECT * FROM {tn} WHERE {idf}='{rekt_key}'".format(
                            tn=table_name, idf='rekt_key', rekt_key=rekt_key
                        )
                    )
                    for row in cur:
                        logger.info("Rekkord '%s' has been Added " % row[0])
            except BaseException:
                logger.error(format_exc())

    return rc

"""Fetch liquidation information from BitMEX."""
def getRekage(db_path="rekt.sqlite"):

   msgs = []
   url = base_url + "order/liquidations"
   
   try:
     r = requests.get(url)
   except BaseException as ex:
     logger.error(format_exc())
     return ""   

   if r.status_code != 200:
      logger.error( "\nError %s while calling URL %s:\n" % (r.status_code,url))
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
          rc = gotRek(rek["orderID"], rek["symbol"], rek["leavesQty"], rek["price"], position, rek["side"], db_path=db_path)
          if not rc and float(rek["leavesQty"]) > 0:
             msgs.append("Liquidated %s position on %s. Limit %s order for %s @ %s created on www.bitmex.com" % (position,rek["symbol"],rek["side"],rek["leavesQty"],rek["price"]))
   return msgs

"""Send liquidation messages to Twitter."""
def WriteRekage(msgs):

   if msgs is None or len(msgs) == 0: 
     return

   # Consumer keys and access tokens
   # Read credentials from environment variables
   app_key             = os.getenv('TWITTER_APP_KEY')
   app_secret          = os.getenv('TWITTER_APP_SECRET')
   access_token        = os.getenv('TWITTER_ACCESS_TOKEN')
   access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

   auth = tweepy.OAuthHandler(app_key,app_secret)
   auth.set_access_token(access_token,access_token_secret)
   api = tweepy.API(auth)
   for msg in msgs:
      try:
         logger.info("Sending twitter update '%s' " % msg)
         api.update_status(msg)
      except BaseException as ex:
         logger.error(format_exc())

if __name__ == "__main__":

   logger = SetupLogging()
   RunOnce()
   logger.info('Starting RektBitmex ...')
   init_rekkage_db()
   init_pid_db()
   SLEEPTIME = 5 # seconds

   run = None    
   while run != 'n':
      logger.info("Updating Rekt List ...")
      rekts = getRekage()
      if rekts:
         WriteRekage(rekts)
      time.sleep(SLEEPTIME) 
   logger.info('Closing RektBitmex ...')
