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

''' CHECK, STORE EACH Process ID '''
def addPID():
   print(' In Add PID SQLlite() ')
   sqlite_file = 'rekt.sqlite'    # name of the sqlite database file
   table_name = 'rekt_PID'  # name of the table to be created
   new_field = 'rekt_PID' # name of the column
   field_type = 'TEXT'  # column data type

   # Connecting to the database file
   conn = sqlite3.connect("rekt.sqlite")
   c = conn.cursor()
   print(' Connection() open in  Add PID SQLlite() ')
   rekt_count = 0
   try:
      c.execute('SELECT 1 FROM {tn}'.format(tn=table_name))
      rekt_count = c.fetchone()
   except:
      pass

   if rekt_count == 0:
      print("Creating new PID table ... ")
      # Creating a new SQLite table with 1 column
      c.execute('CREATE TABLE {tn} ({nf} {ft} PRIMARY_KEY)'.format(tn=table_name, nf=new_field, ft=field_type))
   else:
      print(" Table %s exists already" % table_name)

   # Committing changes and closing the connection to the database file
   conn.commit()
   conn.close

''' CHECK, STORE EACH LIQUIDATION '''
def addRekt():
   print(' In Add Rekt SQLlite() ')
   sqlite_file = 'rekt.sqlite'    # name of the sqlite database file
   table_name = 'rekkage'  # name of the table to be created
   new_field = 'rekt_key' # name of the column
   field_type = 'TEXT'  # column data type

   # Connecting to the database file
   conn = sqlite3.connect("rekt.sqlite")
   c = conn.cursor()
   rekt_count = 0
   try:
      c.execute('SELECT 1 FROM {tn}'.format(tn=table_name))
      rekt_count = c.fetchone()
   except:
      pass

   if rekt_count == 0:
      print("Creating new Rekkage table ... ")
      # Creating a new SQLite table with 1 column
      c.execute('CREATE TABLE {tn} ({nf} {ft} PRIMARY KEY, rekt_symbol TEXT, rekt_qty INTEGER, rekt_price REAL, rekt_position TEXT, rekt_side TEXT, rekt_ts TEXT)'.format(tn=table_name, nf=new_field, ft=field_type))
   else:
      print(" Table %s exists already" % table_name)

   # Committing changes and closing the connection to the database file
   conn.commit()
   conn.close


''' Setup logging with file, console output '''
def SetupLogging():
   # create logger with 'RektBitmex'
   logger = logging.getLogger('RektBitmex')
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

''' Run the process only once at a time '''
def RunOnce():
    script_name = os.path.basename(__file__)
    l = subprocess.getstatusoutput("ps aux | grep -e '%s' | grep -v grep | awk '{print $2}'| awk '{print $2}'" % script_name)
    if l[1]:
        logger.info("process '%s' is already running, exiting now" % script_name)
        sys.exit(0);

''' Check, Store each Liquidation '''
def gotRek(rekt_key, symbol, qty, price, position, side):
   rc = False
   msg = []
   table_name = 'rekkage'
   conn = sqlite3.connect("rekt.sqlite")
   c = conn.cursor()
   c.execute("SELECT * FROM {tn} WHERE {idf}='{rekt_key}'".format(tn=table_name,idf='rekt_key', rekt_key=rekt_key))
   row = c.fetchone()
   if row:
      logger.info("checking record %s " % rekt_key)
      rc = True 
      if qty < row[2]:
        logger.info("Rekkord %s has decreased open fill qty from %s to %s " % (rekt_key,row[2],qty))
        try:
          with conn:
            c.execute("UPDATE Rekkage SET rekt_qty = %s WHERE rekt_key = '%s' " % (qty,rekt_key))
          logger.info("Rekkord %s has been updated from %s to %s " % (rekt_key,row[2], qty))
          msg = "Liquidation %s order for %s reduced size from %s to %s" % (side,symbol,row[2],qty)
          WriteRekage([ msg ])
        except BaseException as ex:
          logger.error(format_exc())
   else:
      logger.info("Rek %s does NOT exist" % rekt_key)
      try:
        with conn:
          c.execute("INSERT INTO {tn} (rekt_key,rekt_symbol,rekt_qty,rekt_price,rekt_position,rekt_side,rekt_ts) VALUES ('{rekt_key}','{rekt_symbol}',{rekt_qty},{rekt_price},'{rekt_position}','{rekt_side}',(CURRENT_TIMESTAMP))".format(tn=table_name,rekt_key=rekt_key,rekt_symbol=symbol,rekt_qty=qty,rekt_price=price,rekt_position=position,rekt_side=side))
          cur = conn.cursor()
          cur.execute("SELECT * FROM {tn} WHERE {idf}='{rekt_key}'".format(tn=table_name, idf='rekt_key', rekt_key=rekt_key))
          for row in cur:
            logger.info("Rekkord '%s' has been Added " % row[0])
      except BaseException as ex:
        logger.error(format_exc())

   conn.close
   return rc

''' Get rekt details '''
def getRekage():

   msgs = []
   url = "https://www.bitmex.com/api/v1/order/liquidations"
   
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
      print(data)
      for rek in data:
          if rek["side"] == "Buy":
             position = "Short"
          else:
             position = "Long"
          rc = gotRek(rek["orderID"], rek["symbol"],rek["leavesQty"],rek["price"],position,rek["side"])
          if not rc and float(rek["leavesQty"]) > 0:
             msgs.append("Liquidated %s position on %s. Limit %s order for %s @ %s created on www.bitmex.com" % (position,rek["symbol"],rek["side"],rek["leavesQty"],rek["price"]))
   return msgs

''' Write Rekage details to Twitter using details from getRekage '''
def WriteRekage(msgs):

   if msgs is None or len(msgs) == 0: 
     return

   # Consumer keys and access tokens
   app_key             = 'ADD TWITTER APP KEY'
   app_secret          = 'ADD TWITTER APP SECRET'
   access_token        = 'ADD TWITTER ACCESS TOKEN'
   access_token_secret = 'ADD TWITTER ACCESS TOKEN SECRET'

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
   logger.info('Starting RektBitmex ...')
   addRekt()
   addPID()
   SLEEPTIME = 5 # seconds

   run = None    
   while run != 'n':
      logger.info("Updating Rekt List ...")
      rekts = getRekage()
      if rekts:
         WriteRekage(rekts)
      time.sleep(SLEEPTIME) 
   logger.info('Closing RektBitmex ...')
