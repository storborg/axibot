import logging

import aiohttp
from aiohttp import web

from . import api, plotting
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


def notify_of_new_document(app):
    for ws in app['clients']:
        msg = api.NewDocumentMessage()
        ws.send_str(msg.serialize())


def set_document(app, f):
    assert app['state'] == State.idle
    app['state'] = State.processing
    orig_actions = app['actions']
    app['actions'] = []

    # Notify all clients we are now processing
    update_all_client_state(app)

    try:
        svgdoc = f.read()
        actions = plotting.process_upload(svgdoc)

    except Exception as e:
        app['state'] = State.idle
        app['actions'] = orig_actions
        update_all_client_state(app)
        raise

    app['document'] = svgdoc
    app['actions'] = actions
    app['state'] = State.idle
    # Notify all clients we are now idle and ready to plot
    update_all_client_state(app)


async def handle_user_message(app, ws, msg):
    if isinstance(msg, api.SetDocumentMessage):
        assert app['state'] == State.idle
        # XXX set new active document

    elif isinstance(msg, api.ManualPenUpMessage):
        assert app['state'] in (State.idle, State.paused)
        plotting.manual_pen_up(app)

    elif isinstance(msg, api.ManualPenDownMessage):
        assert app['state'] in (State.idle, State.paused)
        plotting.manual_pen_down(app)

    elif isinstance(msg, api.PausePlottingMessage):
        assert app['state'] == State.plotting
        plotting.pause(app)
        update_all_client_state(app)

    elif isinstance(msg, api.ResumePlottingMessage):
        assert app['state'] in (State.idle, State.paused)
        plotting.resume(app)
        update_all_client_state(app)

    elif isinstance(msg, api.CancelPlottingMessage):
        assert app['state'] in (State.plotting, State.paused)
        plotting.cancel(app)
        update_all_client_state(app)

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
