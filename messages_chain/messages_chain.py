from typing import List
from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State
from aiogram.types import ContentType, InlineKeyboardMarkup, MediaGroup, Message
from .aiogram_media_group import media_group_handler

from .chain_model import ChainModel
from .chain_repo import ChainRepo, MemoryConnection,MongoConnection,RedisConnection





class MessagesChain:
    """ General Repository


    Args:
        storage: Dispatcher from aiogram (use storage defined in aiogram)  OR  put concret storage
        prefix: Name Collection
    Example:
        Base Usage
        '''Python

        from aiogram import Dispatcher
        from messages_chain import MessageChain

        bot = Bot(token=bot_token)
        dp = Dispatcher(bot)
        chain = MessageChain(storage=dp)
        chain
        '''
        Recommend Usage
        '''Python
        Call Chain in any place

        from messages_chain import MessageChain, Storages
        chain = MessageChain(storage=Storages.MONGO)

        AND
        Register chain in message handler as function
        from aiogram import Dispatcher
        from aiogram.types import ContentType
        from messages_chain import MessageChain

        bot = Bot(token=bot_token)
        dp = Dispatcher(bot)
        dp.register_message_handler(
        chain.chain_write,
        state=cast_state.record_chain,
        content_types=ContentType.all(),
        )
        OR as call with decorator
        @dp.message_handler(state=cast_state.record_chain,content_types=ContentType.all())
        async def my_chain(message: Message):
            await messages_chain.chain_write(message)
        '''

    """
    def __init__(self,storage: Dispatcher | MemoryConnection| RedisConnection | MongoConnection, prefix: str = "messages_chain") -> None:

        self.repo =ChainRepo(storage=storage, storage_prefix=prefix).init()




    @property
    def repository(self) -> ChainRepo:
        return self.repo


    async def chain_start_write(self, state: State) -> None:
        await state.set()
        await self.repo.delete_all()


    @media_group_handler(only_album=False)
    async def chain_write(self,message: List[Message]) -> None:
        """ Use ONLY

        Args:
            message (List[Message]): _description_
        """
        module = self.repo
        text = None
        if len(message) > 1:
            types = list(_.content_type for _ in message)
            ids = []
            data_id = None
            for data in message:

                match data.content_type:
                    case ContentType.PHOTO:
                        data_id = data.photo[-1].file_id
                    case ContentType.VIDEO:
                        data_id = data.video.file_id
                    case ContentType.DOCUMENT:
                        data_id = data.document.file_id
                    case  ContentType.TEXT:
                        data_id = None

                ids.append(data_id)
            text_list = list(_.html_text for _ in message if _.caption)
            text = None
            if text_list:
                text = text_list[0]
            await module.add_message(
                ChainModel(
                    is_media_group=True,
                    content_type=types,
                    data_id=ids,
                    text=text,
                )
            )
            return
        elif bool(getattr(message[0], "caption")) or bool(getattr(message[0], "text")):
            text = message[0].html_text

        msg = message[0]
        data_id = None
        match msg.content_type:
            case ContentType.PHOTO:
                data_id = msg.photo[-1].file_id
            case ContentType.VIDEO:
                data_id = msg.video.file_id
            case ContentType.DOCUMENT:
                data_id = msg.document.file_id
            case ContentType.TEXT:
                data_id = None
            case ContentType.STICKER:
                data_id = msg.sticker.file_id
            case ContentType.VIDEO_NOTE:
                data_id = msg.video_note.file_id
            case ContentType.VOICE:
                data_id = msg.voice.file_id

        await module.add_message(
            ChainModel(
                content_type=msg.content_type,
                data_id=data_id,
                text=text,
            )
        )

    async def chain_finish_write(self,state: FSMContext| None) -> List[ChainModel]:
        if state:
            await state.finish()
        list_descriptions = await self.repo.get_all_chain()
        return list_descriptions


    @staticmethod
    async def chain_read(
        message: Message,
        description: List[ChainModel] | None,
        markup: InlineKeyboardMarkup | None = None,
    ) -> None:
        if isinstance(description, list):
            if not markup:
                markup = None

            if not description:
                return []

            if len(description) == 1:
                last_msg = description[0]

            else:
                last_msg = description.pop()
                for msg in description:
                    text = msg.text
                    data_id = msg.data_id
                    if isinstance(msg.content_type, list) and isinstance(data_id, list):

                        media = MediaGroup()
                        medias = [
                            {"type": type, "media": id}
                            for type, id in zip(msg.content_type, msg.data_id)
                        ]
                        medias[-1] = {
                            "type": msg.content_type[-1],
                            "media": msg.data_id[-1],
                            "caption": msg.text,
                        }
                        media.attach_many(*medias)
                        await message.answer_media_group(media)

                    else:
                        match msg.content_type:
                            case ContentType.PHOTO:
                                await message.answer_photo(photo=data_id, caption=text)
                            case ContentType.VIDEO:
                                await message.answer_video(video=data_id, caption=text)
                            case ContentType.DOCUMENT:
                                await message.answer_document(
                                    document=data_id, caption=text
                                )
                            case ContentType.TEXT:
                                if text:
                                    await message.answer(text=text)
                            case ContentType.STICKER:
                                await message.answer_sticker(sticker=data_id)
                            case ContentType.VIDEO_NOTE:
                                await message.answer_video_note(video_note=data_id)
                            case ContentType.VOICE:
                                await message.answer_voice(voice=data_id)

            if isinstance(last_msg.content_type, list):

                media = MediaGroup()
                medias = [
                    {"type": type, "media": id}
                    for type, id in zip(last_msg.content_type, last_msg.data_id)
                ]
                medias[-1] = {
                    "type": last_msg.content_type[-1],
                    "media": last_msg.data_id[-1],
                    "caption": last_msg.text,
                }
                media.attach_many(*medias)
                await message.answer_media_group(media)
                text = "__"
                await message.answer(text=text, reply_markup=markup)
            data_id = last_msg.data_id
            text = "__"
            if last_msg.text:
                text = last_msg.text
            match last_msg.content_type:
                case ContentType.PHOTO:
                    await message.answer_photo(
                        photo=data_id, caption=text, reply_markup=markup
                    )
                case ContentType.VIDEO:
                    await message.answer_video(
                        video=data_id, caption=text, reply_markup=markup
                    )
                case ContentType.DOCUMENT:
                    await message.answer_document(
                        document=data_id, caption=text, reply_markup=markup
                    )
                case ContentType.TEXT:
                    await message.answer(text=text, reply_markup=markup)
                case ContentType.STICKER:
                    await message.answer_sticker(sticker=data_id, reply_markup=markup)
                case ContentType.VIDEO_NOTE:
                    await message.answer_video_note(
                        video_note=data_id, reply_markup=markup
                    )
                case ContentType.VOICE:
                    await message.answer_voice(voice=data_id, reply_markup=markup)
        else:
            await message.answer(
                "Нет описания, задай описание в настройках курса/плана",
                reply_markup=markup,
            )
