Rekt @ Bitmex bot

Install required libs by using 'pip' tool

Libs are:

- tweepy
- requests
- sqlite3
- commands

Update the Twitter keys and token values to enable posting to twitter, otherwise comment out the call to send Twitter update.

All liquidations will be stored in sqllite local DB (see rekt.sqlite). Log file named rektrunner.log will capture calls to bitmex.com
Some code is included to ensure only one instance of the bot runs. Its not completed and doesn't make any difference to runtime.

Run the bot by executing command: "python rektrunner.py"
