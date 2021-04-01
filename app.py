import logging
import asyncio
from process import run_bot_farm

LOG_FORMAT = ('%(asctime)s,%(msecs)d %(levelname)s: %(message)s')
LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)

if __name__ == '__main__':
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)
    event_loop.create_task(run_bot_farm())
    event_loop.run_forever()