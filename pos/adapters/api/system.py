from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter()


@router.get("/", include_in_schema=False)
def index() -> RedirectResponse:
    return RedirectResponse("/docs")


@router.get("/health", tags=["Сервис"], summary="Проверка запуска")
def health() -> dict[str, str]:
    return {"status": "ok"}
