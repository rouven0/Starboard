"Blueprint file containing the guide command and its component handlers"
# pylint: disable=unused-argument
from os import listdir
from flask_discord_interactions import DiscordInteractionsBlueprint, Message, Embed
from flask_discord_interactions.models.component import ActionRow, Button, SelectMenu, SelectMenuOption
from flask_discord_interactions.models.option import CommandOptionType, Option
from flask_discord_interactions.models.embed import Media

import config


guide_bp = DiscordInteractionsBlueprint()


@guide_bp.command(
    options=[
        Option(
            name="topic",
            description="The topic you want to read about.",
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
    return Message(embed=get_guide_embed(topic), components=get_guide_selects())


@guide_bp.custom_handler(custom_id="guide_topic")
def guide_topic(ctx):
    """Handler for the topic select"""
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
        ),
        ActionRow(
            components=[
                Button(
                    label="Add starboard to your server",
                    style=5,
                    url=(
                        "https://discord.com/api/oauth2/authorize?client_id=966294455726506035"
                        "&redirect_uri=https%3A%2F%2Fstarboard.rfive.de%2Fapi%2Fsetup&response_type=code"
                        "&scope=webhook.incoming%20applications.commands"
                    ),
                )
            ]
        ),
    ]
    return selects
