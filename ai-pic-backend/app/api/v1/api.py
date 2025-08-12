from fastapi import APIRouter
from app.api.v1.endpoints import virtual_ip, virtual_ip_images, stories, episodes, scripts, migrations

api_router = APIRouter()

# 虚拟IP相关路由
api_router.include_router(virtual_ip.router, prefix="/virtual-ips", tags=["virtual-ips"])
api_router.include_router(virtual_ip_images.router, prefix="/virtual-ips", tags=["virtual-ip-images"])

# 剧本相关路由
api_router.include_router(stories.router, prefix="/stories", tags=["stories"])
api_router.include_router(episodes.router, prefix="/episodes", tags=["episodes"])
api_router.include_router(scripts.router, prefix="/scripts", tags=["scripts"])

# 数据库迁移相关路由
api_router.include_router(migrations.router, prefix="/migrations", tags=["migrations"]) 