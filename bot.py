# pylint: disable=unused-argument, missing-module-docstring
import sys
from os import getenv
from datetime import datetime

import logging
from time import sleep
from flask_discord_interactions.models.component import ActionRow, Button
import requests
import threading

from dotenv import load_dotenv

from flask import Flask, request, render_template
from flask_discord_interactions import DiscordInteractions
from flask_discord_interactions.models.embed import Author, Embed, Field, Footer
from flask_discord_interactions.models.message import Message

import config
from resources import messages
from resources import guilds

from guide import guide_bp

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
    if int(message.id) < messages.max_timestamp():
        return Message("You can't star messages older than 30 days.", ephemeral=True)
    if message.author.id == app.config["DISCORD_CLIENT_ID"]:
        return Message("You can't star messages from starboard,", ephemeral=True)
    if messages.exists(message.id):
        return Message("This message already got stars, check your starboard channel to see it.", ephemeral=True)
    messages.insert(messages.Message(id=message.id, star_users=ctx.author.id))
    return Message(
        f"{message.author.username} starred a message:",
        embed=Embed(
            description=message.content
            if message.content
            else message.embeds[0].description
            if message.embeds and message.embeds[0].description
            else "",
            footer=Footer("Click the button to add a star"),
            color=config.EMBED_COLOR,
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
    guild = guilds.get(ctx.guild_id)
    message = messages.get(message_id)
    if int(message_id) < messages.max_timestamp():
        return Message("You can't star messages older than 30 days.", ephemeral=True)
    if ctx.author.id in message.star_users:
        return Message("You can't star a message twice.", ephemeral=True)
    if message.sent:
        return Message("This message was already sent to the starboard channel.", ephemeral=True)
    message.add_star_user(ctx.author.id)
    if stars + 1 < guild.required_stars:
        return Message(
            f"{ctx.author.username} starred a message:",
            embed=Embed(
                description=ctx.message.embeds[0].description,
                footer=Footer("Click the button to add a star"),
                color=config.EMBED_COLOR,
            ),
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

    r = requests.post(
        f"{config.BASE_URL}/{guild.webhook_id}/{guild.webhook_token}",
        json=Message(
            embed=Embed(
                author=Author(
                    name=f"{ctx.author.username}#{ctx.author.discriminator}",
                    icon_url=ctx.message.author.avatar_url,
                ),
                description=ctx.message.embeds[0].description,
                footer=Footer(text=ctx.message.id),
                timestamp=datetime.utcnow().isoformat(),
                color=config.EMBED_COLOR,
                fields=[
                    Field(
                        name="Jump to message",
                        value=(
                            "[click here]"
                            f"(https://discord.com/channels/{ctx.guild_id}/{ctx.channel_id}/{ctx.message.id})"
                        ),
                    )
                ],
            ),
        ).dump()["data"],
    )
    message.mark_sent()
    r.raise_for_status()

    return Message(
        f"{ctx.author.username} starred a message:",
        embed=Embed(
            description=ctx.message.embeds[0].description,
            footer=Footer("Message was sent to the starboard!"),
            color=config.EMBED_COLOR,
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
