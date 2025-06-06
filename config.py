#!/usr/bin/env python
# encoding: utf-8
"""Application configuration."""

import os

# Allow overriding the BitMEX API base URL via environment variable
base_url = os.getenv("BITMEX_BASE_URL", "https://www.bitmex.com/api/v1/")
