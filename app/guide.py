"Blueprint file containing the guide command and its component handlers"
# pylint: disable=unused-argument
from os import listdir

import config
from flask_discord_interactions import DiscordInteractionsBlueprint, Embed, Message
from flask_discord_interactions.models.component import ActionRow, SelectMenu, SelectMenuOption
from flask_discord_interactions.models.embed import Media
from flask_discord_interactions.models.option import Choice, CommandOptionType, Option, Optional
from i18n import t, set as set_i18n

# from i18n import t
from utils import get_localizations, log_command

guide_bp = DiscordInteractionsBlueprint()


@guide_bp.command(
    name_localizations=get_localizations("commands.manual.name"),
    description_localizations=get_localizations("commands.manual.description"),
    options=[
        Option(
            name="language",
            name_localizations=get_localizations("commands.manual.language.name"),
            description="The language you want to read in.",
            description_localizations=get_localizations("commands.manual.language.description"),
            type=CommandOptionType.STRING,
            required=True,
            choices=[
                Choice(
                    name="English",
                    value="en-US",
                    name_localizations=get_localizations("commands.manual.language.english"),
                ),
                Choice(
                    name="German",
                    value="de",
                    name_localizations=get_localizations("commands.manual.language.german"),
                ),
            ],
        ),
        Option(
            name="topic",
            name_localizations=get_localizations("commands.manual.topic.name"),
            description="The topic you want to read about.",
            description_localizations=get_localizations("commands.manual.topic.description"),
            type=CommandOptionType.STRING,
            autocomplete=True,
        ),
    ],
)
def manual(ctx, language: str = None) -> Message:
    """Get some informaton about starboard."""
    used_locale = language if language else ctx.locale
    set_i18n("locale", used_locale)
    log_command(ctx)
    return Message(embed=get_guide_embed("intro", used_locale), components=get_guide_selects(used_locale))


@manual.autocomplete()
def manual_autocomplete(ctx, locale: Option, topic: Optional[Option] = None):
    set_i18n("locale", ctx.locale)
    # workaround since lib goes by order instead of name, topic is only None when locale option is skipped
    if topic is None:
        return [Choice(name=t("commands.manual.topic.locale_error"), value="error")]
    available_files = [
        Choice(name=f[: f.find(".")].replace("_", " "), value=f[: f.find(".")])
        for f in sorted(listdir(f"./guide/{locale.value}"))
    ]
    choices = []
    for choice in available_files:
        if topic.value in str.lower(choice.name):
            choices.append(choice)

    return choices


@guide_bp.custom_handler(custom_id="guide_topic")
def guide_topic(ctx):
    """Handler for the topic select"""
    set_i18n("locale", ctx.locale)
    return Message(embed=get_guide_embed(ctx.values[0]), components=get_guide_selects(), update=True)


def get_guide_embed(topic: str, locale: str) -> Embed:
    """Returns the fitting guide embed for a topic"""
    with open(f"./guide/{locale}/{topic}.md", "r", encoding="utf8") as guide_file:
        topic = str.lower(topic)
        image_url = guide_file.readline()
        guide_embed = Embed(
            title=f"{str.upper(topic[0])}{topic[1:]}".replace("_", " "),
            description=guide_file.read(),
            color=config.EMBED_COLOR,
        )
        if image_url.startswith("https"):
            guide_embed.image = Media(url=image_url)
        else:
            guide_embed.description = image_url + guide_embed.description
        return guide_embed


def get_guide_selects(locale: str):
    """Builder for the topic select"""
    selects = [
        ActionRow(
            components=[
                SelectMenu(
                    custom_id="guide_topic",
                    options=[
                        SelectMenuOption(
                            label=str.upper(f[:1]) + f[1 : f.find(".")].replace("_", " "), value=f[: f.find(".")]
                        )
                        for f in sorted(listdir(f"./guide/{locale}"))
                    ],
                    placeholder="Select a topic",
                )
            ]
        )
    ]
    return selects
