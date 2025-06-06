[![Python App](https://github.com/laisee/rektbitmex/actions/workflows/python-app.yml/badge.svg)](https://github.com/laisee/rektbitmex/actions/workflows/python-app.yml)
[![Bandit Security Check](https://github.com/laisee/rektbitmex/actions/workflows/main.yml/badge.svg)](https://github.com/laisee/rektbitmex/actions/workflows/main.yml)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: CC0-1.0](https://img.shields.io/badge/License-CC0%201.0-lightgrey.svg)](https://creativecommons.org/publicdomain/zero/1.0/)
[![Coverage Status](https://codecov.io/gh/laisee/rektbitmex/branch/master/graph/badge.svg)](https://codecov.io/gh/laisee/rektbitmex)

# 💥 Rekt @ BitMEX Bot

`rektbitmex` tracks liquidation events on [BitMEX](https://www.bitmex.com) and stores
information about each event in a local SQLite database. When configured with
Twitter credentials it tweets a short summary of the liquidation.

---

## Features

- Polls the BitMEX `order/liquidations` API endpoint
- Persists liquidation information to `rekt.sqlite`
- Optional Twitter posting using Tweepy
- PID file handling to avoid multiple running instances
- Simple commands to initialise the database tables

## Requirements

- Python 3.8 or newer
- Dependencies listed in `requirements.txt`

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Initialise the database tables:

```bash
python add_sql_rekt.py
```

Run the bot:

```bash
python rektrunner.py
```

Set the following environment variables if you want the bot to tweet:
`TWITTER_APP_KEY`, `TWITTER_APP_SECRET`, `TWITTER_ACCESS_TOKEN` and
`TWITTER_ACCESS_TOKEN_SECRET`.

## Supported Versions

The project is actively tested with Python 3.8 and later.

## Database Schema

Two tables are created in `rekt.sqlite`:

- **rekkage**: stores liquidation events
  - `rekt_key` TEXT primary key
  - `rekt_symbol` TEXT
  - `rekt_qty` INTEGER
  - `rekt_price` REAL
  - `rekt_position` TEXT
  - `rekt_side` TEXT
  - `rekt_ts` TEXT (timestamp of insertion)
- **rekt_PID**: tracks the running process ID
  - `rekt_PID` TEXT primary key

## Configuration

`config.py` defines the BitMEX API base URL. The database path can be passed to
functions in `rektrunner.py` if you wish to store it elsewhere. Twitter
credentials are read from environment variables as noted above.

## Test Coverage

Unit tests are located in the `tests` directory and can be executed with
`pytest` and the `pytest-cov` plugin:

```bash
pytest --cov=./
```

There are four tests covering database initialisation, record insertion and the
basic helper functions. Coverage results are uploaded to [Codecov](https://codecov.io/gh/laisee/rektbitmex) and displayed in the badge above.
