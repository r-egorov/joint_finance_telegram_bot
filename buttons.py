import emoji
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup,\
    KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

kb_mrkup_general = ReplyKeyboardMarkup(resize_keyboard=True)

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

kb_mrkup_general.row(btn_chs_bdgt)
kb_mrkup_general.row(btn_day_stats, btn_last_expns)
kb_mrkup_general.row(btn_mnth_stats, btn_stats)


