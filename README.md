Rekt @ Bitmex bot

Install required libs by using 'pip' tool

Libs are:

- tweepy
- requests
- sqlite3
- commands

Update the Twitter keys and token values to enable posting to twitter, otherwise comment out the call to send Twitter update.

All liquidations will be stored in sqllite local DB (see rekt.sqlite). Log file named rektrunner.log will capture calls to bitmex.com

Run the bot by executing this command: "python rektrunner.py"
