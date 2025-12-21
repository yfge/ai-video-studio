from fastapi import APIRouter
from app.api.v1.endpoints import auth, virtual_ip, virtual_ip_images, virtual_ip_voice_samples, stories, episodes, scripts, migrations, prompts, diagnostic, admin, tasks, styles
from app.api.v1.endpoints import story_structure
from app.api.v1 import ai_providers, voice

api_router = APIRouter()

# 认证相关路由
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# 管理员相关路由
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

# 虚拟IP相关路由
api_router.include_router(virtual_ip.router, prefix="/virtual-ips", tags=["virtual-ips"])
api_router.include_router(virtual_ip_images.router, prefix="/virtual-ips", tags=["virtual-ip-images"])
api_router.include_router(virtual_ip_voice_samples.router, prefix="/virtual-ips", tags=["virtual-ips"])

# 剧本相关路由
api_router.include_router(stories.router, prefix="/stories", tags=["stories"])
api_router.include_router(episodes.router, prefix="/episodes", tags=["episodes"])
api_router.include_router(scripts.router, prefix="/scripts", tags=["scripts"])
api_router.include_router(story_structure.router, prefix="/story-structure", tags=["story-structure"]) 

# 数据库迁移相关路由
api_router.include_router(migrations.router, prefix="/migrations", tags=["migrations"])

# 提示词管理相关路由
api_router.include_router(prompts.router, prefix="/prompts", tags=["prompts"])

# AI服务提供商相关路由
api_router.include_router(ai_providers.router, prefix="/ai", tags=["ai-providers"])
# 声音/音乐相关路由
api_router.include_router(voice.router, prefix="/voice", tags=["voice"])

# 风格 schema / preset（后端为唯一真源）
api_router.include_router(styles.router, prefix="/styles", tags=["styles"])

# 诊断相关路由
api_router.include_router(diagnostic.router, prefix="/diagnostic", tags=["diagnostic"])

# 任务相关路由
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"]) 
