import logging
import json
from aiogram import types, Bot
from aiogram.utils.markdown import escape_md
from aiohttp import ClientSession
import portal_params


LOG_FORMAT = '%(asctime)s,%(msecs)d %(levelname)s: %(message)s'
LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)


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
        embeds = dict(title="Читать пост на портале", description=f"{message['short_text']})",
                      url=message['link'], author=dict(name=message['author']))
        discord_data = json.dumps({"username": "Ебалай Лама", "embeds": [embeds]})
        async with ClientSession() as session:
            async with session.post(portal_params.discord_webhook_url, data=discord_data,
                                    headers={'Content-Type': 'application/json'}) as hook_response:
                LOGGER.log(logging.INFO, msg="Done POST to Discord Portal Webhook, status: %s" % hook_response.status)
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
