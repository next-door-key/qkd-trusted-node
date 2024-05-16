from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.dependencies import get_settings
from app.internal.lifecycle import Lifecycle
from app.routers import keys, internal


@asynccontextmanager
async def lifespan(api: FastAPI):
    settings = get_settings()
    lifecycle = Lifecycle(api, settings)

    api.lifecycle = lifecycle

    await lifecycle.before_start()
    yield
    await lifecycle.after_landing()


app = FastAPI(lifespan=lifespan)
app.add_middleware(HTTPSRedirectMiddleware)

app.include_router(router=internal.router, prefix='/api/v1')
app.include_router(router=keys.router, prefix='/api/v1')


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={'message': str(exc.detail)}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({'message': 'Validation error', 'details': exc.errors()}),
    )


@app.get('/')
async def index():
    return {'message': 'Hello, World!'}
