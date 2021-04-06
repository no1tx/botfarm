import logging
import json
import importlib
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiohttp import ClientSession, BasicAuth
from database import User, Message
from database import Bot as BotModel

LOG_FORMAT = '%(asctime)s,%(msecs)d %(levelname)s: %(message)s'
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
            self.handler = getattr(importlib.import_module('handlers.' + self.bot.custom_handler),
                                   'custom_handler')
            self.Dispatcher.register_message_handler(self.handler.start_handler,
                                                     commands={"start", "restart", "stop"})
            self.Dispatcher.register_message_handler(self.handler.message_handler)
            LOGGER.log(logging.INFO, msg='Registered bot with custom handler %s' % self.bot.custom_handler)
        else:
            self.Dispatcher.register_message_handler(self.start_handler, commands={"start", "restart", "stop"})
            self.Dispatcher.register_message_handler(self.message_handler)
            LOGGER.log(logging.INFO, msg='Registered bot without custom handlers.')

    async def send_to(self, message, as_html=False, as_markdown_v2=False):
        user = User.get(message['chat_id'])
        if int(message['chat_id']) > 0 and user or int(message['chat_id']) < 0:
            if self.handler.can_send:
                try:
                    result: types.Message = await self.handler.send_to(self.Bot, message)
                    return dict(success=True, message_id=result.message_id)
                except Exception as e:
                    return dict(success=False, detail=str(e))
            else:
                try:
                    if as_html:
                        result: types.Message = await self.Bot.send_message(chat_id=message['chat_id'],
                                                                            text=message['body'],
                                                                            parse_mode=types.ParseMode.HTML)
                    elif as_markdown_v2:
                        result: types.Message = await self.Bot.send_message(chat_id=message['chat_id'],
                                                                            text=message['body'],
                                                                            parse_mode=types.ParseMode.MARKDOWN_V2)
                    else:
                        result: types.Message = await self.Bot.send_message(chat_id=message['chat_id'],
                                                                            text=message['body'])
                    return dict(success=True, message_id=result.message_id)
                except Exception as e:
                    LOGGER.log(logging.INFO, msg="Failed to send message, because %s" % e)
                    return dict(success=False, detail=e, teapot=True)
        else:
            if self.handler.can_send:
                try:
                    result: types.Message = await self.handler.send_to(self.Bot, message)
                    return dict(success=True, message_id=result.message_id)
                except Exception as e:
                    return dict(success=False, detail=str(e))
            else:
                LOGGER.log(logging.INFO, msg="Failed to send message, because user is not started bot")
                return dict(success=False, detail="not started by user, cannot send")

    async def edit(self, message):
        LOGGER.log(logging.INFO, msg="Request to edit message %s in chat %s" % (message['message_id'],
                                                                                message['chat_id']))
        if self.bot.custom_handler:
            result = await self.handler.edit(self.Bot, message)
            return dict(success=True, message_id=result.message_id)
        else:
            try:
                result: types.Message = await self.Bot.edit_message_text(chat_id=message['chat_id'],
                                                                         message_id=message['message_id'],
                                                                         text=message['body'])
                return dict(success=True, message_id=result.message_id)
            except Exception as e:
                return dict(success=False, detail=str(e))

    async def start_handler(self, event: types.Message):
        LOGGER.log(logging.INFO, msg='Got start command from %s:%s' % (self.bot.platform, event.from_user.username))
        if not User.get(event.from_user.id):
            new_user = User(user_id=event.from_user.id, first_name=event.from_user.first_name,
                            last_name=event.from_user.last_name, username=event.from_user.username,
                            platform=self.bot.platform)
            new_user.save()
        else:
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
        await self.Bot.close_bot()
        self.bot.delete()


__default_class__ = TelegramBot
