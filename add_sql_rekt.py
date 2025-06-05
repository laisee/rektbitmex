import os
import sys
import json
import requests
import datetime
import tweepy
from time import gmtime, strftime
from exceptions import BaseException
from traceback import format_exc
import sqlite3
import logging

logger = logging.getLogger(__name__)


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
   print(' Connection() open in  Add Rekt SQLlite() ')
   rekt_count = 0
   try:
      c.execute('SELECT 1 FROM {tn}'.format(tn=table_name))
      rekt_count = c.fetchone()
   except sqlite3.OperationalError:
      pass
   except Exception:
      logger.error(format_exc())

   if rekt_count == 0:
      print("Creating new Rekkage table ... ")
      # Creating a new SQLite table with 1 column
      c.execute('CREATE TABLE {tn} ({nf} {ft} PRIMARY KEY, rekt_symbol TEXT, rekt_qty INTEGER, rekt_price REAL,rekt_side TEXT, rekt_position TEXT, rekt_ts TEXT)'.format(tn=table_name, nf=new_field, ft=field_type))
   else:
      print(" Table %s exists already" % table_name)

   # Committing changes and closing the connection to the database file
   conn.commit()
   conn.close

''' CHECK, STORE EACH LIQUIDATION '''
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
   except sqlite3.OperationalError:
      pass
   except Exception:
      logger.error(format_exc())

   if rekt_count == 0:
      print("Creating new PID table ... ")
      # Creating a new SQLite table with 1 column
      c.execute('CREATE TABLE {tn} ({nf} {ft} PRIMARY_KEY)'.format(tn=table_name, nf=new_field, ft=field_type))
   else:
      print(" Table %s exists already" % table_name)

   # Committing changes and closing the connection to the database file
   conn.commit()
   conn.close

if __name__ == "__main__":
   addRekt()
   addPID()
