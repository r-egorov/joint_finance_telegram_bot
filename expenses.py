import datetime
import re
import pytz
import db
import exceptions
import budgets
from typing import List, NamedTuple, Optional
from categories import Categories


class ParsedMessage(NamedTuple):
    """ Parsed message about the expense structure """
    amount: int
    category_text: str


class Expense(NamedTuple):
    """ Expense to be added to the DB structure """
    id: Optional[int]
    username: Optional[str]
    amount: int
    category_name: str


def add_expense(raw_message: str, user_id: int, budget_id: int) -> Expense:
    """
    Takes the recieved message, parses it and adds an expense to the DB.

    Parameters:
        raw_message: str — the recieved message, raw, not parsed
        user_id: int — User's id
        budget_id: int — the id the User's budget for the expense
    Returns:
        an instance of the Expense class
    """
    parsed_message = _parse_message(raw_message)
    category = Categories().get_category(parsed_message.category_text)
    db.insert("expenses", {
        "user_id": user_id,
        "budget_id": budget_id,
        "amount": parsed_message.amount,
        "created": get_timenow_formatted(),
        "category_codename": category.category_codename,
        "raw_message": raw_message
    })
    return Expense(id=None, username=None,
                   amount=parsed_message.amount,
                   category_name=category.category_name)


def get_day_stats(budget_id: int) -> str:
    """
    Gets statistics for the day

    Parameters:
        budget_id: int — the budget's id
    Returns:
        stats: str — the statistics of the budget for the month, in str format
    """
    cursor = db.get_cursor()
    cursor.execute(
        "SELECT SUM(amount) "
        "FROM expenses "
        "WHERE DATE(created) == DATE('now', 'localtime')"
    )
    result = cursor.fetchone()
    if not result:
        return "Сегодня ещё не было расходов"
    today_exp_sum = result[0]
    return f"Всего потрачено: {today_exp_sum} руб."


def get_month_stats(budget_id: int) -> str:
    """
    Gets statistics for the month

    Parameters:
        budget_id: int — the budget's id
    Returns:
        stats: str — the statistics of the budget for the month, in str format
    """
    now = get_datetimenow()
    first_day_of_the_month = f"{now.year:04d}-{now.month:02d}-01"
    cursor = db.get_cursor()
    cursor.execute(
        "SELECT SUM(amount)"
        f"FROM expenses WHERE DATE(created) >= '{first_day_of_the_month}' "
        f"AND budget_id = {budget_id}"
    )
    result = cursor.fetchone()
    if not result[0]:
        return "В этом месяце ещё не было расходов."
    all_month_expenses = result[0]
    cursor.execute(
        "SELECT DISTINCT user_id "
        "FROM expenses "
        f"WHERE budget_id = {budget_id}"
    )
    result = cursor.fetchall()
    user_ids = []
    for user_ids_tuple in result:
        user_ids.append(user_ids_tuple[0])
    queries = [
        "SELECT u.username, SUM(e.amount) "
        "FROM expenses e "
        "JOIN users u "
        "ON e.user_id = u.id "
        f"WHERE e.budget_id = {budget_id} "
        f"AND e.user_id = {user_id} AND "
        f"DATE(created) >= '{first_day_of_the_month}'"
        for user_id in user_ids
    ]
    result = []
    for i in range(len(queries)):
        cursor.execute(queries[i])
        row = cursor.fetchone()
        result.append(row)

    budget_name = budgets.get_budget_name(budget_id)
    stats = f"Бюджет: \"{budget_name}\"\n"
    stats_strs = [
        f"Пользователь {row[0]} потратил {row[1]}.\n"
        for row in result
    ]
    for string in stats_strs:
        stats += string
    stats += f"Всего потрачено: {all_month_expenses}\n"
    return stats


def get_overall_stats(budget_id: int) -> str:
    """
    Gets overall statistics

    Parameters:
        budget_id: int — the budget's id
    Returns:
        stats: str — the statistics of the budget for the month, in str format
    """
    return "какая-то статистика"


def last(user_id: int, budget_id: int) -> List[Expense]:
    """
    Returns last ten expenses from the selected budget of the User
    Parameters:
        user_id: int — User's id
        budget_id: int — id of the User's budget
    Returns:
        A list of Expense class instances
    """
    cursor = db.get_cursor()
    cursor.execute(
        "SELECT e.id, u.username, e.amount, c.category_name "
        "FROM expenses e JOIN categories c "
        "ON e.category_codename = c.category_codename "
        "JOIN users u "
        "ON e.user_id = u.id "
        f"WHERE e.budget_id = {budget_id} "
        "ORDER BY e.created DESC LIMIT 10"
    )
    rows = cursor.fetchall()
    last_expenses = [Expense(id=row[0], username=row[1], amount=row[2], category_name=row[3])
                     for row in rows]
    return last_expenses


def delete_expense(exp_id: int):
    """ Takes and id of the expense and deletes it from the DB """
    db.delete("expenses", exp_id)


def _parse_message(raw_message: str) -> ParsedMessage:
    """
    Parses the recieved message and returns an instance of ParsedMessage class

    Parameters:
        raw_message: str — the recieved message, raw, not parsed
    Returns:
        parsed message: an instance of ParsedMessage class
    """
    re_result = re.search(r"^(\d+)(.*)", raw_message)
    if not re_result or not re_result.group(0) \
            or not re_result.group(1) or not re_result.group(2):
        raise exceptions.NotCorrectMessage(
            "Сообщение не соответствует шаблону: \"1500 кафе\""
        )

    amount = re_result.group(1).strip()
    category_text = re_result.group(2).strip().lower()
    return ParsedMessage(amount=int(amount), category_text=category_text)


def get_timenow_formatted() -> str:
    """ Returns today's date and time in string format """
    return get_datetimenow().strftime("%Y-%m-%d %H:%M:%S")


def get_datetimenow() -> datetime.datetime:
    """ Gets datetime for now according to the GMT+3 zone (Moscow) """
    tz = pytz.timezone("Europe/Moscow")
    now = datetime.datetime.now(tz)
    return now
