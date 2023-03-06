"""Run the app with `python -m app`."""

import os

from aiohttp.web import run_app

from . import setup_app


app = setup_app(os.environ.get('CONFIG_PATH', 'config.yml'))
run_app(app)
