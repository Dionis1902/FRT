import logging
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException, Depends, APIRouter
from fastapi.responses import JSONResponse
from opentele.td import Account
from add_accounts.base import AddAccount
from db import database
from settings import Settings
from web.connection_manager import ConnectionManager
from web.routes import html, api, login
from db.models import tasks as tasks_model, Status
from web.routes.api import accounts, tasks
from web.utils import check_user, validate_api_data
from starlette.responses import RedirectResponse


def update_api_setter(self, value):
    self.__api = value


setattr(Account, 'api', property(Account.api.fget, update_api_setter))

app = FastAPI()

protected_app = APIRouter(dependencies=[Depends(login.login_manager), Depends(validate_api_data)])


logging.Formatter.converter = time.gmtime


@app.on_event('startup')
async def startup():
    await database.connect()
    await Settings.load()
    await database.execute(tasks_model.update().values(status=Status.KILLED.value).where(tasks_model.c.status == Status.PROGRESS.value))


@app.on_event('shutdown')
async def shutdown():
    await database.disconnect()
    await Settings.save()


@protected_app.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    manager = ConnectionManager(**(await websocket.receive_json()), websocket=websocket)
    await manager.send_data(lock_buttons=AddAccount.in_progress(), update_or_create_progress=AddAccount.progress())
    try:
        await manager.broadcast_data()
    except WebSocketDisconnect:
        await manager.disconnect()


@app.exception_handler(401)
async def need_login(*_):
    return RedirectResponse(url='/login')


@app.exception_handler(404)
async def not_found_exception(request: Request, error: HTTPException):
    if not request.url.path.startswith('/api'):
        return html.templates.TemplateResponse('errors/404.html', {'request': request})
    return JSONResponse(status_code=404, content={'detail': error.detail})


@app.exception_handler(418)
async def go_to_settings(*_, user=Depends(login.login_manager)):
    return RedirectResponse('/settings')


protected_app.include_router(api.router)
protected_app.include_router(html.router)
app.include_router(login.router)
app.include_router(protected_app)
