from typing import List

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message


from messages_chain import MessagesChain, MongoConnection

from .buttons import CategoryButtons, CategoryCallBackData
from .model import CategoryModel, CustomButtonsModel, MessageTextModel
from .repo import CategoryRepo


class CategoryStates(StatesGroup):
    name = State()
    edit_name = State()
    edit_description = State()
    description = State()
    reoder = State()


class Category:
    def __init__(
        self,
        storage: MongoConnection,
        buttons: CustomButtonsModel | None = None,
        prefix: str = "base",
        admin_ids: List[str] = [],
        texts: MessageTextModel = MessageTextModel(),
    ) -> None:
        db_prefix = prefix + "_categories"
        self.repo = CategoryRepo(storage=storage, storage_prefix=db_prefix).init()
        self.chain = MessagesChain(storage, prefix=f"{db_prefix}_chain")
        if texts.debug:
            dct = texts.dict()
            texts = MessageTextModel.parse_obj(
                dict(
                    (_, (_ + ":" + dct[_])) for _ in dct.keys() if type(dct[_]) != bool
                )
            )
        self.texts = texts
        self.admin_ids = admin_ids
        self.callback = CategoryCallBackData(prefix=prefix)
        self.buttons = CategoryButtons(self.callback, buttons)

    def reg_handlers(self, dispatcher: Dispatcher):
        cb = self.callback
        dp = dispatcher
        dp.register_callback_query_handler(
            self.add_category, cb.control.filter(type=["sub", "main"])
        )
        dp.register_callback_query_handler(
            self.delete_category, cb.control.filter(type="delete")
        )
        dp.register_callback_query_handler(
            self.delete_confirmation,
            cb.control.filter(type=["save_subs", "delete_subs", "cancel_deleting"]),
        )
        dp.register_callback_query_handler(
            self.edit_description, cb.control.filter(type="description")
        )
        dp.register_callback_query_handler(
            self.edit_name, cb.control.filter(type="name")
        )
        dp.register_callback_query_handler(
            self.get_category, cb.control.filter(type=["page", "back_self"])
        )
        dp.register_callback_query_handler(
            self.get_main_category, cb.category.filter(id="root")
        )
        dp.register_callback_query_handler(self.get_category, cb.category.filter())
        dp.register_callback_query_handler(
            self.save_category,
            cb.control.filter(type="save"),
            state=CategoryStates.description,
        )
        dp.register_callback_query_handler(
            self.control_category, cb.control.filter(type="menu")
        )
        dp.register_callback_query_handler(
            self.save_new_description,
            cb.control.filter(type="save"),
            state=CategoryStates.edit_description,
        )
        dp.register_message_handler(self.save_name, state=CategoryStates.name)
        dp.register_message_handler(self.save_new_name, state=CategoryStates.edit_name)
        dp.register_message_handler(
            self.chain.chain_write, state=CategoryStates.description
        )
        dp.register_message_handler(
            self.chain.chain_write, state=CategoryStates.edit_description
        )

    async def try_edit(message: Message, text, markup=None):
        try:
            await message.delete()
            await message.bot.edit_message_text(
                text=text,
                chat_id=message.from_user.id,
                message_id=message.message_id - 1,
                reply_markup=markup,
            )
        except Exception:
            await message.answer(text)

    async def get_main_category(self, query: CallbackQuery):
        categories = await self.repo.get_main_category()
        isAdmin = str(query.from_user.id) in self.admin_ids
        if not categories:
            await query.answer(self.texts.error_menu, cache_time=5)
        try:
            await query.message.edit_caption(
                self.texts.menu,
                reply_markup=self.buttons._main_categories(categories, isAdmin),
            )
        except Exception:
            await query.message.edit_text(
                self.texts.menu,
                reply_markup=self.buttons._main_categories(categories, isAdmin),
            )

    async def control_category(self, query: CallbackQuery, callback_data: dict):
        categories = await self.repo.get_category(callback_data["id"])
        # isAdmin = str(query.from_user.id) in self.admin_ids
        if not categories:
            await query.answer(self.texts.error_menu, cache_time=5)
        try:
            await query.message.edit_reply_markup(
                reply_markup=self.buttons._control_menu(callback_data["id"])
            )
        except Exception:
            await query.message.edit_text(
                self.texts.error_menu,
                reply_markup=self.buttons._control_menu(callback_data["id"]),
            )

    async def get_category(self, query: CallbackQuery, callback_data: dict):
        isAdmin = str(query.from_user.id) in self.admin_ids
        type = callback_data.get("type", "")
        isPage = type == "page"
        category = None
        id = callback_data.get("id", "root")

        if id == "root":
            return await self.get_main_category(query)

        kwargs = dict(
            categories=[],
            isAdmin=isAdmin,
            page=1,
            current=category,
            control_text=self.texts.btn_control,
            back_text=self.texts.btn_back_parent,
            id=f"{query.from_user.id}:{type}",
        )

        if isPage:
            page = int(callback_data.get("id", 1))
            kwargs["page"] = page
            await query.message.edit_reply_markup(self.buttons._categories(**kwargs))
            return

        else:
            category = await self.repo.get_category(id)

            if not category:
                await query.message.answer(self.texts.error_found)
                return

            kwargs["current"] = category
            subcats = await self.repo.get_subcategories(str(category.id))

            kwargs["categories"] = subcats

            if category.description:
                try:
                    await query.message.delete()
                except Exception:
                    pass

                await self.chain.chain_read(query.message, category.description)
                await query.message.answer(
                    category.name, reply_markup=self.buttons._categories(**kwargs)
                )

            else:
                await query.message.edit_text(
                    category.name,
                    reply_markup=self.buttons._categories(**kwargs),
                )

    async def get_all_categories(self, id: str):
        raise NotImplemented

    async def add_category(
        self, query: CallbackQuery, callback_data: dict, state: FSMContext
    ) -> None:
        await CategoryStates.name.set()
        await state.update_data(id=callback_data.get("id", "root"))
        await query.message.answer(text=self.texts.get_name)

    async def save_name(self, message: Message, state: FSMContext) -> None:
        await self.chain.chain_start_write(CategoryStates.description)
        await state.update_data(name=message.html_text)
        await message.answer(
            text=self.texts.get_description,
            reply_markup=self.buttons._save_description(
                self.texts.btn_save_description
            ),
        )

    async def save_category(self, query: CallbackQuery, state: FSMContext) -> None:
        async with state.proxy() as data:
            parent_id = data["id"]
            name = data["name"]
        description = await self.chain.chain_finish_write(state)

        for _ in range(20):
            new_category = await self.repo.add_category(
                category=CategoryModel(
                    parent_id=parent_id, name=(name + str(_)), description=description
                )
            )

        if new_category:
            await query.message.answer(text=self.texts.gategory_saved)

            await self.get_category(query, callback_data={"id": new_category.id})
        else:
            await query.message.answer(text=self.texts.error_saving)

    async def delete_category(self, query: CallbackQuery, callback_data: dict) -> None:
        id = callback_data["id"]
        category = await self.repo.get_category(doc_id=id)
        if category:
            subs = await self.repo.get_subcategories(id)
            if subs:
                await query.message.answer(
                    text=self.texts.save_subcategories,
                    reply_markup=self.buttons.save_subcategories(
                        (
                            self.texts.save_subcategories_btn_yes,
                            self.texts.save_subcategories_btn_no,
                            self.texts.btn_cancel_delete,
                        ),
                        id=id,
                    ),
                )
            else:
                await self.repo.delete_category(id)

                await query.message.edit_text(self.texts.deleted_with_subs)
                await self.get_category(query, callback_data={"id": category.parent_id})

    async def delete_confirmation(
        self, query: CallbackQuery, callback_data: dict
    ) -> None:
        choice = callback_data["type"]
        id = callback_data["id"]
        category = await self.repo.get_category(id)

        if not category:
            await query.answer(self.texts.error_found)
            return
        match choice:
            case "delete_subs":
                await self.repo.delete_category(id)
                await query.message.answer(self.texts.deleted_with_subs)
            case "save_subs":
                await self.repo.delete_category(id, saveChilderns=True)
                await query.message.answer(self.texts.deleted_without_subs)
            case _:
                await query.message.answer(self.texts.btn_cancel_delete)
        await self.get_category(query, callback_data={"id": category.parent_id})

    async def edit_name(
        self, query: CallbackQuery, state: FSMContext, callback_data: dict
    ) -> None:
        id = callback_data["id"]
        await CategoryStates.edit_name.set()
        await state.update_data(id=id)
        await state.update_data(query=query.to_python())
        await query.message.answer(self.texts.get_new_name)

    async def edit_description(
        self, query: CallbackQuery, state: FSMContext, callback_data: dict
    ) -> None:
        id = callback_data["id"]
        await self.chain.chain_start_write(CategoryStates.edit_description)
        await state.update_data(id=id)
        await state.update_data(query=query.to_python())
        await query.message.answer(
            self.texts.get_new_description,
            reply_markup=self.buttons._save_description(self.texts.get_new_description),
        )

    async def save_new_name(self, message: Message, state: FSMContext) -> None:
        data = await state.get_data()
        await state.finish()
        name = message.html_text
        category = await self.repo.update_name_category(data["id"], name)
        if category:
            await message.answer(self.texts.name_updated)
            await self.get_category(CallbackQuery.to_object(data["query"]), data)
        else:
            await message.answer(self.texts.error_updating)

    async def save_new_description(self, message: Message, state: FSMContext) -> None:
        data = await state.get_data()
        description = await self.chain.chain_finish_write(state)
        category = await self.repo.update_desciption_category(data["id"], description)
        if category:
            await message.answer(self.texts.description_updated)
            await self.get_category(CallbackQuery.to_object(data["query"]), data)
        else:
            await message.answer(self.texts.error_updating)

    async def save_extra():
        raise NotImplemented

    async def edit_extra():
        raise NotImplemented

    async def save_new_extra():
        raise NotImplemented

    async def delete_extra():
        raise NotImplemented
