from typing import List

from aiogram.dispatcher import FSMContext
from aiogram.types import ContentType, InlineKeyboardMarkup, MediaGroup, Message
from aiogram_media_group import media_group_handler
from .chain_model import ChainModel


class MessagesChain:
    @staticmethod
    async def chain_start_write() -> None:
        await ShopSetup.edit_description.set()
        await _chain_repo.delete_all()

    @staticmethod
    @media_group_handler(only_album=False)
    async def chain_write(message: List[Message]) -> None:
        module = _chain_repo
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
            await module.add_descr(
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

        await module.add_descr(
            ChainModel(
                content_type=msg.content_type,
                data_id=data_id,
                text=text,
            )
        )

    @staticmethod
    async def chain_finish_write(state: FSMContext) -> List[ChainModel]:
        await state.finish()
        list_descriptions = await _chain_repo.get_all_descr()
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
