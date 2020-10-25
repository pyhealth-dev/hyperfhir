"""Application Configuration"""
import pathlib
import os
from dotenv import load_dotenv


__author__ = "Md Nazrul Islam <email2nazrul@gmail.com>"


def lookup_env_file(create=True):
    """ """
    env_file = os.environ.get("HYPERFHIR-CONFIGURATION-FILE", None)
    if env_file is None:
        env_file = os.path.join(os.getcwd(), ".env")
    env_file = pathlib.Path(env_file)
    if not env_file.exists() and create:
        env_file.touch()
    elif not env_file.exists():
        raise LookupError(f"{env_file} doesn't found.")
    if not env_file.is_file():
        raise ValueError(f"{env_file} is not file.")
    return env_file


load_dotenv(lookup_env_file(True))

PROJECT_NAME = os.environ.get("PROJECT_NAME", "Hyper FHIR Server")
