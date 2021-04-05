from aiogram import types, Bot
from aiogram.utils.markdown import escape_md

class custom_handler:
    can_send = True

    @staticmethod
    async def start_handler(event: types.Message):
        pass

    @staticmethod
    async def message_handler(event: types.Message):
        pass

    @staticmethod
    async def send_to(bot: Bot, message):
        response: types.Message = await bot.send_message(message['chat_id'],
                                                         text=f"*{message['author']}* поделился\\(\\-лась\\) новостью\\!\n"
                                                              f"\n"
                                                              f"{escape_md(message['short_text'])}\n"
                                                              f"\n"
                                                              f"Читать далее: {escape_md(message['link'])}",
                                                         parse_mode=types.ParseMode.MARKDOWN_V2
                                                         )
        return response

    @staticmethod
    async def edit(bot: Bot, message):
        response: types.Message = await bot.edit_message_text(chat_id=message['chat_id'],
                                                              message_id=message['message_id'],
                                                              text=f"*{message['author']}* поделился\\(\\-лась\\) новостью\\!\n"
                                                                   f"\n"
                                                                   f"{escape_md(message['short_text'])}\n"
                                                                   f"\n"
                                                                   f"Читать далее: {escape_md(message['link'])}",
                                                              parse_mode=types.ParseMode.MARKDOWN_V2)
        return response
