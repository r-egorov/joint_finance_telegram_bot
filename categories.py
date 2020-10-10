from typing import Dict, List, NamedTuple
import db


class Category(NamedTuple):
    """ Category structure """
    category_codename: str
    category_name: str
    is_base_expense: bool
    aliases: List[str]


class Categories:
    def __init__(self):
        self._categories = self._get_categories()

    def _get_categories(self) -> List[Category]:
        """ Returns a list of all the categories in the database """
        categories = db.get_all(
            "categories",
            ["category_codename", "category_name",
             "is_base_expense", "aliases"]
        )
        res_categories = self._fill_aliases(categories)
        return res_categories

    def _fill_aliases(self, categories: List[Dict]) -> List[Category]:
        """
        Fills the categories with the aliases,
        which could be used to choose the category for the expense.
        i.g. User's message: '150 cafe', where cafe is an alias for some category.

        Parameters:
            The list of column:value dicts from 'categories' table
        Returns:
            The list of Category class instances
        """
        res_categories = []
        for cat in categories:
            aliases = cat["aliases"].split(", ")
            aliases = list(filter(None, map(str.strip, aliases)))
            aliases.append(cat["category_codename"])
            aliases.append(cat["category_name"])
            res_categories.append(Category(
                category_codename=cat["category_codename"],
                category_name=cat["category_name"],
                is_base_expense=cat["is_base_expense"],
                aliases=aliases
            ))
        return res_categories

    def get_all_categories(self) -> List[Category]:
        """ Returns the list of all the Categories """
        return self._categories

    def get_category(self, alias: str) -> Category:
        """ Takes an alias and returns the corresponding category """
        other_category = None
        for cat in self._categories:
            if cat.category_codename == "other":
                other_category = cat
            for aliases_list in cat.aliases:
                if alias in aliases_list:
                    return cat
        return other_category
