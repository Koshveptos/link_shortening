from fastapi import APIRouter

from src.endpoints import auth, links

api_router = APIRouter(prefix="/api")


api_router.include_router(links.router)
api_router.include_router(auth.router)
