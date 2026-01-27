from __future__ import annotations

from typing import Any, Dict

from app.services.task_agent_run.utils import (
    loads_task_parameters,
    maybe_int,
    parse_result_id,
    split_provider_model,
)


def build_environment_images_agent_run(db, task, *, user_id: int, variant: bool) -> Dict[str, Any]:
    from app.models.story_structure import Environment

    params = loads_task_parameters(getattr(task, "parameters", None))
    env_id = maybe_int(params.get("env_id"))
    if env_id is None:
        suffix = "environment_image_variants" if variant else "environment_images"
        rest = parse_result_id(getattr(task, "result_file_path", None), prefix=suffix)
        if rest:
            env_id = maybe_int(rest.split(":", 1)[0])
    if env_id is None:
        return {}

    env = db.query(Environment).filter(Environment.id == env_id, Environment.user_id == user_id).first()
    if not env:
        return {}

    provider_used, model_used = split_provider_model(params.get("model"))
    prompt_value = params.get("extra_prompt") or params.get("prompt")

    payload: Dict[str, Any] = {
        "generation_method": "image_to_image" if variant else "text_to_image",
        "provider_used": provider_used,
        "model_used": model_used,
        "prompt": prompt_value if isinstance(prompt_value, str) else getattr(task, "prompt", None),
        "result_ref": {
            "environment_id": env.id,
            "environment_business_id": getattr(env, "business_id", None),
        },
    }
    count = maybe_int(params.get("count"))
    if count is not None:
        payload["result_ref"]["count"] = count
    return payload


def build_virtual_ip_image_agent_run(db, task, *, user_id: int) -> Dict[str, Any]:
    from app.models.virtual_ip import VirtualIP, VirtualIPImage

    result = parse_result_id(getattr(task, "result_file_path", None), prefix="virtual_ip_image")
    if not result:
        return {}
    tokens = result.split(":")
    if len(tokens) < 2:
        return {}
    vip_id = maybe_int(tokens[0])
    image_id = maybe_int(tokens[1])
    if vip_id is None or image_id is None:
        return {}

    image = (
        db.query(VirtualIPImage)
        .join(VirtualIP, VirtualIPImage.virtual_ip_id == VirtualIP.id)
        .filter(VirtualIPImage.id == image_id, VirtualIP.user_id == user_id)
        .first()
    )
    if not image:
        return {}

    params = loads_task_parameters(getattr(task, "parameters", None))
    provider_used, _ = split_provider_model(params.get("model"))

    generation_method = None
    if isinstance(getattr(image, "metadata", None), dict):
        generation_method = image.metadata.get("generation_method")

    return {
        "generation_method": generation_method or "virtual_ip_image",
        "provider_used": provider_used,
        "model_used": getattr(image, "ai_model", None),
        "prompt": getattr(image, "prompt", None) or getattr(task, "prompt", None),
        "usage": getattr(image, "generation_params", None),
        "result_ref": {
            "virtual_ip_id": getattr(image, "virtual_ip_id", None),
            "virtual_ip_business_id": getattr(image, "virtual_ip_business_id", None),
            "virtual_ip_image_id": getattr(image, "id", None),
        },
    }


def build_virtual_ip_variant_agent_run(db, task, *, user_id: int) -> Dict[str, Any]:
    from app.models.virtual_ip import VirtualIP, VirtualIPImage

    params = loads_task_parameters(getattr(task, "parameters", None))
    base_image_id = maybe_int(params.get("image_id"))
    if base_image_id is None:
        result = parse_result_id(getattr(task, "result_file_path", None), prefix="virtual_ip_image_variants")
        if result:
            base_image_id = maybe_int(result.split(":", 1)[0])
    if base_image_id is None:
        return {}

    base_image = (
        db.query(VirtualIPImage)
        .join(VirtualIP, VirtualIPImage.virtual_ip_id == VirtualIP.id)
        .filter(VirtualIPImage.id == base_image_id, VirtualIP.user_id == user_id)
        .first()
    )
    if not base_image:
        return {}

    provider_used, model_used = split_provider_model(params.get("model"))
    count = maybe_int(params.get("count"))

    return {
        "generation_method": "virtual_ip_image_variant",
        "provider_used": provider_used,
        "model_used": model_used,
        "prompt": getattr(task, "prompt", None),
        "result_ref": {
            "virtual_ip_id": getattr(base_image, "virtual_ip_id", None),
            "virtual_ip_business_id": getattr(base_image, "virtual_ip_business_id", None),
            "base_image_id": getattr(base_image, "id", None),
            "count": count,
        },
    }

