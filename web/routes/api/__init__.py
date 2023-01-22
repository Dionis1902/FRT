from fastapi import APIRouter, Form, Depends
from settings import Settings
from web import ConnectionManager
from web.routes.api import accounts, tasks
from web.utils import get_manager_form

router = APIRouter(prefix='/api', tags=['API'])

router.include_router(accounts.router)
router.include_router(tasks.router)


@router.post('/settings')
async def update_settings(username: str = Form(), password: str = Form(), api_id: int = Form(), api_hash: str = Form(),
                          proxy: str = Form(None), hash_password: str = Form(''), use_password: bool = Form(True),
                          use_last_name: bool = Form(True), first_names: str = Form(''), last_names: str = Form(''),
                          flood_wait: int = Form(60), manager: ConnectionManager = Depends(get_manager_form)):
    Settings.set_many(dict(username=username, password=password, api_id=api_id, api_hash=api_hash, proxy=proxy,
                           hash_password=hash_password, use_password=use_password, use_last_name=use_last_name,
                           first_names=list(filter(None, first_names.split('\r\n'))), last_names=list(filter(None, last_names.split('\r\n'))),
                           flood_wait=flood_wait))
    await Settings.save()
    await manager.alert('Success update settings')
    return {'success': True}
