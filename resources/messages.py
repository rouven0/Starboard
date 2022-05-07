# pylint: disable=attribute-defined-outside-init
"""
Discord servers
"""
from dataclasses import dataclass
from time import time

from resources import database


def max_timestamp() -> int:
    """Pseudo id from a message 30 days ago"""
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
        """Number of stars a message has"""
        return len(self.star_users.split(";"))

    @property
    def sent(self):
        """Whether the message has been sent to starboard"""
        return self.flags & 1 << 0


def exists(id: str) -> bool:
    """
    Checks if a message is found in the database

    :param str name: A name to check
    :return: A bool defining whether that message exists
    """
    if len(database.fetchall("SELECT * FROM messages WHERE id=%s", (id,))) == 1:
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
    record = database.fetchone("SELECT * FROM messages WHERE id=%s", (id,))
    message = Message(**record)
    return message


def get_all() -> list[Message]:
    """
    :return: A list of all registered messages
    """
    records = database.fetchall("SELECT * from messages")
    return [Message(**record) for record in records]


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
    database.execute(sql, tuple(message))


def update(message: Message, flags: int = None, star_users: str = None) -> None:
    """
    Updates a message in the database

    Same as in players, not documented until fixed
    """
    if flags is not None:
        database.execute("UPDATE messages SET flags=%s WHERE id=%s", (flags, message.id))
        message.flags = flags
    if star_users is not None:
        database.execute("UPDATE messages SET star_users=%s WHERE id=%s", (star_users, message.id))
        message.star_users = star_users


def delete(message: Message) -> None:
    """
    Deletes a message from the database

    :param Message message: The message to delete
    """
    database.execute("DELETE FROM messages WHERE id=%s", (message.id,))


class MessageNotFound(Exception):
    """
    Exception raised when a message isn't found in the database
    """

    def __str__(self) -> str:
        return "Requested message was not found"
