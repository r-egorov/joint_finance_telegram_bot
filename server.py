from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils.executor import start_webhook
from aiogram.utils.markdown import text, bold, italic
from aiogram.types import ParseMode, ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import TOKEN, ACCESS_IDS
from states import UserState
from middlewares import AccessMiddleware

import re
import users
import expenses
import exceptions
import budgets

WEBHOOK_HOST = "35.188.177.177"
WEBHOOK_PORT = 8443
WEBHOOK_LISTEN = "0.0.0.0"

WEBHOOK_SSL_CERT = "../url_cert.pem"
WEBHOOK_SSL_PRIV = "../url_private.key"

WEBHOOK_URL_BASE = f"https://{WEBHOOK_HOST}:{WEBHOOK_PORT}"
WEBHOOK_URL_PATH = f"/{TOKEN}/"
WEBHOOK_URL = f"{WEBHOOK_URL_BASE}{WEBHOOK_URL_PATH}"

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


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    """ Greets, offers /help """
    await message.answer(
        "Привет!\nЯ — бот для учёта расходов и ведения бюджета!\n"
        "Напиши /help, чтобы узнать, как мной пользоваться!\n"
    )


@dp.message_handler(lambda message: not users.user_exists(message.from_user.id))
async def register_user(message: types.Message):
    """ Registers user if not registered """
    if users.add_user_ifn_exists(message.from_user):
        budgets.init_budgets(message.from_user.id, str(message.from_user.username))
        answer_text = "Вы успешно зарегистрированы!\n"
        await UserState.IDLE.set()
        return await message.answer(answer_text)


@dp.message_handler(state="*", commands=['help'])
async def process_help_command(message: types.Message):
    """ Gets "/help" message, tells about hte bot's functions"""
    message_text = text(bold("Вам доступны следующие команды:\n\n") +
                        italic("Просмотр последних трат текущего бюджета: ") + "/getlastexpenses\n" +
                        italic("Сменить бюджет: ") + "/choosebudget\n")
    await message.answer(message_text, parse_mode=ParseMode.MARKDOWN)


@dp.message_handler(state="*", commands=["main_menu"])
async def main_menu(message: types.Message):
    """ Offers to navigate through the bot with commands """
    message_text = text(bold("Вам доступны следующие команды:\n\n") +
                        italic("Выбор бюджета: ") + "/choosebudget\n")
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    choose_budget_button = KeyboardButton("/choosebudget")
    keyboard.add(choose_budget_button, "/getlastexpenses", "/getstats")
    await message.answer(message_text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)


@dp.message_handler(state="*", commands=["choosebudget"])
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


@dp.message_handler(state=[UserState.JOINT_BUDGET, UserState.PERSONAL_BUDGET],
                    commands=["getstats"])
async def get_statistics(message: types.Message):
    """ Gets month stats for the current budget """
    state = dp.current_state(user=message.from_user.id)
    if await state.get_state() == "UserState:JOINT_BUDGET":
        budget_name = "joint"
    else:
        budget_name = message.from_user.username + "_personal"
    budget_id = budgets.get_budget_id(budget_name)
    stats_str = expenses.get_month_stats(budget_id)
    await message.answer(stats_str)


@dp.message_handler(state=[UserState.JOINT_BUDGET, UserState.PERSONAL_BUDGET],
                    commands=["getlastexpenses"])
async def get_last_expenses(message: types.Message):
    """ Gets last ten expenses for the current budget """
    state = dp.current_state(user=message.from_user.id)
    if await state.get_state() == "UserState:JOINT_BUDGET":
        budget_name = "joint"
    else:
        budget_name = message.from_user.username + "_personal"
    budget_id = budgets.get_budget_id(budget_name)
    last_expenses = expenses.last(message.from_user.id, budget_id)
    if not last_expenses:
        await message.answer("Трат ещё не было.")
        return
    expenses_to_send = [
        f"- {expense.amount} руб. на {expense.category_name}, добавил {expense.username} — нажми "
        f"/del{expense.id} для удаления\n"
        for expense in last_expenses
    ]
    answer_text = text(bold(f"Последние траты в \"{budget_name}\"\n") + "\n".join(expenses_to_send))
    await message.answer(answer_text, parse_mode=ParseMode.MARKDOWN)


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


async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)


async def on_shutdown(dp):
    await bot.delete_webhook()
    await dp.storage.close()
    await dp.storage.wait_closed()

if __name__ == "__main__":
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_URL_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBHOOK_HOST,
        port=WEBHOOK_PORT
    )
