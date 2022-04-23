# pylint: disable=attribute-defined-outside-init
"""
Discord servers
"""
from dataclasses import dataclass
from resources import database


@dataclass
class Guild:
    """
    :ivar str id: Internal guild id
    :ivar str webhook_id: id of the webhook used to send messages to discord
    :ivar str webhook_token: token of the webhook used to send messages to discord
    :ivar int required_stars: stars required to send the message
    :ivar int flags: flags of the guild

    Flag documentation
    ^^^^^^^^^^^^^^^^^^
        1 << 0: Self stars allowed
        1 << 1: Delete own messages after sending
    """

    id: str
    webhook_id: str
    webhook_token: str
    required_stars: int = 3
    flags: int = 0

    def __iter__(self):
        self._n = 0
        return self

    def __next__(self):
        if self._n < len(vars(self)) - 1:
            attr = list(vars(self).keys())[self._n]
            self._n += 1
            return self.__getattribute__(attr)
        raise StopIteration

    @property
    def self_stars_allowed(self):
        """
        :return: True if self stars are allowed
        :rtype: bool
        """
        return bool(self.flags & 1 << 0)

    @property
    def delete_own_messages(self):
        """
        :return: True if own messages should be deleted
        :rtype: bool
        """
        return bool(self.flags & 1 << 1)


def exists(id: str) -> bool:
    """
    Checks if a guild is found in the database

    :param str name: A name to check
    :return: A bool defining whether that guild exists
    """
    database.cur.execute("SELECT * FROM guilds WHERE id=%s", (id,))
    if len(database.cur.fetchall()) == 1:
        return True
    return False


def get(id: str) -> Guild:
    """
    Gets a guild from the database

    :param str id: The desired guild's id, can be None
    :raises GuildNotFound: In case a guild with this name doesn't exist
    :return: The desired guild
    """
    if not exists(id):
        raise GuildNotFound()
    database.cur.execute("SELECT * FROM guilds WHERE id=%s", (id,))
    record = database.cur.fetchone()
    guild = Guild(**record)
    return guild


def get_all() -> list[Guild]:
    """
    :return: A list of all registered guilds
    """
    database.cur.execute("SELECT * from guilds")
    guilds = []
    for record in database.cur.fetchall():
        guilds.append(Guild(**record))
    return guilds


def insert(guild: Guild):
    """
    Add a new guild

    :param Guild guild: The guild to insert
    :return: The guild's id
    """
    attrs = vars(guild)
    placeholders = ", ".join(["%s"] * len(attrs))
    columns = ", ".join(attrs.keys())
    sql = f"INSERT INTO guilds ({columns}) VALUES ({placeholders})"
    print(sql)
    print(tuple(guild))
    database.cur.execute(sql, tuple(guild))
    database.con.commit()


def update(
    guild: Guild, webhook_id: str = None, webhook_token: str = None, required_stars: int = None, flags: int = None
) -> None:
    """
    Updates a guild in the database

    Same as in players, not documented until fixed
    """
    if webhook_id is not None:
        database.cur.execute("UPDATE guilds SET webhook_id=%s WHERE id=%s", (webhook_id, guild.id))
        guild.webhook_id = webhook_id
    if webhook_token is not None:
        database.cur.execute("UPDATE guilds SET webhook_token=%s WHERE id=%s", (webhook_token, guild.id))
        guild.webhook_token = webhook_token
    if required_stars is not None:
        database.cur.execute("UPDATE guilds SET required_stars=%s WHERE id=%s", (required_stars, guild.id))
        guild.required_stars = required_stars
    if flags is not None:
        database.cur.execute("UPDATE guilds SET flags=%s WHERE id=%s", (flags, guild.id))
        guild.flags = flags
    database.con.commit()


class GuildNotFound(Exception):
    """
    Exception raised when a guild isn't found in the database
    """

    def __str__(self) -> str:
        return "Requested guild was not found"
