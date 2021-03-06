from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.utils.markdown import text, bold, italic
from aiogram.types import ParseMode, ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from typing import Union

from config import TOKEN, ACCESS_IDS
from states import UserState
from middlewares import AccessMiddleware
from categories import Categories

import buttons
import re
import users
import expenses
import exceptions
import budgets

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(AccessMiddleware(ACCESS_IDS))


@dp.message_handler(commands=['set_state'])
async def process_setstate_command(message: types.Message):
    argument = message.get_args()
    state = dp.current_state(user=message.from_user.id)
    if not argument:
        await state.reset_state()
        return await message.reply("State reset, no argument found")
    state_to_set = "UserState:" + argument
    index = UserState.all_states_names.index(state_to_set)
    await state.set_state(UserState.states[index])
    await message.answer("State set")


async def state_budget_name(message: Union[types.Message, types.CallbackQuery]):
    state = dp.current_state(user=message.from_user.id)
    if await state.get_state() == "UserState:JOINT_BUDGET":
        budget_name = "joint"
    else:
        budget_name = message.from_user.username + "_personal"
    return budget_name


@dp.message_handler(lambda message: not users.user_exists(message.from_user.id))
async def register_user(message: types.Message):
    """ Registers user if not registered """
    if users.add_user_ifn_exists(message.from_user):
        budgets.init_budgets(message.from_user.id, str(message.from_user.username))
        answer_text = "Вы успешно зарегистрированы!\n"
        await UserState.IDLE.set()
        return await message.answer(answer_text)


@dp.message_handler(state="*", commands=["main_menu", "start"])
async def main_menu(message: types.Message):
    """ Offers to navigate through the bot with commands """
    answer_text = text("Вы в главном меню.")
    await message.answer(answer_text, reply_markup=buttons.kb_general)


@dp.message_handler(lambda message: message.text == buttons.content_chs_bdgt,
                    state="*")
async def choose_budget_menu(message: types.Message):
    """ Offers to choose the budget: personal or joint """
    budgets_list = budgets.get_all_budgets(message.from_user.id)
    budgets_list_rows = [
        f"{budget.name}, balance: {budget.balance}, daily limit: {budget.daily_limit}"
        for budget in budgets_list
    ]
    answer_text = text("Вам доступны следующие бюджеты:" +
                       "\n\n" +
                       "\n".join(budgets_list_rows))
    kb_mrkup = buttons.mrkup_chs_budget(budgets_list)
    await UserState.CHOOSE_BUDGET.set()
    await message.answer(answer_text, reply_markup=kb_mrkup)


@dp.message_handler(commands=["list_categories"],
                    state="*")
async def list_categories(message: types.Message):
    """
    Sends a list of categories to the user
    """
    categories_list = Categories().get_all_categories()
    categories_strs = [text(bold(f"\"{c.category_name.capitalize()}\"\n") + f"Теги: {c.aliases}\n")
                       for c in categories_list]
    answer_text = "\n".join(categories_strs)
    await message.answer(text(bold("Список категорий\n\n") +
                              answer_text), parse_mode=ParseMode.MARKDOWN)


@dp.callback_query_handler(lambda c: re.match(r"^choose\d+$", c.data),
                           state=UserState.CHOOSE_BUDGET)
async def choose_budget(callback_query: types.CallbackQuery):
    """ Chooses the budget, sets the corresponding state to the user """
    await bot.answer_callback_query(callback_query.id)
    budget_id = int(re.search(r"^choose(\d+)$", callback_query.data).group(1))
    budget_name = budgets.get_budget_name(budget_id)
    if budget_name == "joint":
        await UserState.JOINT_BUDGET.set()
    else:
        await UserState.PERSONAL_BUDGET.set()
    await bot.send_message(callback_query.from_user.id,
                           f"Выбран бюджет - {budget_name}")


@dp.callback_query_handler(lambda c: c.data == "deleting_expenses",
                           state=[UserState.JOINT_BUDGET, UserState.PERSONAL_BUDGET])
async def deleting_expenses_state(callback_query: types.CallbackQuery):
    """ Sends each expense from the last ten, offering to delete each of them """
    await bot.answer_callback_query(callback_query.id)
    budget_name = await state_budget_name(callback_query)
    budget_id = budgets.get_budget_id(budget_name)
    last_expenses = expenses.get_last_expenses(callback_query.from_user.id, budget_id)
    if not last_expenses:
        await bot.send_message(callback_query.from_user.id, "Трат ещё не было.")
        return
    await bot.send_message(callback_query.from_user.id, text(bold("Удаление трат\n\n")),
                           parse_mode=ParseMode.MARKDOWN)
    for expense in last_expenses:
        expense_str = f"- {expense.amount} руб. на {expense.category_name}, добавил {expense.username}\n"
        await bot.send_message(callback_query.from_user.id, expense_str,
                               reply_markup=buttons.markup_del_expense(expense))


@dp.callback_query_handler(lambda c: c.data.startswith('del'),
                           state=[UserState.JOINT_BUDGET, UserState.PERSONAL_BUDGET])
async def del_expense(callback_query: types.CallbackQuery):
    """ Deletes an expense from the table expenses"""
    await bot.answer_callback_query(callback_query.id)

    row_id = int(callback_query.data[3:])
    expenses.delete_expense(row_id)
    answer = "Удалил!"
    await bot.send_message(callback_query.from_user.id, answer)


@dp.callback_query_handler(lambda c: c.data.startswith('mstats'),
                           state=[UserState.JOINT_BUDGET, UserState.PERSONAL_BUDGET])
async def choose_month_stats(callback_query: types.CallbackQuery):
    """ Gets stats for the chosen month """
    await bot.answer_callback_query(callback_query.id)

    year_month = str(callback_query.data[6:])
    budget_name = await state_budget_name(callback_query)
    budget_id = budgets.get_budget_id(budget_name)
    stats_str = expenses.get_month_stats(budget_id, year_month)
    month_name = expenses.month_name(year_month)
    await bot.send_message(callback_query.from_user.id,
                           text(bold("Расходы за выбранный месяц\n{0}\n\n"
                                     .format(month_name))) +
                           stats_str,
                           parse_mode=ParseMode.MARKDOWN)


@dp.message_handler(lambda message: message.text == buttons.content_mnth_stats,
                    state=[UserState.JOINT_BUDGET, UserState.PERSONAL_BUDGET])
async def get_month_statistics(message: types.Message):
    """ Gets month stats for the current budget """
    budget_name = await state_budget_name(message)
    budget_id = budgets.get_budget_id(budget_name)
    now_year_month = expenses.get_year_month_now()
    stats_str = expenses.get_month_stats(budget_id, now_year_month)
    kb = buttons.mrkup_chs_month_stats(expenses.get_budget_months(budget_id))
    await message.answer(text(bold("Расходы за месяц\n\n")) +
                         stats_str,
                         parse_mode=ParseMode.MARKDOWN,
                         reply_markup=kb)


@dp.message_handler(lambda message: message.text == buttons.content_day_stats,
                    state=[UserState.JOINT_BUDGET, UserState.PERSONAL_BUDGET])
async def get_day_statistics(message: types.Message):
    budget_name = await state_budget_name(message)
    budget_id = budgets.get_budget_id(budget_name)
    stats_str = expenses.get_day_stats(budget_id)
    await message.answer(text(bold("Расходы за сегодня\n\n")) +
                         stats_str,
                         parse_mode=ParseMode.MARKDOWN)


@dp.message_handler(lambda message: message.text == buttons.content_stats,
                    state=[UserState.JOINT_BUDGET, UserState.PERSONAL_BUDGET])
async def get_overall_statistics(message: types.Message):
    budget_name = await state_budget_name(message)
    budget_id = budgets.get_budget_id(budget_name)
    stats_str = expenses.get_overall_stats(message.from_user.id)
    await message.answer(text(bold(f"Общая статистика\n\n")) +
                         stats_str,
                         parse_mode=ParseMode.MARKDOWN)


@dp.message_handler(lambda message: message.text == buttons.content_last_expns,
                    state=[UserState.JOINT_BUDGET, UserState.PERSONAL_BUDGET])
async def get_last_expenses(message: types.Message):
    """ Gets last ten expenses for the current budget """
    budget_name = await state_budget_name(message)
    budget_id = budgets.get_budget_id(budget_name)
    last_expenses = expenses.get_last_expenses(message.from_user.id, budget_id)
    budget_name_mrkdwn = budget_name.replace("_", "\\_")
    kb = None
    answer_text = text(bold(f"Последние траты\n\n") +
                       f"Бюджет: \"{budget_name_mrkdwn}\"\n\n")
    if not last_expenses:
        answer_text += "Трат ещё не было."
    else:
        expenses_to_send = [
            f"- {expense.amount} руб. на {expense.category_name}, добавил {expense.username}\n"
            for expense in last_expenses
        ]
        answer_text += "\n".join(expenses_to_send)
        kb = buttons.kb_del_expenses
    params = {"text": answer_text, "parse_mode": ParseMode.MARKDOWN}
    if kb: params["reply_markup"] = kb
    await message.answer(**params)


@dp.message_handler(state=UserState.PERSONAL_BUDGET)
async def add_expense(message: types.Message):
    """ Adds an expense to the needed budget """
    budget_name = message.from_user.username + "_personal"
    budget_id = budgets.get_budget_id(budget_name)
    try:
        expense = expenses.add_expense(message.text, message.from_user.id,
                                       budget_id)
    except exceptions.NotCorrectMessage as e:
        await message.answer(str(e))
        return
    answer_text = (
        f"В бюджет \"{budget_name}\" "
        f"добавлена трата {expense.amount} руб. на {expense.category_name}.\n"
    )
    await message.answer(answer_text)


@dp.message_handler(state=UserState.JOINT_BUDGET)
async def add_expense(message: types.Message):
    """ Adds an expense to the needed budget """
    budget_id = budgets.get_budget_id("joint")
    users_list = budgets.get_all_users(budget_id)
    try:
        expense = expenses.add_expense(message.text, message.from_user.id,
                                       budget_id)
    except exceptions.NotCorrectMessage as e:
        await message.answer(str(e))
        return
    answer_text = (
        f"В бюждет \"joint\" "
        f"добавлена трата {expense.amount} руб. на {expense.category_name}.\n"
    )
    for user in users_list:
        if user.id == message.from_user.id:
            continue
        else:
            await bot.send_message(user.id,
                                   (text(bold("В бюджет \"joint\" была добавлена трата\n\n") +
                                         f"Добавил: {message.from_user.username}\n" +
                                         f"Сумма: {expense.amount}\n" +
                                         f"Категория: {expense.category_name}\n")
                                    ),
                                   parse_mode=ParseMode.MARKDOWN)
    await message.answer(answer_text)


if __name__ == "__main__":
    executor.start_polling(dp)
