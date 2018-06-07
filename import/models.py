import logging
import argparse
import asyncio

from sqlalchemy.orm import sessionmaker
# from sqlalchemy import Column, Integer, String, TIMESTAMP
# from sqlalchemy.dialects.postgresql import JSONB
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.schema import Sequence
from sqlalchemy import create_engine

# from aiopg.sa import create_engine as aiopg_engine
from sqlalchemy.engine.url import URL

# from sqlalchemy_utils.functions import database_exists
# from sqlalchemy_utils.functions import create_database
# from sqlalchemy_utils.functions import drop_database

from settings import config_auth


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

# Base = declarative_base()

Session = sessionmaker()

session = []


def make_conf(section):

    host = config_auth.get(section, "host")
    port = config_auth.get(section, "port")
    db = config_auth.get(section, "dbname")

    CONF = URL(
        drivername="postgresql",
        username=config_auth.get(section, "user"),
        password=config_auth.get(section, "password"),
        host=host,
        port=port,
        database=db,
    )

    log.info(f"Database config {host}:{port}:{db}")
    return CONF
