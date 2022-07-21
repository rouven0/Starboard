"""Some configuration values"""
from os import getenv

LOG_FORMAT = "%(levelname)s [%(module)s.%(funcName)s]: %(message)s"
EMBED_COLOR = int("0x2f3136", 16)
BASE_URL = "https://discord.com/api/v10/webhooks"
DATABASE_ARGS = {
    "host": getenv("MYSQL_HOST"),
    "user": getenv("MYSQL_USER"),
    "passwd": getenv("MYSQL_PASSWORD"),
    "database": getenv("MYSQL_DATABASE"),
}


class I18n:
    "I18n configuration values"
    AVAILABLE_LOCALES = ["en-US", "de"]
    FILENAME_FORMAT = "{locale}{format}"
    FALLBACK = "en-US"
