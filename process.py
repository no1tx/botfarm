from fastapi import FastAPI, Request, HTTPException
from fastapi.encoders import jsonable_encoder
from database import Bot
import traceback
import json
import logging
import importlib
import asyncio
import random
from uvicorn import Config, Server

LOG_FORMAT = '%(asctime)s,%(msecs)d %(levelname)s: %(message)s'
LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)

app = FastAPI(title='botfarm')

running_bots = dict()


async def start_all_bots():
    bots = Bot.get_all()
    if bots:
        for bot_model in bots:
            bot_module = getattr(importlib.import_module('platforms.' + bot_model.platform), '__default_class__')
            bot = bot_module(bot_model)
            loop = asyncio.get_running_loop()
            loop.create_task(bot.start_polling())
            running_bots[bot_model.name] = bot
    else:
        LOGGER.log(logging.INFO, msg='Please add bot in the database. There is nothing to start.')


@app.post('/api/bot/add')
async def add_bot(request: Request):
    request_body = b''
    async for chunk in request.stream():
        request_body += chunk
    message = json.loads(request_body)
    access_token = ''.join(random.choice('0123456789abcdef') for n in range(16))
    try:
        if message['name'] and message['token'] and message['platform']:
            if message['custom_handler']:
                bot_model = Bot(name=message['name'], platform=message['platform'], token=message['token'],
                                custom_handler=message['custom_handler'], access_token=access_token)
            elif message['start_message'] and message['default_response']:
                bot_model = Bot(name=message['name'], platform=message['platform'], token=message['token'],
                                start_message=message['start_message'], default_response=message['default_response'],
                                custom_handler=None, access_token=access_token)
            elif message['start_callback'] and message['message_callback']:
                if message['callback_auth'] and message['callback_login'] and message['callback_password']:
                    bot_model = Bot(name=message['name'], platform=message['platform'], token=message['token'],
                                    custom_handler=None, start_callback=message['start_callback'],
                                    message_callback=message['message_callback'], callback_auth=True,
                                    callback_login=message['callback_login'],
                                    callback_password=message['callback_password'], access_token=access_token)
                else:
                    bot_model = Bot(name=message['name'], platform=message['platform'], token=message['token'],
                                    custom_handler=None, start_callback=message['start_callback'],
                                    message_callback=message['message_callback'], access_token=access_token)
            else:
                bot_model = Bot(name=message['name'], platform=message['platform'],
                                token=message['token'], access_token=access_token)

            bot_model.save()
            bot_module = getattr(importlib.import_module('platforms.' + bot_model.platform), '__default_class__')
            bot = bot_module(bot_model)
            loop = asyncio.get_running_loop()
            loop.create_task(bot.start_polling())
            running_bots[bot_model.name] = bot
            return jsonable_encoder(dict(success=True, message="Bot registered and started.",
                                         access_token=bot_model.access_token))
    except KeyError as e:
        raise HTTPException(status_code=400, detail=dict(need_value=e.args))
    except Exception as e:
        LOGGER.log(logging.INFO, msg="Failed to start new bot because %s" % e)
        raise HTTPException(status_code=500)


@app.post('/api/bot/{name}/send')
async def send_message(request: Request, name):
    if not name:
        raise HTTPException(status_code=400, detail='You need to provide bot name')
    else:
        request_body = b''
        async for chunk in request.stream():
            request_body += chunk
        message = json.loads(request_body)
        if message['access_token'] == running_bots[name].bot.access_token:
            if message['chat_id']:
                try:
                    result = await running_bots[name].send_to(message)
                    return jsonable_encoder(result)
                except Exception as e:
                    LOGGER.log(logging.INFO, msg='Failed to process send request because %s' % e)
                    return HTTPException(status_code=500, detail=jsonable_encoder(e))
        else:
            raise HTTPException(status_code=403, detail="Access denied.")


@app.post('/api/bot/{name}/edit')
async def edit_message(request: Request, name):
    if not name:
        raise HTTPException(status_code=400, detail='You need to provide bot name')
    else:
        request_body = b''
        async for chunk in request.stream():
            request_body += chunk
        message = json.loads(request_body)
        if message['access_token'] == running_bots[name].bot.access_token:
            result = await running_bots[name].edit(message)
            return jsonable_encoder(result)


@app.post('/api/bot/{name}/remove')
async def stop(request: Request, name):
    if not name:
        raise HTTPException(status_code=400, detail='You need to provide bot name')
    else:
        request_body = b''
        async for chunk in request.stream():
            request_body += chunk
        message = json.loads(request_body)
        if message['access_token'] == running_bots[name].bot.access_token:
            running_bots[name].close()
            del running_bots[name]


async def run_bot_farm():
    loop = asyncio.get_running_loop()
    loop.create_task(start_all_bots())
    server = web_app(loop)
    loop.create_task(server.serve())


def web_app(loop):
    config = Config(app=app, loop=loop, port=8001, host='0.0.0.0')
    server = Server(config)
    return server


if __name__ == '__main__':
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)
    event_loop.create_task(run_bot_farm())
    event_loop.run_forever()
