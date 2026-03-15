import logging
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.core.config import settings
from src.core.logger import logger
from src.endpoints.router import api_router

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

logging.basicConfig(
    level=settings.LOG_LEVEL.upper(),
    format="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
)


@app.middleware("http")
async def log_request(
    request: Request, call_next: Callable[[Request], Awaitable[JSONResponse]]
) -> JSONResponse:
    logger.info(f"{request.method} {request.url.path}")
    try:
        response = await call_next(request)
        logger.info(f"{response.status_code} {request.url.path}")
        return response
    except Exception as e:
        logger.error(f"{request.method} {request.url.path} Error - {str(e)}")
        raise


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = []
    for error in exc.errors():
        safe_error = {
            "loc": error.get("loc"),
            "msg": str(error.get("msg")),
            "type": error.get("type"),
        }
        if "ctx" in error:
            safe_error["ctx"] = {
                k: str(v)
                if not isinstance(v, (str, int, float, bool, type(None)))
                else v
                for k, v in error["ctx"].items()
            }
        errors.append(safe_error)

    logger.warning(f"Validation error: {errors}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation failed", "errors": errors},
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    logger.warning(f"Not found: {request.url.path}")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "Not found"},
    )


app.include_router(api_router)


@app.get("/health")
def health() -> dict[str, str]:
    logger.debug("Health check requested")
    return {"status": "ok", "app": settings.APP_NAME}
