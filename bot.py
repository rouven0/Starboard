# pylint: disable=unused-argument, missing-module-docstring
import sys
from os import getenv
from datetime import datetime

import logging
import requests

from dotenv import load_dotenv

from flask import Flask, request, render_template
from flask_discord_interactions import DiscordInteractions
from flask_discord_interactions.models.embed import Author, Embed, Field, Footer
from flask_discord_interactions.models.message import Message

import config

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
    "Message starring context menu command"
    if message.author.id == app.config["DISCORD_CLIENT_ID"]:
        return Message("You can't star messages from starboard,", ephemeral=True)
    r = requests.post(
        "TODO: replace this",
        json=Message(
            embed=Embed(
                author=Author(
                    name=f"{message.author.username}#{message.author.discriminator}",
                    icon_url=message.author.avatar_url,
                ),
                description=message.content
                if message.content
                else message.embeds[0].description
                if message.embeds and message.embeds[0].description
                else None,
                footer=Footer(text=message.id),
                timestamp=datetime.utcnow().isoformat(),
                color=config.EMBED_COLOR,
                fields=[
                    Field(
                        name="Jump to message",
                        value=(
                            "[click here]"
                            f"(https://discord.com/channels/{ctx.guild_id}/{ctx.channel_id}/{message.id})"
                        ),
                    )
                ],
            ),
        ).dump()["data"],
    )
    r.raise_for_status()

    return "message starred"


@app.route("/setup")
def webhook():
    "Setup route that gets the webhook from the discord api"
    data = {
        "client_id": getenv("DISCORD_CLIENT_ID", default=""),
        "client_secret": getenv("DISCORD_CLIENT_SECRET", default=""),
        "grant_type": "authorization_code",
        "code": request.args.get("code"),
        "redirect_uri": "https://starboard.rfive.de/api/setup",
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post("https://discord.com/api/v10/oauth2/token", data=data, headers=headers)
    r.raise_for_status()

    return render_template("./setup_success.html")


if "--update" in sys.argv:
    discord.update_commands(guild_id=830928381100556338)
    sys.exit()

if "--deploy" in sys.argv:
    discord.update_commands()
    sys.exit()


discord.set_route("/interactions")

if __name__ == "__main__":
    app.run(port=9200, debug=True)
