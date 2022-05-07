# pylint: disable=unused-argument, missing-module-docstring
import logging
import sys
import threading
from datetime import datetime
from os import getenv
from time import sleep

import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request
from flask_discord_interactions import DiscordInteractions
from flask_discord_interactions.models.component import ActionRow, Button
from flask_discord_interactions.models.embed import (Author, Embed, Field,
                                                     Footer, Media)
from flask_discord_interactions.models.message import Message
from flask_discord_interactions.models.option import CommandOptionType, Option

import config
from guide import guide_bp
from resources import guilds, messages

load_dotenv("./.env")

app = Flask(__name__)
discord = DiscordInteractions(app)

app.config["DISCORD_CLIENT_ID"] = getenv("DISCORD_CLIENT_ID", default="")
app.config["DISCORD_PUBLIC_KEY"] = getenv("DISCORD_PUBLIC_KEY", default="")
app.config["DISCORD_CLIENT_SECRET"] = getenv("DISCORD_CLIENT_SECRET", default="")

if "--debug" in sys.argv:
    app.config["DONT_VALIDATE_SIGNATURE"] = True

logger = logging.getLogger()
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(config.LOG_FORMAT))
logger.addHandler(console_handler)

if "--remove-global" in sys.argv:
    discord.update_commands()
    sys.exit()


@discord.command(type=3, name="Star message")
def star(ctx, message: Message):
    """Message starring context menu command"""
    guild = guilds.get(ctx.guild_id)
    if int(message.id) < messages.max_timestamp():
        return Message("You can't star messages older than 30 days.", ephemeral=True)
    if message.author.id == app.config["DISCORD_CLIENT_ID"]:
        return Message("You can't star messages from starboard,", ephemeral=True)
    if messages.exists(message.id):
        return Message("This message already got stars, check your starboard channel to see it.", ephemeral=True)
    if ctx.author.id == message.author.id and guild.self_stars_allowed is False:
        return Message("You can't star your own messages.", ephemeral=True)
    messages.insert(messages.Message(id=message.id, star_users=ctx.author.id))
    try:
        attachment_url = request.json["data"]["resolved"]["messages"][message.id]["attachments"][0]["url"]
    except IndexError:
        attachment_url = None
    return Message(
        f"{ctx.author.username} starred a message:",
        embed=Embed(
            author=Author(
                name=f"{message.author.username}#{message.author.discriminator}", icon_url=message.author.avatar_url
            ),
            description=message.content
            if message.content
            else message.embeds[0].description
            if message.embeds and message.embeds[0].description
            else "",
            footer=Footer("Click the button to add a star"),
            color=config.EMBED_COLOR,
            image=Media(url=attachment_url) if attachment_url else None,
        ),
        components=[
            ActionRow(
                components=[
                    Button(label="1", emoji={"name": "⭐", "id": None}, custom_id=["star", message.id, 1], style=2)
                ]
            )
        ],
    )


@discord.custom_handler(custom_id="star")
def star_button(ctx, message_id, stars: int):
    """Star button handler"""
    guild = guilds.get(ctx.guild_id)
    message = messages.get(message_id)
    if int(message_id) < messages.max_timestamp():
        return Message("You can't star messages older than 30 days.", ephemeral=True)
    if ctx.author.id in message.star_users:
        return Message("You can't star a message twice.", ephemeral=True)
    if message.sent:
        return Message("This message was already sent to the starboard channel.", ephemeral=True)
    if ctx.author.id == ctx.message.author.id and not guild.self_stars_allowed:
        return Message("You can't star your own messages.", ephemeral=True)
    message.add_star_user(ctx.author.id)
    embed = ctx.message.embeds[0]
    if stars + 1 < guild.required_stars:
        embed.footer = Footer("Click the button to add a star")
        return Message(
            f"{ctx.author.username} starred a message:",
            embed=embed,
            components=[
                ActionRow(
                    components=[
                        Button(
                            label=str(stars + 1),
                            emoji={"name": "⭐", "id": None},
                            custom_id=["star", message_id, stars + 1],
                            style=2,
                        )
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
    embed.footer = Footer(message_id)
    embed.timestamp = datetime.utcnow().isoformat()
    embed.fields = [
        {
            "name": "Jump to message",
            "value": f"[click here](https://discord.com/channels/{ctx.guild_id}/{ctx.channel_id}/{message_id})",
        }
    ]

    r = requests.post(
        f"{config.BASE_URL}/{guild.webhook_id}/{guild.webhook_token}",
        json=Message(
            embed=embed,
        ).dump()["data"],
    )
    message.mark_sent()
    r.raise_for_status()

    return Message(
        f"{ctx.author.username} starred a message:",
        embed=Embed(
            author=embed.author,
            description=ctx.message.embeds[0].description,
            footer=Footer("Message was sent to the starboard!"),
            color=config.EMBED_COLOR,
            image=embed.image,
        ),
        components=[
            ActionRow(
                components=[
                    Button(
                        label=str(stars + 1),
                        emoji={"name": "⭐", "id": None},
                        custom_id=["star", stars + 1],
                        style=2,
                        disabled=True,
                    )
                ]
            )
        ],
        update=True,
    )


@discord.command(
    default_member_permissions=32,
    options=[
        Option(
            name="stars",
            type=CommandOptionType.INTEGER,
            description="The amount of stars required to send the message.",
            min_value=2,
        ),
        Option(
            name="allow_self_stars",
            type=CommandOptionType.BOOLEAN,
            description="Whether or not to allow users to star their own messages.",
        ),
        Option(
            name="delete_message",
            type=CommandOptionType.BOOLEAN,
            description="Whether or not to delete the interaction response after starring and sending the message.",
        ),
    ],
)
def settings(ctx, stars: int = None, allow_self_stars: bool = None, delete_message: bool = None):
    """Set up starboard."""
    guild = guilds.get(ctx.guild_id)
    if stars:
        guilds.update(guild, required_stars=stars)
    if allow_self_stars is not None:
        guild.set_self_stars_allowed(allow_self_stars)
    if delete_message is not None:
        guild.set_delete_own_messages(delete_message)
    return Message(
        "Settings successfully updated.",
        embed=Embed(
            fields=[
                Field("Required stars", str(guild.required_stars)),
                Field("Allow self stars", str(guild.self_stars_allowed)),
                Field("Delete interaction response", str(guild.delete_own_messages)),
            ],
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
    r = requests.post("https://discord.com/api/v10/oauth2/token", data=data, headers=headers)
    try:
        r.raise_for_status()
    except requests.HTTPError:
        return "Error while setting up", 500
    webhook = r.json()["webhook"]
    if not guilds.exists(webhook["guild_id"]):
        guilds.insert(guilds.Guild(id=webhook["guild_id"], webhook_id=webhook["id"], webhook_token=webhook["token"]))
        msg = "Your webhook has been created"
    else:
        guilds.update(guilds.get(webhook["guild_id"]), webhook_id=webhook["id"], webhook_token=webhook["token"])
        msg = "Your webhook has been updated. The old webhook can now be deleted."

    return render_template("./setup_success.html", msg=msg)


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
