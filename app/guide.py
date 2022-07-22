"Blueprint file containing the guide command and its component handlers"
# pylint: disable=unused-argument
from os import listdir

import config
from flask_discord_interactions import DiscordInteractionsBlueprint, Embed, Message
from flask_discord_interactions.models.component import ActionRow, SelectMenu, SelectMenuOption
from flask_discord_interactions.models.embed import Media
from flask_discord_interactions.models.option import CommandOptionType, Option
from i18n import set as set_i18n

# from i18n import t
from utils import get_localizations, log_command

guide_bp = DiscordInteractionsBlueprint()


@guide_bp.command(
    name_localizations=get_localizations("commands.manual.name"),
    description_localizations=get_localizations("commands.manual.description"),
    options=[
        Option(
            name="topic",
            name_localizations=get_localizations("commands.manual.topic.name"),
            description="The topic you want to read about.",
            description_localizations=get_localizations("commands.manual.topic.description"),
            type=CommandOptionType.STRING,
            choices=[
                {"name": f[: f.find(".")].replace("_", " "), "value": f[: f.find(".")]}
                for f in sorted(listdir("./guide"))
            ],
        )
    ],
)
def manual(ctx, topic: str = "introduction") -> Message:
    """Get some informaton about starboard."""
    set_i18n("locale", ctx.locale)
    log_command(ctx)
    return Message(embed=get_guide_embed(topic), components=get_guide_selects())


@guide_bp.custom_handler(custom_id="guide_topic")
def guide_topic(ctx):
    """Handler for the topic select"""
    set_i18n("locale", ctx.locale)
    return Message(embed=get_guide_embed(ctx.values[0]), components=get_guide_selects(), update=True)


def get_guide_embed(topic: str) -> Embed:
    """Returns the fitting guide embed for a topic"""
    with open(f"./guide/{topic}.md", "r", encoding="utf8") as guide_file:
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


def get_guide_selects():
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
                        for f in sorted(listdir("./guide"))
                    ],
                    placeholder="Select a topic",
                )
            ]
        )
    ]
    return selects
