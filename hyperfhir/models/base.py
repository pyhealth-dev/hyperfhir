
from typing import Any

from sqlalchemy.ext.declarative import as_declarative, declared_attr

__author__ = "Md Nazrul Islam<email2nazrul@gmail.com>"


@as_declarative()
class Base:

    id: Any

    @declared_attr
    def __tablename__(cls) -> str:
        """ """
        return f"{cls.__name__.lower()[:-5]}_table"
