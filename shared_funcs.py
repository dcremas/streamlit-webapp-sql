
def database_path(curr_db='finance'):
    from configparser import ConfigParser

    config = ConfigParser()
    config.read('config.ini')

    return (
        f"{config[curr_db]['dialect']}+{config[curr_db]['driver']}"
        f"://{config[curr_db]['username']}:{config[curr_db]['password']}"
        f"@{config[curr_db]['host']}:{config[curr_db]['port']}/{curr_db}"
    )


def connection_uri(curr_db='finance'):
    from configparser import ConfigParser

    config = ConfigParser()
    config.read('config.ini')

    return (
        f"postgresql"
        f"://{config[curr_db]['username']}:{config[curr_db]['password']}"
        f"@{config[curr_db]['host']}:{config[curr_db]['port']}/{curr_db}"
    )
