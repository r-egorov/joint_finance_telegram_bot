# Telegram Bot for budgeting, early version
This bot can be used by two users for joint budgeting.
It is availible only in Russian so far.

Each user has their own personal budget as well as joint budget with the other user.

The users can add expenses to the database by sending a message of the "*500 cafe*" template. In this case an expense of 500 roubles will be added in the "*cafe*" category. The expenses can be deleted by clicking on the "Delete" inline button, which will be sent by the bot.

The categories can be accessed with aliases, specified in the database. One can get all the categories by using yhe "/list_categories" command. Custom categories and custom aliases for them are coming in the later versions.

The users can request month statistics for one of their budgets, last ten expenses in the budget and overall statistics on their expenses.

The libraries used for this projects:
* aiogram
* sqlite3
* re

Setup:
1. Create a telegram bot using the @BotFather bot and get the token for your bot.
2. Create a **config.py** file, where specify the *TOKEN* variable, which would be your token, and *ACCESS_IDS* list, which would contain two user ids of the people who will use the bot.
3. Start the server using the *python server.py* command.
