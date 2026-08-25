from fastapi import APIRouter
from starlette.requests import Request

from core.template import UserTemplates
from ..plugin_config import module_name, TEMPLATE_PATH

router = APIRouter()
templates = UserTemplates()


@router.get("/")
async def index(request: Request):
    """CTX 상품수집 사용자 페이지 (준비 중)"""
    context = {
        "request": request,
        "title": "CTX 상품수집",
        "module_name": module_name,
    }
    return templates.TemplateResponse(
        f"{TEMPLATE_PATH}/index.html", context
    )
