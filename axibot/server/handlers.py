import logging

import aiohttp
from aiohttp import web

from . import api, plotting
from .state import State

log = logging.getLogger(__name__)


def broadcast(app, msg, exclude_client=None):
    s = msg.serialize()
    for ws in app['clients']:
        if ws != exclude_client:
            ws.send_str(s)


def notify_state(app, specific_client=None, exclude_client=None):
    state = app['state']
    num_actions = len(app['job'])
    action_index = app['action_index']
    msg = api.StateMessage(
        state=state.name,
        num_actions=num_actions,
        action_index=action_index,
        estimated_time=app['estimated_time'],
        consumed_time=app['consumed_time'],
        x=app['position'][0],
        y=app['position'][1],
        pen_up=app['pen_up'],
    )
    if specific_client:
        specific_client.send_str(msg.serialize())
    else:
        broadcast(app, msg, exclude_client=exclude_client)


def notify_new_document(app, exclude_client=None):
    msg = api.NewDocumentMessage(document=app['document'])
    broadcast(app, msg, exclude_client=exclude_client)


def notify_error(app, to_client, s):
    msg = api.ErrorMessage(s)
    to_client.send_str(msg.serialize())


def notify_job_complete(app):
    log.info("Notifying clients of completed job. Est: %s, Actual: %s.",
             app['estimated_time'], app['consumed_time'])
    msg = api.CompletedJobMessage(estimated_time=app['estimated_time'],
                                  actual_time=app['consumed_time'])
    broadcast(app, msg)


async def handle_user_message(app, ws, msg):
    if isinstance(msg, api.SetDocumentMessage):
        assert app['state'] == State.idle
        try:
            app['state'] = State.processing
            notify_state(app)
            job = await plotting.process_upload_background(app, msg.document)
        except Exception as e:
            notify_error(app, ws, str(e))
        else:
            app['document'] = job.document
            app['job'] = job
            app['estimated_time'] = job.duration().total_seconds()
            notify_new_document(app, exclude_client=ws)
        finally:
            app['state'] = State.idle
            notify_state(app)

    elif isinstance(msg, api.ManualPenUpMessage):
        assert app['state'] == State.idle
        plotting.manual_pen_up(app)

    elif isinstance(msg, api.ManualPenDownMessage):
        assert app['state'] == State.idle
        plotting.manual_pen_down(app)

    elif isinstance(msg, api.ResumePlottingMessage):
        assert app['state'] == State.idle
        plotting.resume(app)
        notify_state(app)

    elif isinstance(msg, api.CancelPlottingMessage):
        assert app['state'] == State.plotting
        plotting.cancel(app)
        notify_state(app)

    else:
        log.error("Unknown user message: %s, ignoring.", msg)


async def client_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    app = request.app

    log.info("Client connected.")
    clients = app['clients']
    clients.add(ws)

    notify_state(app, specific_client=ws)

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
