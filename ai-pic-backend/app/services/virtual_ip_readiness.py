"""Non-blocking production readiness checks for a VirtualIP.

Static checks only: no provider API calls, no hard blocks. Warnings surface in
the IP detail page so operators fix gaps before render time instead of hitting
runtime failures (missing avatar anchor, unusable voice binding).
"""

from __future__ import annotations

from typing import Any

from app.models.virtual_ip import VirtualIP


def _has_default_avatar(ip: VirtualIP) -> bool:
    if isinstance(ip.default_avatar_url, str) and ip.default_avatar_url.strip():
        return True
    for image in list(ip.images or []):
        if getattr(image, "is_default", False) and not getattr(
            image, "is_deleted", False
        ):
            return True
    return False


def _voice_config_valid(ip: VirtualIP) -> bool:
    config: Any = ip.voice_config
    if not isinstance(config, dict):
        return False
    provider = config.get("provider")
    voice_id = config.get("voice_id")
    return bool(
        isinstance(provider, str)
        and provider.strip()
        and isinstance(voice_id, str)
        and voice_id.strip()
    )


def compute_virtual_ip_readiness(ip: VirtualIP) -> dict[str, Any]:
    has_default_avatar = _has_default_avatar(ip)
    voice_config_valid = _voice_config_valid(ip)
    warnings: list[str] = []
    if not has_default_avatar:
        warnings.append(
            "未设置默认头像：角色匹配会取不到形象锚点，请在图片管理中"
            "上传/生成图片并标记默认头像。"
        )
    if not voice_config_valid:
        warnings.append(
            "语音绑定不完整：缺少 provider 或 voice_id，配音生成会失败，"
            "请在声音设置中完成绑定。"
        )
    return {
        "has_default_avatar": has_default_avatar,
        "voice_config_valid": voice_config_valid,
        "warnings": warnings,
    }
