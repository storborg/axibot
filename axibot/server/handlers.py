import logging

import aiohttp
from aiohttp import web

from . import api

log = logging.getLogger(__name__)


async def client_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    app = request.app

    log.info("Client connected.")
    clients = app['clients']
    clients.add(ws)

    state = request.app['state']
    log.info("Current state is %s.", state)
    msg = api.StateMessage(state=state)
    ws.send_str(msg.serialize())

    try:
        async for msg in ws:
            if msg.tp == aiohttp.MsgType.binary:
                log.info("User message: %s", msg)
            elif msg.tp == aiohttp.MsgType.closed:
                break
            elif msg.tp == aiohttp.MsgType.error:
                log.info("User websocket error: %s", msg)
                break
            else:
                log.error("Unknown user message type: %s, ignoring.", msg.tp)
    finally:
        log.info("Client connection closed.")
        clients.remove(ws)

    return ws
