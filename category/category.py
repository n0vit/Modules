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
        prefix = prefix + "_categories"
        self.repo = CategoryRepo(storage=storage, storage_prefix=prefix).init()
        self.chain = MessagesChain(storage, prefix=f"{prefix}_chain")
        if texts.debug:
            texts = MessageTextModel.parse_obj(
                dict((_, _ + ":" + texts.dict()[_]) for _ in texts.dict().keys())
            )
        self.texts = texts
        self.admin_ids = admin_ids
        self.custom_buttons = buttons
        self.buttons = CategoryButtons()



    def reg_handlers(self, dispatcher: Dispatcher):
        cb = CategoryCallBackData()
        dp = dispatcher
        dp.register_callback_query_handler(self.add_category, cb.control.filter(type=['sub', 'main']))
        dp.register_callback_query_handler(self.delete_category, cb.control.filter(type='delete'))
        dp.register_callback_query_handler(self.delete_confirmation, cb.control.filter(type=['save_subs','delete_subs','cancel_deleting']))
        dp.register_callback_query_handler(self.edit_description, cb.control.filter(type='description'))
        dp.register_callback_query_handler(self.edit_name, cb.control.filter(type='name'))
        dp.register_callback_query_handler(self.get_category, cb.control.filter(type=['reorder', 'page']))
        dp.register_callback_query_handler(self.get_category, cb.category.filter())
        dp.register_message_handler(self.save_category, state=CategoryStates.description)
        dp.register_message_handler(self.save_name, state=CategoryStates.name)
        dp.register_message_handler(self.save_new_name, state=CategoryStates.edit_name)
        dp.register_message_handler(self.save_new_description, state=CategoryStates.edit_description)

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

    async def get_main_category(self, query:CallbackQuery):
        categories = await self.repo.get_subcategories('root')
        if not categories:
            await query.answer(self.texts.error_menu, cache_time=5)
        try:
            await query.message.edit_caption(self.texts.menu, reply_markup=self.buttons)
        except Exception:
            await query.message.edit_text(self.texts.menu, )

    async def get_category(self, query: CallbackQuery, callback_data: dict):
        isAdmin = query.from_user.id in self.admin_ids
        isReorder = callback_data.get("type", "") == "reorder"
        isPage = callback_data.get("type", "") == "page"
        category = None

        if isPage:
            page_number = int(callback_data.get("id", 1))
        else:
            page_number = 1 #TODO: Check
            category = await self.repo.get_category(callback_data["id"])
        if category:
            if category.description:
                try:
                    await query.message.delete()
                except Exception:
                    pass

                await self.chain.chain_read(query.message, category.description)
                subcats = await self.repo.get_subcategories(category.id)
                await query.message.answer(
                    category.name,
                    reply_markup=self.buttons.categories(
                        subcats or [],
                        isAdmin=isAdmin,
                        custom_buttons=self.buttons,
                        isReorder=isReorder,
                        page=page_number,
                        control_text=self.texts.btn_control,
                    ),
                )

            else:
                query.message.edit_text(
                    category.name,
                    reply_markup=self.buttons.categories([], isAdmin=isAdmin),
                )

    async def get_all_categories(self, id: str):
        raise NotImplemented

    async def add_category(
        self, query: CallbackQuery, callback_data: dict, state: FSMContext
    ) -> None:
        await CategoryStates.name.set()
        await state.update_data(id=callback_data.get("id", "root"))
        await state.update_data(query=query.to_python())

        await query.message.answer(text=self.texts.get_name)

    async def save_name(self, message: Message, state: FSMContext) -> None:
        state.update_data(name=message.html_text)

        await self.chain.chain_start_write(CategoryStates.description)
        await message.answer(text=self.texts.get_description)

    async def save_category(self, message: Message, state: FSMContext) -> None:
        description =  await self.chain.chain_finish_write(state)
        description = [] if message.html_text == "." else description
        name = await state.get_data("name")
        parent_id = await state.get_data("id")
        query = await state.get_data("query")
        new_category = await self.repo.add_category(category=CategoryModel(parent_id,name,description))
        if parent_id !='root' and new_category:
            await self.repo.update_subcategories(parent_id, [new_category.id])
        if new_category:
            await message.answer(text=self.texts.gategory_saved)
            await self.get_category(CallbackQuery.to_object(query), callback_data={"id":new_category.id})
        else:
            await message.answer(text=self.texts.error_saving)
        await state.finish()


    async def delete_category(self, query: CallbackQuery, callback_data: dict) -> None:
        id = callback_data["id"]
        category = await self.repo.get_category(doc_id=id)
        if category:
            if category.subcategories:
                await query.message.answer(
                    text=self.texts.save_subcategories,
                    reply_markup=CategoryButtons.save_subcategories(
                        self.texts.save_subcategories_btn_yes,
                        self.texts.save_subcategories_btn_no,
                        self.texts.btn_cancel_delete,
                    ),
                )
            else:
                await self.repo.delete_category(id)
                await query.message.answer(self.texts.deleted_with_subs)

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
        await self.get_category(query, callback_data={''})

    async def edit_name(
        self, query: CallbackQuery, state: FSMContext, callback_data: dict
    ) -> None:
        id = callback_data["id"]
        CategoryStates.edit_name.set()
        state.update_data(id=id)
        await query.message.answer(self.texts.get_new_name)

    async def edit_description(
        self, query: CallbackQuery, state: FSMContext, callback_data: dict
    ) -> None:
        id = callback_data["id"]
        self.chain.chain_start_write(CategoryStates.edit_description)
        state.update_data(id=id)
        await query.message.answer(self.texts.get_new_description)

    async def save_new_name(self, message: Message, state: FSMContext) -> None:
        id = await state.get_data("id")
        await state.finish()
        name = message.html_text
        category = await self.repo.update_name_category(id, name)
        if category:
            await message.answer(self.texts.name_updated)
            await self.get_category(id)
        else:
            await message.answer(self.texts.error_updating)

    async def save_new_description(self, message: Message, state: FSMContext) -> None:
        id = await state.get_data("id")
        description =  await self.chain.chain_finish_write(state)
        description = [] if message.html_text == "." else description
        category = await self.repo.update_desciption_category(id, description)
        if category:
            await message.answer(self.texts.description_updated)
            await self.get_category(id)
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
