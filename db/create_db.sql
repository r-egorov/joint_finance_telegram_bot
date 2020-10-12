CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY,
    username VARCHAR(255),
    state VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS budget(
    id INTEGER PRIMARY KEY,
    name VARCHAR(255),
    balance INTEGER,
    daily_limit INTEGER
);

CREATE TABLE IF NOT EXISTS userBudgetMap(
    row_id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES id(users),
    budget_id INTEGER REFERENCES id(budget)
);

CREATE TABLE IF NOT EXISTS categories(
    category_codename VARCHAR(255) PRIMARY KEY,
    category_name VARCHAR(255),
    is_base_expense BOOLEAN,
    aliases TEXT
);

CREATE TABLE IF NOT EXISTS expenses(
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES id(users),
    budget_id INTEGER REFERENCES id(budget),
    amount INTEGER,
    created DATETIME,
    category_codename VARCHAR(255) REFERENCES category_codename(categories),
    raw_message TEXT
);

INSERT OR REPLACE INTO categories (category_codename, category_name, is_base_expense, aliases)
VALUES
    ("groceries", "продукты", 1, "еда"),
    ("coffee", "кофе", 0, "cofix, кофикс"),
    ("dinner", "обед", 1, "столовая, ланч, бизнес-ланч, бизнес ланч"),
    ("cafe", "кафе", 0, "ресторан"),
    ("transport", "транспорт", 1, "метро, автобус, metro"),
    ("taxi", "такси", 0, "яндекс такси, yandex taxi"),
    ("phone", "телефон", 1, "теле2, связь"),
    ("books", "книги", 0, "литература, литра, лит-ра"),
    ("internet", "интернет", 1, "инет, inet"),
    ("subscriptions", "подписки", 0, "подписка"),
    ("other", "прочее", 0, "другое");

INSERT OR REPLACE INTO budget (id, name, balance, daily_limit)
VALUES
    (1, "joint", 15000, 1000);
