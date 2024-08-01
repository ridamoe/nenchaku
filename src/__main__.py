import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve

from . import app

asyncio.run(serve(app, Config()))