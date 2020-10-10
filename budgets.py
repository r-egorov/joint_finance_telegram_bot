import db
import users
from typing import Dict, List, Tuple, NamedTuple


class Budget(NamedTuple):
    """ Budget structure """
    id: int
    name: str
    balance: int
    daily_limit: int


def init_budgets(user_id: int, username: str):
    """
    Initializes standard budgets for a user

    Parameters:
        user_id: int — the User's id
        username: str - the User's username
    """
    budget_name = username + "_personal"
    column_values = {
        "name": budget_name,
        "balance": 10000,
        "daily_limit": 500
    }
    db.insert("budget", column_values)
    update_budget_map(user_id, get_budget_id(budget_name))
    update_budget_map(user_id, get_budget_id("joint"))


def get_all_budgets(user_id: int) -> List[Budget]:
    """
    Gets all the budgets of the user

    Parameters:
        user_id: int - the User's id
    Returns:
        A list of Budget class instances
    """
    cursor = db.get_cursor()
    cursor.execute(
        "SELECT b.id, b.name, b.balance, b.daily_limit "
        "FROM budget b JOIN userBudgetMap u "
        "ON b.id = u.budget_id "
        f"WHERE u.user_id = {user_id} "
    )
    rows = cursor.fetchall()
    budgets = [Budget(id=row[0], name=row[1], balance=row[2], daily_limit=row[3])
               for row in rows]
    return budgets


def update_budget_map(user_id: int, budget_id: int):
    """
    Updates the UserBudgetMap

    Parameters:
        user_id: int - the User's id
        budget_id: int - the budget's id
    """
    column_values = {
        "user_id": user_id,
        "budget_id": budget_id
    }
    db.insert("userBudgetMap", column_values)


def get_budget_id(budget_name: str) -> int:
    """
    Gets budget's id based on the budget's name

    Parameters:
        budget_name: str — the budget's name
    Returns:
        budget_id: int — the budget's id
    """
    cursor = db.get_cursor()
    cursor.execute(f"SELECT id FROM budget WHERE name = \"{budget_name}\"")
    budget_id = cursor.fetchall()[0][0]
    return budget_id


def get_budget_name(budget_id: int) -> str:
    """
    Gets budget's name based on the budget's id

    Parameters:
        budget_id: int — the budget's id
    Returns:
        budget_name: str — the budget's name
    """
    cursor = db.get_cursor()
    cursor.execute(f"SELECT name FROM budget WHERE id = {budget_id}")
    budget_name = cursor.fetchall()[0][0]
    return budget_name


def set_balance(budget_id: int, balance: int):
    """
    Sets balance to the budget

    Parameters:
        budget_id: int — the budget's id
        balance: int — the new balance
    """
    column_value = {"balance": balance}
    db.update("balance", budget_id, column_value)


def set_daily_limit(budget_id: int, daily_limit: int):
    """
    Sets daily limit to the budget

    Parameters:
        budget_id: int — the budget's id
        daily_limit: int — the new daily limit
    """
    column_value = {"daily_limit": daily_limit}
    db.update("balance", budget_id, column_value)
