import emoji
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup,\
    KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from typing import List
from expenses import Expense

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
