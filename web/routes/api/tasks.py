import os

import aiofiles
from fastapi import APIRouter, Request, Depends, Response

from db import database
from db.models import tasks
from functions.base_function import Base
from web.utils import depends_function

router = APIRouter(prefix='/tasks', tags=['Tasks'])


@router.get('/')
async def get_tasks():
    return await database.fetch_all(tasks.select().order_by(tasks.c.id))


@router.post('/{function_id}')
async def create_task(request: Request, function=Depends(depends_function)):
    data = await request.json()
    func = function['class_'](**data)
    task_id = await func.save_task()
    return {'task_id': task_id}


@router.delete('/{task_id}')
async def stop_task(task_id: int):
    return dict(status=await Base.stop(task_id))


@router.get('/log/{task_id}')
async def get_tasks(task_id: int):
    log_file = os.path.join(os.getcwd(), 'data', 'logs', f'task_{task_id}.log')
    if os.path.isfile(log_file):
        try:
            async with aiofiles.open(log_file, 'r', encoding='utf-8') as f:
                return Response(content=await f.read(), media_type='text/plain')
        except (Exception, ):
            pass
    return Response(status_code=404)
