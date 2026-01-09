import os
from dotenv import load_dotenv


def database_path(curr_db='apple_weatherkit'):

    load_dotenv()

    dialect = os.getenv('dialect')
    driver = os.getenv('driver')
    username = os.getenv('username')
    password = os.getenv('password')
    host = os.getenv('host')
    port = os.getenv('port')
    curr_db = curr_db

    return f"{dialect}+{driver}://{username}:{password}@{host}:{port}/{curr_db}"


def connection_uri(curr_db='finance'):
    from configparser import ConfigParser

    config = ConfigParser()
    config.read('config.ini')

    return (
        f"postgresql"
        f"://{config[curr_db]['username']}:{config[curr_db]['password']}"
        f"@{config[curr_db]['host']}:{config[curr_db]['port']}/{curr_db}"
    )
