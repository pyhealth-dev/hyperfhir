"""Application Configuration"""
import os
import pathlib
from urllib.parse import urlencode

from dotenv import find_dotenv
from dotenv import load_dotenv as _load_dotenv

__author__ = "Md Nazrul Islam <email2nazrul@gmail.com>"


def load_dotenv(create=True):
    """ """
    auto_discover = find_dotenv()
    provided_env_file = os.environ.get("HYPERFHIR_CONFIGURATION_FILE", "")
    if provided_env_file == "" and auto_discover == "":
        env_file = os.path.join(os.getcwd(), ".env")
    elif provided_env_file:
        env_file = provided_env_file
    else:
        env_file = auto_discover

    env_file = pathlib.Path(env_file)
    if not env_file.exists() and create:
        env_file.touch()
    elif not env_file.exists():
        raise LookupError(f"{env_file} doesn't found.")
    if not env_file.is_file():
        raise ValueError(f"{env_file} is not file.")
    override = auto_discover != "" and provided_env_file != ""
    _load_dotenv(dotenv_path=env_file, override=override)


load_dotenv(True)

PROJECT_NAME = os.environ.get("PROJECT_NAME", "Hyper FHIR Server")


def get_database_dsn() -> str:
    """ """
    DB_DSN = "postgresql://{user}:{password}@{server}:{port}/{db}".format(
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        server=os.getenv("POSTGRES_SERVER"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        db=os.getenv("POSTGRES_DB"),
    )
    return DB_DSN


def get_elasticsearch_dsn() -> str:
    """ """
    http_auth = ""
    if os.getenv("ELASTICSEARCH_USER"):
        http_auth = "{0}:{1}".format(
            os.getenv("ELASTICSEARCH_USER"), os.getenv("POSTGRES_PASSWORD", None) or ""
        )

    ES_DSN = "es://{http_auth}@{server}:{port}/".format(
        http_auth=http_auth,
        server=os.getenv("ELASTICSEARCH_SERVER_HOST"),
        port=os.getenv("ELASTICSEARCH_SERVER_PORT", "9200"),
    )
    options = {"use_ssl": os.getenv("ELASTICSEARCH_OPT_USE_SSL", "NO")}

    if os.environ.get("ELASTICSEARCH_OPT_URL_PREFIX", None):
        options["url_prefix"] = os.environ.get("ELASTICSEARCH_OPT_URL_PREFIX", None)

    if os.environ.get("ELASTICSEARCH_OPT_SNIFF_ON_START", None):
        options["sniff_on_start"] = os.environ.get("ELASTICSEARCH_OPT_SNIFF_ON_START")

    if os.environ.get("ELASTICSEARCH_OPT_SNIFFER_TIMEOUT", None):
        options["sniffer_timeout"] = os.environ.get("ELASTICSEARCH_OPT_SNIFFER_TIMEOUT")

    if os.environ.get("ELASTICSEARCH_OPT_SNIFF_TIMEOUT", None):
        options["sniff_timeout"] = os.environ.get("ELASTICSEARCH_OPT_SNIFF_TIMEOUT")

    if os.environ.get("ELASTICSEARCH_OPT_SNIFF_ON_CONN_FAIL", None):
        options["sniff_on_connection_fail"] = os.environ.get(
            "ELASTICSEARCH_OPT_SNIFF_ON_CONN_FAIL", None
        )

    if os.environ.get("ELASTICSEARCH_OPT_MAX_RETRIES", None):
        options["max_retries"] = os.environ.get("ELASTICSEARCH_OPT_MAX_RETRIES")

    if os.environ.get("ELASTICSEARCH_OPT_RETRY_ON_STATUS", None):
        options["retry_on_status"] = os.environ.get("ELASTICSEARCH_OPT_RETRY_ON_STATUS")

    if os.environ.get("ELASTICSEARCH_OPT_RETRY_TIME_OUT", None):
        options["retry_on_timeout"] = os.environ.get("ELASTICSEARCH_OPT_RETRY_TIME_OUT")

    if os.environ.get("ELASTICSEARCH_OPT_SERIALIZER", None):
        options["serializer"] = os.environ.get("ELASTICSEARCH_OPT_SERIALIZER", None)

    if os.environ.get("ELASTICSEARCH_OPT_HOST_INFO_CALLBACK", None):
        options["host_info_callback"] = os.environ.get(
            "ELASTICSEARCH_OPT_HOST_INFO_CALLBACK"
        )

    if len(options) > 0:
        ES_DSN = "{0}?{1}".format(ES_DSN, urlencode(options))

    return ES_DSN


ELASTICSEARCH_STATIC_MAPPINGS = (
    pathlib.Path(os.path.abspath(__file__)).parent.parent
    / "static"
    / "HL7"
    / "FHIR"
    / "mappings"
)
