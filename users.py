from aiogram.types import User
from typing import Dict, List, NamedTuple

import db
import budgets
import states

class BotUser(NamedTuple):
    """ User structure """
    user_id: int
    username: str


def add_user_ifn_exists(user: User):
    """
    Adds a new user to the database if no such user exists
    Parameters:
        user: User — the User class
    Returns:
        True — if added successfully
        False — if the User was not add (there was such a User before)
    """
    user_id = user.id
    username = user.username
    if user_exists(user_id):
        return False
    db.insert("users", {
        "id": user_id,
        "username": username
    })
    reset_state(user_id)
    return True


def user_exists(user_id: int) -> bool:
    """ Checks if the User is present in the DB """
    cursor = db.get_cursor()
    cursor.execute(
        f"SELECT username FROM users WHERE id={user_id}"
    )
    user = cursor.fetchall()
    if user:
        return True
    return False


def set_state(user_id: int, state):
    """ Sets the state to the given user and adds it to the DB """
    column_value = {"state": state.state}
    db.update("users", user_id, column_value)


def reset_state(user_id: int):
    """ Sets the IDLE state to the given user """
    set_state(user_id, states.UserState.IDLE)
