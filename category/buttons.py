import math
from typing import List
from aiogram.utils.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from .model import CategoryModel, CustomButtonsModel


class CategoryCallBackData:
    def __init__(self, prefix: str = ""):
        self.control = CallbackData(prefix + "_control_categories", "type", "id")
        self.category = CallbackData(prefix + "_category", "id")


class CategoryButtons:
    def __init__(
        self,
        callback: CategoryCallBackData,
        custom_buttons: CustomButtonsModel | None = None,
    ) -> None:
        self.custom_buttons = custom_buttons
        self.cb = callback
        self.cats = {}
        self.current = {}

    def add_main_category(self, name: str = "Add Category") -> InlineKeyboardButton:
        return InlineKeyboardButton(
            name, callback_data=self.cb.control.new(type="main", id="root")
        )

    def _main_categories(
        self, categories: List[CategoryModel], isAdmin: bool = False
    ) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup(row_width=1)
        if isAdmin:
            markup.add(self.add_main_category())
        buttons = [
            InlineKeyboardButton(_.name, callback_data=self.cb.category.new(id=_.id))
            for _ in categories
        ]
        markup.add(*buttons)
        return markup

    def main_menu(self, name: str = "Categories") -> InlineKeyboardButton:
        return InlineKeyboardButton(name, callback_data=self.cb.category.new(id="root"))

    def _save_description(self, name: str) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup().add(
            InlineKeyboardButton(
                name, callback_data=self.cb.control.new(type="save", id="")
            )
        )

    def _get_navigation(self, page: int, pages: int, type: str = "page"):
        return [
            InlineKeyboardButton(
                text="◀" if page > 1 else "❌",
                callback_data=self.cb.control.new(
                    type=type if page > 1 else "",
                    id=str((page - 1)) if page > 1 else "",
                ),
            ),
            InlineKeyboardButton(text=f"{page} / {pages}", callback_data="_"),
            InlineKeyboardButton(
                text="▶" if page < pages else "❌",
                callback_data=self.cb.control.new(
                    type=type if page < pages else "",
                    id=str((page + 1)) if page < pages else "",
                ),
            ),
        ]

    def _categories(
        self,
        categories: List[CategoryModel],
        control_text: str,
        back_text: str,
        page: int = 1,
        current: CategoryModel | None = None,
        isAdmin: bool = False,
        isReorder: bool = False,
        id: str = "",
    ) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardMarkup(row_width=1)

        user, type = id.split(":")

        if not categories and type == "page":
            categories = self.cats.get(user)
            current = self.current.get(user)

        else:
            self.cats[user] = categories
            self.current[user] = current

        lenght = len(categories)

        if self.custom_buttons and self.custom_buttons.category:
            keyboard.add(
                [
                    InlineKeyboardButton(
                        button.name,
                        callback_data=button.callback.new(
                            id=current.id, **button.own_args
                        ),
                    )
                    for button in self.custom_buttons.category
                ]
            )

        if isAdmin:
            keyboard.add(
                InlineKeyboardButton(
                    control_text,
                    callback_data=self.cb.control.new(type="menu", id=str(current.id)),
                )
            )

        buttons = [
            InlineKeyboardButton(_.name, callback_data=self.cb.category.new(id=_.id))
            for _ in categories
        ]

        pages = 1
        start = 0
        stop = 4

        if lenght > 6:
            pages = math.ceil(lenght / 6)
            start = (page - 1) * 5
            stop = start + 5
            keyboard.add(*buttons[start:stop])
            if not isReorder:
                keyboard.row(*self._get_navigation(page, pages))
        else:
            keyboard.add(*buttons)

        keyboard.add(
            *[
                InlineKeyboardButton(
                    back_text, callback_data=self.cb.category.new(id=current.parent_id)
                )
            ]
        )
        return keyboard

    def _control_menu(
        self, id: str, text: List[str] | None = None
    ) -> InlineKeyboardMarkup:
        """
        Param: text - text for buttons

        0 - add subcategory
        1 - change name
        2 - chahge descrition
        3 - select subcategory for reordering
        4 - delete category
        5 - back to category

        """
        if not text:
            text = [
                "Add Subcategory",
                "Change Name",
                "Change Description",
                "Reorder Subcategories",
                "Delete Category",
                "<--=",
            ]
        types = ["sub", "name", "description", "select", "delete", "back_self"]
        keyboard = InlineKeyboardMarkup(row_width=1)
        buttons = [
            InlineKeyboardButton(
                name, callback_data=self.cb.control.new(type=type, id=id)
            )
            for name, type in zip(text, types)
        ]
        return keyboard.add(*buttons)

    def save_subcategories(self, texts: List, id: str) -> InlineKeyboardButton:
        types = ["save_subs", "delete_subs", "cancel_deleting"]
        markup = InlineKeyboardMarkup(row_width=1)
        return markup.add(
            *[
                InlineKeyboardButton(
                    name, callback_data=self.cb.control.new(type=type, id=id)
                )
                for name, type in zip(texts, types)
            ]
        )
