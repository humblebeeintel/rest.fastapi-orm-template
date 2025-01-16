# -*- coding: utf-8 -*-

## Internal modules
from api.bootstrap import create_app
from api import server
from api.logger import logger


app = create_app()


if __name__ == "__main__":
    logger.info(f"Starting server from '__main__.py'...")
    server.run(app="api.__main__:app")


__all__ = ["app"]