from typing import List
from aiogram.utils.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton,InlineKeyboardMarkup

from .model import CategoryModel, CustomButtonsModel

class CategoryCallBackData:
    def __init__(self, prefix:str = ''):
        self.control = CallbackData(prefix + "_control_categories", "type", "id")
        self.category = CallbackData(prefix + "_category", "id")




class CategoryButtons:

    def __init__(self,callback:CategoryCallBackData) -> None:
        self.cb = callback


    def add_main_category(self,name: str = "Add Category") -> InlineKeyboardButton:
        return InlineKeyboardButton(
            name, callback_data=self.cb.control.new(type="main", id="root")
        )


    def categories(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup().add(InlineKeyboardButton('c', callback_data=self.cb.control.new(type='root', id='root')))

    def _save_description(self, name: str) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup().add(InlineKeyboardButton(name, callback_data=self.cb.control.new(type='save', id='')))

    def _categories(self,
        categories: List[CategoryModel],
        custom_buttons: CustomButtonsModel | None,
        current_id: str,
        page: int = 1,
        isAdmin: bool = False,
        isReorder: bool = False,
        id: str = "",
        control_text: str = "Category Controls"
    ) -> InlineKeyboardMarkup:
        lenght = len(categories)
        keyboard = InlineKeyboardMarkup(row_width=1)

        if custom_buttons and custom_buttons.category:
            keyboard.add(
                [
                    InlineKeyboardButton(
                        button.name,
                        callback_data=button.callback.new(
                            id=current_id, **button.own_args
                        ),
                    )
                    for button in custom_buttons.category
                ]
            )

        if isAdmin:
            keyboard.add(
                InlineKeyboardButton(
                    control_text,
                    callback_data=self.cb.control.new(type="menu"),
                )
            )

        buttons = [
            InlineKeyboardButton(
                _.name, callback_data=CategoryCallBackData.category.new(id=_.id)
            )
            for _ in categories
        ]
        pages = 1
        start = 0
        stop = 4
        position = [_ for _ in categories if _.id == id]
        if not position:
            position = 0
        reorder_buttons = [
            InlineKeyboardButton(
                text=" " if page > 1 else "◀️",
                callback_data=CategoryCallBackData.control.new(
                    type="reorder", id=" " if page > 1 else "c_back"
                ),
            ),
            InlineKeyboardButton(
                text="🔼",
                callback_data=CategoryCallBackData.control.new(
                    type="reorder", id=" " if position > start else "c_up"
                ),
            ),
            InlineKeyboardButton(text=f"{page} / {pages}"),
            InlineKeyboardButton(
                text="🔽",
                callback_data=CategoryCallBackData.control.new(
                    type="reorder", id=" " if position < stop else "c_down"
                ),
            ),
            InlineKeyboardButton(
                text=" " if page < pages else "▶️",
                callback_data=CategoryCallBackData.control.new(
                    type="reorder", id=" " if page < pages else "c_next"
                ),
            ),
        ]

        if lenght > 6:
            pages = lenght // 6
            navigation = [
                InlineKeyboardButton(
                    text=" " if page > 1 else "⤎",
                    callback_data=CategoryCallBackData.control.new(
                        type="page", id=" " if page > 1 else "back"
                    ),
                ),
                InlineKeyboardButton(text=f"{page} / {pages}"),
                InlineKeyboardButton(
                    text=" " if page < pages else "⤏",
                    callback_data=CategoryCallBackData.control.new(
                        type="page", id=" " if page < pages else "next"
                    ),
                ),
            ]
            start = (page - 1) * 4
            stop = start + 4
            keyboard.add(*buttons[start, stop])
            if not isReorder:
                keyboard.row(navigation)
        else:
            keyboard.add(*buttons)
        if isReorder:
            keyboard.row(reorder_buttons)
        return keyboard

    def control_menu(text: List[str] | None) -> InlineKeyboardMarkup:
        if not text:
            text = [
                "Add Subcategory",
                "Change Name",
                "Change Description",
                "Reorder Subcategories",
                "Delete Category",
            ]
        """
            Param: text - text for buttons

            0 - add subcategory
            1 - change name
            2 - chahge descrition
            3 - reorder subcategories
            4 - delete category

        """
        types = ["sub", "name", "description", "reorder", "delete"]
        keyboard = InlineKeyboardMarkup(row_width=1)
        buttons = [
            InlineKeyboardButton(
                name, callback_data=CategoryCallBackData.control.new(type=type)
            )
            for name, type in zip(text, types)
        ]
        return keyboard.add(*buttons)

    def save_subcategories(
        *texts: str
    ) -> InlineKeyboardButton:
        types = ["save_subs", "delete_subs", "cancel_deleting"]
        return [InlineKeyboardButton(name,
                                     callback_data=CategoryCallBackData.control.new(type=type, id='')
                                    ) for name, type in zip(texts,types) ]
