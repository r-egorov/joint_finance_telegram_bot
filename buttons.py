import emoji
from aiogram.types import ReplyKeyboardMarkup,\
    KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from typing import List
from expenses import Expense
from budgets import Budget

kb_general = ReplyKeyboardMarkup(resize_keyboard=True)

content_chs_bdgt = "Выбор бюджета " + emoji.emojize(":moneybag:", use_aliases=True)
content_day_stats = "Траты за день " + emoji.emojize(":date:", use_aliases=True)
content_mnth_stats = "Траты за месяц " + emoji.emojize(":spiral_calendar:", use_aliases=True)
content_last_expns = "Последние траты " + emoji.emojize(":inbox_tray:", use_aliases=True)
content_stats = "Статистика " + emoji.emojize(":bar_chart:", use_aliases=True)

btn_chs_bdgt = KeyboardButton(content_chs_bdgt)
btn_day_stats = KeyboardButton(content_day_stats)
btn_mnth_stats = KeyboardButton(content_mnth_stats)
btn_last_expns = KeyboardButton(content_last_expns)
btn_stats = KeyboardButton(content_stats)

kb_general.row(btn_chs_bdgt)
kb_general.row(btn_day_stats, btn_last_expns)
kb_general.row(btn_mnth_stats, btn_stats)

btn_inln_del_expenses = InlineKeyboardButton("Удаление трат", callback_data="deleting_expenses")
kb_del_expenses = InlineKeyboardMarkup().add(btn_inln_del_expenses)


def markup_del_expense(expense: Expense) -> InlineKeyboardMarkup:
    """
    Makes a markup of an inline button to delete an expense.

    Parameters:
        expense: Expense — an expense to be deleted (instances of the Expense
        class)
    Returns:
        kb_mrkup: InlineKeyboardMarkup — a markup for the button
    """
    btn_inln_del_exp = InlineKeyboardButton("Удалить трату",
                                            callback_data=f"del{expense.id}")
    kb_mrkup = InlineKeyboardMarkup().add(btn_inln_del_exp)
    return kb_mrkup


def btn_chs_budget(budget: Budget) -> InlineKeyboardButton:
    """
    Makes a markup of an inline button to choose a budget

    Parameters:
        budget: Budget — an instance of the Budget class
    Returns:
        btn_inln_chs_budget: InlineKeyboardButton — an inline button to choose the budget
    """
    btn_inln_chs_budget = InlineKeyboardButton(f"Выбрать - \"{budget.name}\"",
                                               callback_data=f"choose{budget.id}")
    return btn_inln_chs_budget


def mrkup_chs_budget(budgets_list: List[Budget]) -> InlineKeyboardMarkup:
    """
    Makes a markup of as many inline buttons as the user has

    Parameters:
        budgets_list: List[Budget] — a list of budgets the user has
    Returns:
        kb_mrkup: InlineKeyboardMarkup — a markup of buttons to choose the
        budget
    """
    kb_mrkup = InlineKeyboardMarkup()
    for budget in budgets_list:
        btn_inln_chs_budget = btn_chs_budget(budget)
        kb_mrkup.add(btn_inln_chs_budget)
    return kb_mrkup


def mrkup_chs_month_stats(month_list: List) -> InlineKeyboardMarkup:
    """
    Makes a markup of as many month buttons as there are in the budget

    Parameters:
        month_list: List — a list of year-month in '%Y-%m' format
    Returns:
        kb_mrkup: InlineKeyboardMarkup — a markup of buttons to choose the
        month
    """
    kb_mrkup = InlineKeyboardMarkup()
    for month in month_list:
        btn_inln_chs_month = InlineKeyboardButton(month,
                                                  callback_data=f"mstats{month}")
        kb_mrkup.add(btn_inln_chs_month)
    return kb_mrkup