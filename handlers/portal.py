import logging
import json
from aiogram import types, Bot
from aiogram.utils.markdown import escape_md
from aiohttp import ClientSession
from handlers.portal_params import bot_name, avatar_url, discord_webhook_url

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
                                                              f"{escape_md(message['short_text']).replace('&nbsp;', '')}\n"
                                                              f"\n"
                                                              f"Читать далее: {escape_md(message['link'])}",
                                                         parse_mode=types.ParseMode.MARKDOWN_V2
                                                         )
        embeds = dict(title="Читать пост на портале", description=f"{message['short_text'].replace('&nbsp;', '')})",
                      url=message['link'], author=dict(name=message['author']))
        discord_data = json.dumps({"username": bot_name,
                                   "avatar_url": avatar_url, "embeds": [embeds]})
        async with ClientSession() as session:
            async with session.post(discord_webhook_url, data=discord_data,
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
                                                                   f"Читать далее: {escape_md(message['link'])}\n"
                                                                   f"\n"
                                                                   f"❤ Этот пост понравился {message['likes']} людям\\.",
                                                              parse_mode=types.ParseMode.MARKDOWN_V2)
        return response
