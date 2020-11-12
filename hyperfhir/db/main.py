import typing

from databases import Database, DatabaseURL

from ..core.config import get_database_dsn

DB_ = None


def get_db(url=None, create: bool = False) -> Database:
    """
    :param url:
    :param create:
    :return:
    """
    global DB_
    if DB_ is None or create is True:
        dsn = get_database_dsn()
        url = url or DatabaseURL(dsn)

        DB_ = Database(url=url)
    return DB_
