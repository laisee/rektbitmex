[![Python App](https://github.com/laisee/rektbitmex/actions/workflows/python-app.yml/badge.svg)](https://github.com/laisee/rektbitmex/actions/workflows/python-app.yml)

### Rekt @ Bitmex bot

Runs under Python 3.XX

Install required libs by using 'pip' tool

Libs are:

- requests
- tweepy

Add following environment variables with your Twitter credentials to a .env file to enable
posting to Twitter:

- `TWITTER_APP_KEY`
- `TWITTER_APP_SECRET`
- `TWITTER_ACCESS_TOKEN`
- `TWITTER_ACCESS_TOKEN_SECRET`

If these are not provided, comment out the call that sends Twitter updates.

All liquidations will be stored in sqllite local DB (see rekt.sqlite). 

Log file named rektrunner.log will capture calls to bitmex.com

Run the bot by executing command: "python rektrunner.py"
