import logging

import aiohttp
from aiohttp import web

from . import api
from .state import State

log = logging.getLogger(__name__)


def update_client_state(app, ws):
    state = app['state']
    num_actions = len(app['actions'])
    action_index = app['action_index']
    msg = api.StateMessage(
        state=state.name,
        num_actions=num_actions,
        action_index=action_index,
    )
    ws.send_str(msg.serialize())


def update_all_client_state(app):
    for ws in app['clients']:
        update_client_state(app, ws)


async def handle_user_message(app, ws, msg):
    if isinstance(msg, api.SetDocumentMessage):
        assert app['state'] == State.idle
        # XXX set new active document

    elif isinstance(msg, api.ManualPenUpMessage):
        assert app['state'] in (State.idle, State.processing, State.paused)
        app['bot'].pen_up(1000)

    elif isinstance(msg, api.ManualPenDownMessage):
        assert app['state'] in (State.idle, State.processing, State.paused)
        app['bot'].pen_down(1000)

    elif isinstance(msg, api.PausePlottingMessage):
        assert app['state'] == State.plotting
        # XXX pause the plotter

    elif isinstance(msg, api.ResumePlottingMessage):
        assert app['state'] == State.paused
        # XXX resume the plotter

    elif isinstance(msg, api.CancelPlottingMessage):
        assert app['state'] in (State.plotting, State.paused)
        # XXX cancel the plotter

    else:
        log.error("Unknown user message: %s, ignoring.", msg)


async def client_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    app = request.app

    log.info("Client connected.")
    clients = app['clients']
    clients.add(ws)

    update_client_state(app, ws)

    try:
        async for raw_msg in ws:
            if raw_msg.tp == aiohttp.MsgType.text:
                msg = api.Message.deserialize(raw_msg.data)
                log.info("User message: %s", msg)
                await handle_user_message(app, ws, msg)
            elif raw_msg.tp == aiohttp.MsgType.closed:
                break
            elif raw_msg.tp == aiohttp.MsgType.error:
                log.info("User websocket error: %s", msg)
                break
            else:
                log.error("Unknown user message type: %s, ignoring.",
                          raw_msg.tp)
    finally:
        log.info("Client connection closed.")
        clients.remove(ws)

    return ws
