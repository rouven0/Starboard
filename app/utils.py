"""
Some utility functions
"""
from flask_discord_interactions import Context
import i18n
import logging


def get_localizations(key: str) -> dict:
    """
    Returns all localizations for a string
    """
    localizations = {}
    for locale in i18n.get("available_locales"):
        localizations[locale] = i18n.t(key, locale=locale)
    return localizations
