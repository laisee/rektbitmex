Rekt @ Bitmex bot

Runs under Python 2.7.X, not 3.X

Install required libs by using 'pip' tool

Libs are:

- requests
- tweepy

Set the following environment variables with your Twitter credentials to enable
posting to Twitter:

- `TWITTER_APP_KEY`
- `TWITTER_APP_SECRET`
- `TWITTER_ACCESS_TOKEN`
- `TWITTER_ACCESS_TOKEN_SECRET`

If these are not provided, comment out the call that sends Twitter updates.

All liquidations will be stored in sqllite local DB (see rekt.sqlite). Log file named rektrunner.log will capture calls to bitmex.com
Some code is included to ensure only one instance of the bot runs. Its not completed and doesn't make any difference to runtime.

Run the bot by executing command: "python rektrunner.py"
