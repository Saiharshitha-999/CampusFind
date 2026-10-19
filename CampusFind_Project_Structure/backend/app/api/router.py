from fastapi import APIRouter
from app.features.auth.router import router as auth_router
from app.features.reports.router import router as reports_router
from app.features.search.router import router as search_router
from app.features.claims.router import router as claims_router
from app.features.admin.router import router as admin_router
from app.features.notifications.router import router as notifications_router
from app.features.status.router import router as status_router

api_router=APIRouter()
api_router.include_router(auth_router,prefix='/auth',tags=['auth'])
api_router.include_router(reports_router,prefix='/reports',tags=['reports'])
api_router.include_router(search_router,tags=['search'])
api_router.include_router(claims_router,tags=['claims'])
api_router.include_router(admin_router,prefix='/admin',tags=['admin'])
api_router.include_router(notifications_router,prefix='/notifications',tags=['notifications'])
api_router.include_router(status_router,tags=['status'])
