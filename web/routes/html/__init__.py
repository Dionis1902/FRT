from fastapi import APIRouter, Request, Depends, HTTPException
from starlette.templating import Jinja2Templates

from db import database
from db.models import tasks
from functions import FUNCTIONS
from settings import Settings
from web.utils import depends_account, depends_function

router = APIRouter(include_in_schema=False)

templates = Jinja2Templates(directory='web/templates')


@router.get('/')
async def index(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})


@router.get('/accounts')
async def get_accounts(request: Request):
    return templates.TemplateResponse('accounts/index.html', {'request': request})


@router.get('/accounts/{user_id}')
async def get_account(request: Request, account=Depends(depends_account)):
    return templates.TemplateResponse('account/index.html', {'request': request, 'account': account, 'settings': Settings})


@router.get('/settings')
async def get_settings(request: Request):
    return templates.TemplateResponse('settings.html', {'request': request, 'settings': Settings})


@router.get('/functions')
async def get_functions(request: Request):
    return templates.TemplateResponse('functions/index.html', {'request': request, 'functions': FUNCTIONS.values()})


@router.get('/functions/{function_id}')
async def get_function(request: Request, function=Depends(depends_function)):
    return templates.TemplateResponse('functions/function.html', {'request': request, 'function': function})


@router.get('/tasks')
async def get_tasks(request: Request):
    return templates.TemplateResponse('tasks/index.html', {'request': request})


@router.get('/tasks/{task_id}')
async def get_tasks(request: Request, task_id: int):
    task = await database.fetch_one(tasks.select().where(tasks.c.id == task_id))
    if not task:
        raise HTTPException(404)
    return templates.TemplateResponse('tasks/task.html', {'request': request, 'task': task})
