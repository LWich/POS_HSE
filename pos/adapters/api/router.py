from fastapi import APIRouter

from pos.adapters.api import system
from pos.adapters.api.v1 import criteria, evaluations, reports, students

router = APIRouter()
router.include_router(students.router)
router.include_router(criteria.router)
router.include_router(evaluations.router)
router.include_router(reports.router)
router.include_router(system.router)
