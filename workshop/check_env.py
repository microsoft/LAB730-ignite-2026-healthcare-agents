"""Workshop environment check. Run: uv run workshop/check_env.py"""

import sys

import mcp  # noqa: F401
import numpy  # noqa: F401
import pandas  # noqa: F401
import PIL  # noqa: F401
import sklearn  # noqa: F401
import dotenv  # noqa: F401
import requests  # noqa: F401
import matplotlib  # noqa: F401
import ipykernel  # noqa: F401

print(f"Workshop env OK — Python {sys.version_info.major}.{sys.version_info.minor}")
