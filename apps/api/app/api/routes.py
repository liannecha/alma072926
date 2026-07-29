from fastapi import APIRouter

from app.api.leads import router as leads_router

router = APIRouter()
router.include_router(leads_router)


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
