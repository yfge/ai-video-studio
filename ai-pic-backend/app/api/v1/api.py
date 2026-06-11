from app.api.v1 import ai_providers, ai_text_generation, voice
from app.api.v1.endpoints import (
    admin,
    auth,
    diagnostic,
    episodes,
    image_gen_profiles,
    migrations,
    prompts,
    scoring,
    scripts,
    stories,
    story_structure,
    styles,
    task_control,
    tasks,
    timeline_clip_tasks,
    timeline_keyframes,
    timelines,
    virtual_ip,
    virtual_ip_images,
    virtual_ip_voice_samples,
    workbench,
)
from fastapi import APIRouter

api_router = APIRouter()

# 认证相关路由
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# 管理员相关路由
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

# 虚拟IP相关路由
api_router.include_router(virtual_ip.router, tags=["virtual-ips"])
api_router.include_router(
    virtual_ip_images.router, prefix="/virtual-ips", tags=["virtual-ip-images"]
)
api_router.include_router(
    virtual_ip_voice_samples.router, prefix="/virtual-ips", tags=["virtual-ips"]
)

# 剧本相关路由
api_router.include_router(stories.router, prefix="/stories", tags=["stories"])
api_router.include_router(episodes.router, prefix="/episodes", tags=["episodes"])
api_router.include_router(scripts.router, prefix="/scripts", tags=["scripts"])
api_router.include_router(
    story_structure.router, prefix="/story-structure", tags=["story-structure"]
)
api_router.include_router(timelines.router, tags=["timelines"])
api_router.include_router(timeline_keyframes.router, tags=["timelines"])
api_router.include_router(timeline_clip_tasks.router, tags=["timelines"])
api_router.include_router(task_control.router, tags=["tasks"])

# 数据库迁移相关路由
api_router.include_router(migrations.router, prefix="/migrations", tags=["migrations"])

# 提示词管理相关路由
api_router.include_router(prompts.router, prefix="/prompts", tags=["prompts"])

# 图像生成 profiles（后端为唯一真源）
api_router.include_router(
    image_gen_profiles.router, prefix="/image-gen", tags=["image-gen"]
)

# AI服务提供商相关路由
api_router.include_router(
    ai_text_generation.router, prefix="/ai", tags=["ai-providers"]
)
api_router.include_router(ai_providers.router, prefix="/ai", tags=["ai-providers"])
# 声音/音乐相关路由
api_router.include_router(voice.router, prefix="/voice", tags=["voice"])

# 风格 schema / preset（后端为唯一真源）
api_router.include_router(styles.router, prefix="/styles", tags=["styles"])

# 诊断相关路由
api_router.include_router(diagnostic.router, prefix="/diagnostic", tags=["diagnostic"])

# 任务相关路由
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])

# 工作台聚合路由
api_router.include_router(workbench.router, prefix="/workbench", tags=["workbench"])

# 剧本评分与投流表相关路由
api_router.include_router(scoring.router, prefix="/scoring", tags=["scoring"])
