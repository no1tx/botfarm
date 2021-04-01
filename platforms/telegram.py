import logging
import json
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiohttp import ClientSession, BasicAuth
from database import User, Message
from database import Bot as BotModel

LOG_FORMAT = ('%(asctime)s,%(msecs)d %(levelname)s: %(message)s')
LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)

__platform__ = 'telegram'

http_session = ClientSession()


class TelegramBot(object):
    def __init__(self, bot_model: BotModel):
        self.bot = bot_model
        LOGGER.log(logging.INFO, msg=f'Starting Telegram bot %s' % self.bot.name)
        self.Bot = Bot(token=self.bot.token)
        self.Dispatcher = Dispatcher(bot=self.Bot)
        if self.bot.custom_handler:
            self.Dispatcher.register_message_handler(self.bot.custom_handler.start_handler,
                                                     commands={"start", "restart", "stop"})
            self.Dispatcher.register_message_handler(self.bot.custom_handler.message_handler)
            LOGGER.log(logging.INFO, msg='Registered bot with custom handler %s' % self.bot.custom_handler)
        else:
            self.Dispatcher.register_message_handler(self.start_handler, commands={"start", "restart", "stop"})
            self.Dispatcher.register_message_handler(self.message_handler)
            LOGGER.log(logging.INFO, msg='Registered bot without custom handlers.')

    async def send_to(self, chat_id, body, as_html=False, as_markdown_v2=False):
        user = User.get(chat_id)
        if int(chat_id) > 0 and user or int(chat_id) < 0:
            try:
                if as_html:
                    await self.Bot.send_message(chat_id=chat_id, text=body, parse_mode=types.ParseMode.HTML)
                elif as_markdown_v2:
                    await self.Bot.send_message(chat_id=chat_id, text=body, parse_mode=types.ParseMode.MARKDOWN_V2)
                else:
                    await self.Bot.send_message(chat_id=chat_id, text=body)
            except Exception as e:
                LOGGER.log(logging.INFO, msg="Failed to send message, because %s" % e)
        else:
            LOGGER.log(logging.INFO, msg="Failed to send message, because user is not started bot")

    async def start_handler(self, event: types.Message):
        LOGGER.log(logging.INFO, msg='Got start command from %s:%s' % (self.bot.platform, event.from_user.username))
        if not User.get(event.from_user.id):
            new_user = User(user_id=event.from_user.id, first_name=event.from_user.first_name,
                            last_name=event.from_user.last_name, username=event.from_user.username,
                            platform=self.bot.platform)
            new_user.save()
        if self.bot.start_callback:
            message = json.dumps(dict(bot=self.bot.name, chat_id=event.from_user.id, command=event.get_command()))
            if self.bot.callback_auth:
                await http_session.post(self.bot.start_callback,
                                        auth=BasicAuth(self.bot.callback_login, self.bot.callback_password),
                                        data=message)
            else:
                await http_session.post(self.bot.start_callback, data=message)
        else:
            if self.bot.start_message:
                await event.answer(self.bot.start_message)

    async def message_handler(self, event: types.Message):
        user = User.get(event.from_user.id)
        LOGGER.log(logging.INFO, msg='Fetched message from %s' % user.username)
        new_message = Message(date=datetime.now(), sender=user.username, body=event.text, recipient=self.bot.name,
                              message_id=event.message_id, processed=True)
        new_message.save()
        if self.bot.message_callback:
            message = json.dumps(dict(bot=self.bot.name, chat_id=event.from_user.id, body=event.text))
            if self.bot.callback_auth:
                await http_session.post(self.bot.start_callback,
                                        auth=BasicAuth(self.bot.callback_login, self.bot.callback_password),
                                        data=message)
            else:
                await http_session.post(self.bot.start_callback, data=message)
        else:
            if self.bot.default_response:
                await event.answer(self.bot.default_response)

    async def start_polling(self):
        await self.Dispatcher.start_polling()

    async def close(self):
        await self.Bot.close()
        self.bot.delete()


__default_class__ = TelegramBot
