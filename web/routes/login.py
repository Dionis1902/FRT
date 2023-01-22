from datetime import timedelta
from fastapi import APIRouter, Request, HTTPException, Form
from fastapi_login import LoginManager
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates

from settings import Settings

login_manager = LoginManager(secret="your-secret", token_url='/auth/login', use_cookie=True)

router = APIRouter(include_in_schema=False)

templates = Jinja2Templates(directory='web/templates')

fake_db = {'test': {'password': 'test'}}


@login_manager.user_loader()
def load_user(username):
    if username == Settings.get('username'):
        return dict(password=Settings.get('password'))
    raise HTTPException(401)


@router.post('/login')
def login(request: Request, username: str = Form(), password: str = Form()):
    if not request.headers.get('referer').endswith('/login'):
        raise HTTPException(403)
    if username != Settings.get('username'):
        return templates.TemplateResponse('errors/401.html', {'request': request, 'error_data': {'message': 'User don\'t exist', 'type': 'danger'}})
    elif password != Settings.get('password'):
        return templates.TemplateResponse('errors/401.html', {'request': request, 'error_data': {'message': 'Invalid password', 'type': 'danger'}})
    access_token = login_manager.create_access_token(
        data={'sub': username}, expires=timedelta(days=7)
    )
    resp = RedirectResponse(url="/", status_code=302)
    login_manager.set_cookie(resp, access_token)
    return resp


@router.get('/login')
async def login(request: Request):
    return templates.TemplateResponse('errors/401.html', {'request': request})

