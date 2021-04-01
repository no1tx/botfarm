import sys
from platforms.telegram import TelegramBot
from database import Bot as BotModel
import asyncio
from aiogram import types


class custom_handler:
    @staticmethod
    async def start_handler(event: types.Message):
        await event.answer(text=f"Hello from custom_handler(). ID %s" % event.message_id)

    @staticmethod
    async def message_handler(event: types.Message):
        await event.reply(text="You said: %s" % event.text)


async def test_bot():
    bot_model = BotModel(token=sys.argv[1], name="Test Bot", platform='telegram',
                         start_message="Hello from main()", default_response="I'm hear you.",
                         custom_handler=custom_handler)
    bot = TelegramBot(bot_model=bot_model)
    await bot.start_polling()

if __name__ == '__main__':
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)
    event_loop.create_task(test_bot())
    event_loop.run_forever()