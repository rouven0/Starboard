# pylint: disable=attribute-defined-outside-init
"""
Discord servers
"""
from dataclasses import dataclass
from resources import database
from time import time


def max_timestamp() -> int:
    return int((time() - 30 * 24 * 60 * 60) * 1000.0 - 1420070400000) << 22


@dataclass
class Message:
    """
    :ivar str id: Internal message id
    :ivar int stars: stars of the message
    :ivar int flags: flags of the message
    :ivar str star_users: users who already starred

    Flag documentation
    ^^^^^^^^^^^^^^^^^^
        1 << 0: Message has been sent to starboard
    """

    id: str
    flags: int = 0
    star_users: str = ""

    def __iter__(self):
        self._n = 0
        return self

    def __next__(self):
        if self._n < len(vars(self)) - 1:
            attr = list(vars(self).keys())[self._n]
            self._n += 1
            return self.__getattribute__(attr)
        raise StopIteration

    def add_star_user(self, id: int) -> None:
        """
        Add a user to the star_users list
        """
        update(self, star_users=f"{self.star_users};{id}")

    def mark_sent(self) -> None:
        """
        Mark the message as sent to starboard
        """
        update(self, flags=self.flags | 1 << 0)

    @property
    def stars(self):
        return len(self.star_users.split(";"))

    @property
    def sent(self):
        return self.flags & 1 << 0


def exists(id: str) -> bool:
    """
    Checks if a message is found in the database

    :param str name: A name to check
    :return: A bool defining whether that message exists
    """
    database.cur.execute("SELECT * FROM messages WHERE id=%s", (id,))
    if len(database.cur.fetchall()) == 1:
        return True
    return False


def get(id: str) -> Message:
    """
    Gets a message from the database

    :param str id: The desired message's id, can be None
    :raises MessageNotFound: In case a message with this name doesn't exist
    :return: The desired message
    """
    if not exists(id):
        raise MessageNotFound()
    database.cur.execute("SELECT * FROM messages WHERE id=%s", (id,))
    record = database.cur.fetchone()
    message = Message(**record)
    return message


def get_all() -> list[Message]:
    """
    :return: A list of all registered messages
    """
    database.con.commit()
    database.cur.execute("SELECT * from messages")
    messages = []
    for record in database.cur.fetchall():
        messages.append(Message(**record))
    return messages


def insert(message: Message):
    """
    Add a new message

    :param Message message: The message to insert
    :return: The message's id
    """
    attrs = vars(message)
    placeholders = ", ".join(["%s"] * len(attrs))
    columns = ", ".join(attrs.keys())
    sql = f"INSERT INTO messages ({columns}) VALUES ({placeholders})"
    print(sql)
    print(tuple(message))
    database.cur.execute(sql, tuple(message))
    database.con.commit()


def update(message: Message, stars: int = None, flags: int = None, star_users: str = None) -> None:
    """
    Updates a message in the database

    Same as in players, not documented until fixed
    """
    if stars is not None:
        database.cur.execute("UPDATE messages SET stars=%s WHERE id=%s", (stars, message.id))
        message.stars = stars
    if flags is not None:
        database.cur.execute("UPDATE messages SET flags=%s WHERE id=%s", (flags, message.id))
        message.flags = flags
    if star_users is not None:
        database.cur.execute("UPDATE messages SET star_users=%s WHERE id=%s", (star_users, message.id))
        message.star_users = star_users
    database.con.commit()


def delete(message: Message) -> None:
    """
    Deletes a message from the database

    :param Message message: The message to delete
    """
    database.cur.execute("DELETE FROM messages WHERE id=%s", (message.id,))
    database.con.commit()


class MessageNotFound(Exception):
    """
    Exception raised when a message isn't found in the database
    """

    def __str__(self) -> str:
        return "Requested message was not found"
