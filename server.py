from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.utils.markdown import text, bold, italic
from aiogram.types import ParseMode, ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import TOKEN, ACCESS_IDS
from states import UserState
from middlewares import AccessMiddleware

import buttons
import emoji
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


async def state_budget_name(message: types.Message):
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
    await message.answer(answer_text, reply_markup=buttons.kb_mrkup_general)


@dp.message_handler(lambda message: message.text == buttons.content_chs_bdgt,
                    state="*")
async def choose_budget_menu(message: types.Message):
    """ Offers to choose the budget: personal or joint """
    budgets_list = budgets.get_all_budgets(message.from_user.id)
    budgets_list_rows = [
        f"/id{budget.id} - {budget.name}, balance: {budget.balance}, daily limit: {budget.daily_limit}"
        for budget in budgets_list
    ]
    answer_text = text("Вам доступны следующие бюджеты:" +
                       "\n\n" +
                       "\n".join(budgets_list_rows) +
                       "\n\nЧтобы выбрать бюджет, нажмите на его ID.")
    await UserState.CHOOSE_BUDGET.set()
    await message.answer(answer_text)


@dp.message_handler(state=UserState.CHOOSE_BUDGET)
async def choose_budget(message: types.Message):
    """ Chooses the budget, sets the corresponding state to the user """
    if not re.match(r"^/id\d+$", message.text):
        await message.answer("Пожалуйста, выберите нужный ID бюджета.")
    else:
        budget_id = int(re.search(r"^/id(\d+)$", message.text).group(1))
        budget_name = budgets.get_budget_name(budget_id)
        if budget_name == "joint":
            await UserState.JOINT_BUDGET.set()
        else:
            await UserState.PERSONAL_BUDGET.set()
        await message.answer(f"Выбран бюджет - {budget_name}")


@dp.message_handler(lambda message: message.text.startswith('/del'),
                    state=[UserState.JOINT_BUDGET, UserState.PERSONAL_BUDGET])
async def del_expense(message: types.Message):
    """ Deletes an expense from the table expenses"""
    try:
        row_id = int(message.text[4:])
        expenses.delete_expense(row_id)
        answer = "Удалил!"
    except ValueError:
        answer = "Не понял, попробуй формат сообщения \"/del <id расхода>\""
    await message.answer(answer)


@dp.message_handler(lambda message: message.text == buttons.content_mnth_stats,
                    state=[UserState.JOINT_BUDGET, UserState.PERSONAL_BUDGET])
async def get_month_statistics(message: types.Message):
    """ Gets month stats for the current budget """
    budget_name = await state_budget_name(message)
    budget_id = budgets.get_budget_id(budget_name)
    stats_str = expenses.get_month_stats(budget_id)
    await message.answer(text(bold("Расходы за месяц\n")) +
                         stats_str,
                         parse_mode=ParseMode.MARKDOWN)


@dp.message_handler(lambda message: message.text == buttons.content_day_stats,
                    state=[UserState.JOINT_BUDGET, UserState.PERSONAL_BUDGET])
async def get_day_statistics(message: types.Message):
    budget_name = await state_budget_name(message)
    budget_id = budgets.get_budget_id(budget_name)
    stats_str = expenses.get_day_stats(budget_id)
    await message.answer(text(bold("Расходы за сегодня\n")) +
                         stats_str,
                         parse_mode=ParseMode.MARKDOWN)


@dp.message_handler(lambda message: message.text == buttons.content_stats,
                    state=[UserState.JOINT_BUDGET, UserState.PERSONAL_BUDGET])
async def get_overall_statistics(message: types.Message):
    budget_name = await state_budget_name(message)
    budget_id = budgets.get_budget_id(budget_name)
    stats_str = expenses.get_overall_stats(budget_id)
    await message.answer(text(bold(f"Общая статистика\n")) +
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
    answer_text = text(bold(f"Последние траты\n") +
                       f"Бюджет: \"{budget_name_mrkdwn}\"\n")
    if not last_expenses:
        answer_text += "Трат ещё не было."
    else:
        expenses_to_send = [
            f"- {expense.amount} руб. на {expense.category_name}, добавил {expense.username} — нажми "
            f"/del{expense.id} для удаления\n"
            for expense in last_expenses
        ]
        answer_text += "\n".join(expenses_to_send)
    await message.answer(answer_text,
                         parse_mode=ParseMode.MARKDOWN)


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
    await message.answer(answer_text)


if __name__ == "__main__":
    executor.start_polling(dp)
