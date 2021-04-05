from aiogram import types, Bot
from database import User


class custom_handler:

    can_send = True

    @staticmethod
    async def start_handler(event: types.Message):
        if not User.get(event.from_user.id):
            new_user = User(user_id=event.from_user.id, first_name=event.from_user.first_name,
                            last_name=event.from_user.last_name, username=event.from_user.username,
                            platform='telegram')
            new_user.save()
        await event.answer(text=f"Hello from custom_handler(). ID %s" % event.message_id)

    @staticmethod
    async def message_handler(event: types.Message):
        await event.reply(text="You said: %s" % event.text)

    @staticmethod
    async def send_to(bot: Bot, message):
        response: types.Message = await bot.send_message(message['chat_id'],
                                         text="Мне тут просили передать, что ты пидар, или %s" % message['body'])
        return response

    @staticmethod
    async def edit(bot: Bot, message):
        try:
            response: types.Message = await bot.edit_message_text(chat_id=message['chat_id'],
                                                                message_id=message['message_id'],
                                                                text=message['body'])
            return response
        except Exception as e:
            return dict(success=False, detail=str(e))