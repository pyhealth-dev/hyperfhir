import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr

from .base import Base

__author__ = "Md Nazrul Islam >"


class ResourceTransactionModel(Base):

    id = sa.Column("id", sa.Integer, primary_key=True, autoincrement=True)
    # ${fhir_release}_{resource_type}_{resource_id(hex)}
    index_id = sa.Column("index_id", sa.String(127), nullable=False)
    resource_id = sa.Column("resource_id", sa.CHAR(36), nullable=False, index=True)
    status = sa.Column(
        "status",
        sa.Enum(
            "created",
            "updated",
            "deleted",
            "recreated",
            "archived",
            name="resource_transaction_status",
        ),
        index=True,
    )
    resource_type = sa.Column(
        "resource_type", sa.String(64), nullable=False, index=True
    )
    resource_version = sa.Column("resource_version", sa.String(8), nullable=False)
    resource = sa.Column("resource", JSONB, nullable=False)
    fhir_version = sa.Column("fhir_version", sa.String(8), nullable=False)
    timestamp = sa.Column(
        "timestamp",
        sa.DateTime(timezone=True),
        onupdate=datetime.datetime.utcnow(),
        default=datetime.datetime.utcnow(),
    )

    @declared_attr
    def __table_args__(cls):
        """ """
        return (sa.UniqueConstraint("resource_id", "resource_type"),)


class ResourceHistoryModel(Base):

    id = sa.Column("id", sa.BIGINT, primary_key=True)
    txid = sa.Column("txid", sa.Integer, nullable=False)
    status = sa.Column(
        "status",
        sa.Enum(
            "created",
            "updated",
            "deleted",
            "recreated",
            "archived",
            name="resource_transaction_status",
        ),
    )
    resource_version = sa.Column("resource_version", sa.String(8), nullable=False)
    resource_id = sa.Column("resource_id", sa.CHAR(36), nullable=False, index=True)
    fhir_version = sa.Column("fhir_version", sa.String(8), nullable=False)
    resource_type = sa.Column(
        "resource_type", sa.String(64), nullable=False, index=True
    )
    resource = sa.Column("resource", JSONB, nullable=False)
    next_txid = sa.Column("next_txid", sa.Integer, nullable=True)
    pre_txid = sa.Column("pre_txid", sa.Integer, nullable=True)
    timestamp = sa.Column("timestamp", sa.DateTime(timezone=True), default=None)
