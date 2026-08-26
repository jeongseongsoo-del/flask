import time

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from starlette.requests import Request

from core.template import UserTemplates
from ..plugin_config import module_name, TEMPLATE_PATH

router = APIRouter()
templates = UserTemplates()

CTX_API_URL = "https://ctx.cretec.kr/CtxApp/ctx/selectPowerSearchJson.do"


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


@router.get("/api/prod-search")
async def prod_search(
    prod_cd: str = Query(..., description="상품코드"),
    keyword: str = Query("", description="키워드"),
):
    """CTX API 프록시 — 브라우저 CORS 우회용 서버사이드 호출"""
    params = {
        "prod_cd": prod_cd,
        "keyword": keyword,
        "_": int(time.time() * 1000),
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(CTX_API_URL, params=params)
            resp.raise_for_status()
            return JSONResponse(content=resp.json())
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="CTX API 응답 시간 초과")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"CTX API 오류: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"CTX API 호출 실패: {str(e)}")
