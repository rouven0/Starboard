# pylint: disable=unused-argument, missing-module-docstring, wrong-import-position
import logging
import sys
import threading
from datetime import datetime
from os import getenv
from time import sleep

import config
import i18n
import requests
from flask import Flask, redirect, request
from flask_discord_interactions import DiscordInteractions
from flask_discord_interactions.models.component import ActionRow, Button
from flask_discord_interactions.models.embed import Author, Embed, Field, Footer, Media
from flask_discord_interactions.models.message import Message
from flask_discord_interactions.models.option import CommandOptionType, Option
from i18n import set as set_i18n
from i18n import t
from resources import guilds, messages
from utils import get_localizations, log_command

i18n.set("filename_format", config.I18n.FILENAME_FORMAT)
i18n.set("fallback", config.I18n.FALLBACK)
i18n.set("available_locales", config.I18n.AVAILABLE_LOCALES)
i18n.set("skip_locale_root_data", True)

i18n.load_path.append("./locales")

# ugly thing I have to do to support nested locales
for locale in config.I18n.AVAILABLE_LOCALES:
    logging.info("Initialized locale %s", locale)
    i18n.t("name", locale=locale)
from guide import guide_bp

app = Flask(__name__)
discord = DiscordInteractions(app)

app.config["DISCORD_CLIENT_ID"] = getenv("DISCORD_CLIENT_ID", default="")
app.config["DISCORD_PUBLIC_KEY"] = getenv("DISCORD_PUBLIC_KEY", default="")
app.config["DISCORD_CLIENT_SECRET"] = getenv("DISCORD_CLIENT_SECRET", default="")

if "--debug" in sys.argv:
    app.config["DONT_VALIDATE_SIGNATURE"] = True

logger = logging.getLogger()
logger.setLevel(logging.INFO)

logger.handlers.clear()
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(config.LOG_FORMAT))
logger.addHandler(console_handler)


if "--remove-global" in sys.argv:
    discord.update_commands()
    sys.exit()


@app.errorhandler(guilds.GuildNotFound)
def guild_not_found(error: guilds.GuildNotFound):
    """
    Prompt the webhook selection again
    """
    return Message(
        embed=Embed(
            title=t("guild_not_found.title"),
            description=t("guild_not_found.body"),
            color=config.EMBED_COLOR,
            fields=[
                Field(name=t("guild_not_found.explanation.name"), value=t("guild_not_found.explanation.value")),
                Field(name=t("guild_not_found.warning.name"), value=t("guild_not_found.warning.value")),
            ],
        ),
        ephemeral=True,
        components=[
            ActionRow(
                components=[
                    Button(
                        style=5,
                        label=t("guild_not_found.button"),
                        url="https://discord.com/api/oauth2/authorize?client_id=966294455726506035&permissions=0&redirect_uri=https%3A%2F%2Fstarboard.rfive.de%2Fapi%2Fsetup&response_type=code&scope=webhook.incoming",
                    )
                ]
            )
        ],
    ).dump()


@discord.command(
    type=3, name="Star message", name_localizations=get_localizations("commands.star_context.name"), dm_permission=False
)
def star(ctx, message: Message):
    """Message starring context menu command"""
    set_i18n("locale", ctx.locale)
    log_command(ctx)
    guild = guilds.get(ctx.guild_id)
    if int(message.id) < messages.max_timestamp():
        return Message(t("errors.too_old"), ephemeral=True)
    if message.author.id == app.config["DISCORD_CLIENT_ID"]:
        return Message(t("errors.starboard_message"), ephemeral=True)
    if messages.exists(message.id):
        return Message(t("errors.message_exists"), ephemeral=True)
    if ctx.author.id == message.author.id and guild.self_stars_allowed is False:
        return Message(t("errors.self_star"), ephemeral=True)
    messages.insert(messages.Message(id=message.id, star_users=ctx.author.id))
    try:
        attachment_url = request.json["data"]["resolved"]["messages"][message.id]["attachments"][0]["url"]
    except IndexError:
        attachment_url = None
    set_i18n("locale", ctx.guild_locale)
    return Message(
        t("message.author", author=ctx.author.username),
        embeds=[
            Embed(
                author=Author(
                    name=f"{message.author.username}#{message.author.discriminator}", icon_url=message.author.avatar_url
                ),
                description=message.content,
                footer=Footer(t("message.footer")),
                color=config.EMBED_COLOR,
                image=Media(url=attachment_url) if attachment_url else None,
            )
        ]
        + message.embeds,
        components=[
            ActionRow(
                components=[
                    Button(label="1", emoji={"name": "⭐", "id": None}, custom_id=["star", message.id, 1], style=2),
                    Button(
                        label=t("message.jump"),
                        style=5,
                        url=f"https://discord.com/channels/{ctx.guild_id}/{ctx.channel_id}/{message.id}",
                    ),
                ]
            )
        ],
    )


@discord.custom_handler(custom_id="star")
def star_button(ctx, message_id, stars: int):
    """Star button handler"""
    set_i18n("locale", ctx.locale)
    guild = guilds.get(ctx.guild_id)
    message = messages.get(message_id)
    if int(message_id) < messages.max_timestamp():
        return Message(t("errors.too_old"), ephemeral=True)
    if ctx.author.id in message.star_users:
        return Message(t("errors.starred_twice"), ephemeral=True)
    if message.sent:
        return Message(t("errors.starboard_message"), ephemeral=True)
    if ctx.author.id == ctx.message.author.id and not guild.self_stars_allowed:
        return Message(t("errors.self_star"), ephemeral=True)
    set_i18n("locale", ctx.guild_locale)
    message.add_star_user(ctx.author.id)
    embeds = ctx.message.embeds
    if stars + 1 < guild.required_stars:
        embeds[0].footer = Footer(t("message.footer"))
        return Message(
            t("message.author", author=ctx.author.username),
            embeds=embeds,
            components=[
                ActionRow(
                    components=[
                        Button(
                            label=str(stars + 1),
                            emoji={"name": "⭐", "id": None},
                            custom_id=["star", message_id, stars + 1],
                            style=2,
                        ),
                        Button(
                            label=t("message.jump"),
                            style=5,
                            url=f"https://discord.com/channels/{ctx.guild_id}/{ctx.channel_id}/{message_id}",
                        ),
                    ]
                )
            ],
            update=True,
        )

    def delete_original():
        sleep(1)
        requests.delete(ctx.followup_url() + "/messages/@original").raise_for_status()

    if guild.delete_own_messages:
        threading.Thread(target=delete_original).start()
    embeds_starboard = embeds.copy()
    embeds_starboard[0].footer = Footer(message_id)
    embeds_starboard[0].timestamp = datetime.utcnow().isoformat()

    requests.post(
        f"{config.BASE_URL}/{guild.webhook_id}/{guild.webhook_token}",
        json=Message(
            embeds=embeds_starboard,
            components=[
                ActionRow(
                    components=[
                        Button(
                            label=t("message.jump"),
                            style=5,
                            url=f"https://discord.com/channels/{ctx.guild_id}/{ctx.channel_id}/{message_id}",
                        )
                    ]
                )
            ],
        ).dump()["data"],
    ).raise_for_status()
    message.mark_sent()

    return Message(
        t("message.author", author=ctx.author.username),
        embeds=embeds,
        components=[
            ActionRow(
                components=[
                    Button(
                        label=str(stars + 1),
                        emoji={"name": "⭐", "id": None},
                        custom_id=["star", stars + 1],
                        style=2,
                        disabled=True,
                    ),
                    Button(
                        label=t("message.jump"),
                        style=5,
                        url=f"https://discord.com/channels/{ctx.guild_id}/{ctx.channel_id}/{message_id}",
                    ),
                ]
            )
        ],
        update=True,
    )


@discord.command(
    name_localizations=get_localizations("commands.settings.name"),
    description_localizations=get_localizations("commands.settings.description"),
    default_member_permissions=32,
    dm_permission=False,
    options=[
        Option(
            name="stars",
            name_localizations=get_localizations("commands.settings.stars.name"),
            type=CommandOptionType.INTEGER,
            description="The amount of stars required to send the message.",
            description_localizations=get_localizations("commands.settings.stars.description"),
            min_value=2,
        ),
        Option(
            name="allow_self_stars",
            name_localizations=get_localizations("commands.settings.allow_self_stars.name"),
            type=CommandOptionType.BOOLEAN,
            description="Whether or not to allow users to star their own messages.",
            description_localizations=get_localizations("commands.settings.allow_self_stars.description"),
        ),
        Option(
            name="delete_message",
            name_localizations=get_localizations("commands.settings.delete_message.name"),
            type=CommandOptionType.BOOLEAN,
            description="Whether or not to delete the interaction response after starring and sending the message.",
            description_localizations=get_localizations("commands.settings.delete_message.description"),
        ),
    ],
)
def settings(ctx, stars: int = None, allow_self_stars: bool = None, delete_message: bool = None):
    """Set up starboard."""
    set_i18n("locale", ctx.locale)
    log_command(ctx)
    guild = guilds.get(ctx.guild_id)
    if stars:
        guilds.update(guild, required_stars=stars)
    if allow_self_stars is not None:
        guild.set_self_stars_allowed(allow_self_stars)
    if delete_message is not None:
        guild.set_delete_own_messages(delete_message)
    return Message(
        t("settings.success"),
        embed=Embed(
            fields=[
                Field(t("settings.required_stars"), str(guild.required_stars)),
                Field(t("settings.allow_self_stars"), "✅" if guild.self_stars_allowed is True else "⛔"),
                Field(t("settings.delete_message"), "✅" if guild.delete_own_messages is True else "⛔"),
            ],
            color=config.EMBED_COLOR,
        ),
        ephemeral=True,
    )


@app.route("/setup")
def webhook():
    """Setup route that gets the webhook from the discord api"""
    data = {
        "client_id": getenv("DISCORD_CLIENT_ID", default=""),
        "client_secret": getenv("DISCORD_CLIENT_SECRET", default=""),
        "grant_type": "authorization_code",
        "code": request.args.get("code"),
        "redirect_uri": "https://starboard.rfive.de/api/setup",
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    auth_request = requests.post("https://discord.com/api/v10/oauth2/token", data=data, headers=headers)
    try:
        auth_request.raise_for_status()
    except requests.HTTPError as error:
        logging.error(error)
        return "Error while setting up", 500
    # pylint: disable = redefined-outer-name
    webhook = auth_request.json()["webhook"]
    if not guilds.exists(webhook["guild_id"]):
        guilds.insert(guilds.Guild(id=webhook["guild_id"], webhook_id=webhook["id"], webhook_token=webhook["token"]))
    else:
        guilds.update(guilds.get(webhook["guild_id"]), webhook_id=webhook["id"], webhook_token=webhook["token"])
    logging.info("Got authorized for guild %s", webhook["guild_id"])

    return redirect("https://discord.com/oauth2/authorized")


discord.register_blueprint(guide_bp)

if "--update" in sys.argv:
    discord.update_commands(guild_id=830928381100556338)
    sys.exit()

if "--deploy" in sys.argv:
    discord.update_commands()
    sys.exit()


discord.set_route("/interactions")

if __name__ == "__main__":
    app.run(port=9200, debug=True)
