import typing

from databases import Database, DatabaseURL

from ..core.config import get_database_dsn

DB_ = None


def get_db(
    url: typing.Union[str, DatabaseURL] = None, create: bool = False
) -> Database:
    """
    :param url:
    :param create:
    :return:
    """
    global DB_
    if DB_ is None or create is True:
        url = url or DatabaseURL(get_database_dsn())
        DB_ = Database(url=url)
    return DB_
