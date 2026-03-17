from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.config import settings

app = FastAPI(title='Video Subtitle API', version='0.1.0')
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.include_router(router)


@app.on_event('startup')
async def ensure_workdir_root() -> None:
    Path(settings.workdir_root).mkdir(parents=True, exist_ok=True)


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and 'error' in exc.detail and 'code' in exc.detail:
        payload = exc.detail
    else:
        payload = {'error': str(exc.detail), 'code': 'HTTP_ERROR'}
    return JSONResponse(status_code=exc.status_code, content=payload)


@app.get('/healthz')
def healthz():
    return {'ok': True}
