[![Python App](https://github.com/laisee/rektbitmex/actions/workflows/python-app.yml/badge.svg)](https://github.com/laisee/rektbitmex/actions/workflows/python-app.yml)

### Rekt @ Bitmex bot

Runs under Python 3.XX

Install required libs by using `pip` tool and the provided `requirements.txt`
file:

```
pip install -r requirements.txt
```

Libs are:

- requests
- tweepy

Add following environment variables with your Twitter credentials to a .env file to enable
posting to Twitter:

- `TWITTER_APP_KEY`
- `TWITTER_APP_SECRET`
- `TWITTER_ACCESS_TOKEN`
- `TWITTER_ACCESS_TOKEN_SECRET`

Without these variables the bot will run but will not attempt to publish updates
to Twitter.

If these are not provided, comment out the call that sends Twitter updates.

All liquidations will be stored in sqllite local DB (see rekt.sqlite). 

Log file named rektrunner.log will capture calls to bitmex.com

### Running Tests

Install the requirements and execute `pytest`:

```
pytest -q
```

### Database Schema

The SQLite database `rekt.sqlite` contains two tables:

* `rekkage` - stores liquidation events (`rekt_key`, `rekt_symbol`,
  `rekt_qty`, `rekt_price`, `rekt_position`, `rekt_side`, `rekt_ts`).
* `rekt_PID` - stores process IDs to avoid duplicate bot instances.

Run the bot by executing command: "python rektrunner.py"
