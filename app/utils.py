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


def log_command(ctx: Context) -> None:
    """
    Log a used command to stdout
    """
    logging.info(
        "%s#%s used /%s in guild %s with locale %s and guild locale %s.",
        ctx.author.username,
        ctx.author.discriminator,
        ctx.command_name,
        ctx.guild_id,
        ctx.locale,
        ctx.guild_id,
    )
