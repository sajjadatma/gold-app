from fastapi import APIRouter

from app.api.routes import items, login, private, users, utils
from app.core.config import settings
from app.modules.brand_import.api import router as brand_assets_router
from app.modules.brand_models.api import router as brand_models_router
from app.modules.brands.api import router as brands_router
from app.modules.generations.api import router as generations_router
from app.modules.products.api import router as products_router

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(brands_router)
api_router.include_router(brand_assets_router)
api_router.include_router(brand_models_router)
api_router.include_router(generations_router)
api_router.include_router(products_router)


if settings.FASTAPI_ENV == "development":
    api_router.include_router(private.router)
