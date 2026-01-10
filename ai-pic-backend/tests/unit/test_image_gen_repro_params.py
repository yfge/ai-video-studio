from app.services.image_gen import (
    ImageGenDomain,
    ImageGenMode,
    ImageGenRequest,
    build_ai_manager_call,
    normalize_image_gen_request,
)


def test_image_gen_normalize_clamps_and_passes_jimeng_params():
    normalized = normalize_image_gen_request(
        ImageGenRequest(
            domain=ImageGenDomain.VIRTUAL_IP,
            mode=ImageGenMode.TEXT_TO_IMAGE,
            prompt="test",
            model="jimeng-sdxl",
            size="1024x1024",
            steps=999,
            cfg_scale=99,
            seed=2**40,
            negative_prompt="low quality, watermark",
        )
    )
    call = build_ai_manager_call(normalized)

    assert call["prefer_provider"] == "jimeng"
    assert call["steps"] == 60
    assert call["cfg_scale"] == 30.0
    assert call["seed"] == 2**31 - 1
    assert call["negative_prompt"] == "low quality, watermark"


def test_image_gen_provider_filter_drops_steps_for_keling():
    normalized = normalize_image_gen_request(
        ImageGenRequest(
            domain=ImageGenDomain.ENVIRONMENT,
            mode=ImageGenMode.TEXT_TO_IMAGE,
            prompt="test",
            model="kling-image",
            size="1024x1024",
            steps=30,
            cfg_scale=7.0,
            seed=123,
            negative_prompt="blurry",
        )
    )
    call = build_ai_manager_call(normalized)

    assert call["prefer_provider"] == "keling"
    assert call["negative_prompt"] == "blurry"
    assert "steps" not in call
    assert "cfg_scale" not in call
    assert "seed" not in call


def test_image_gen_img2img_strength_clamped_for_jimeng():
    normalized = normalize_image_gen_request(
        ImageGenRequest(
            domain=ImageGenDomain.STORYBOARD,
            mode=ImageGenMode.IMAGE_TO_IMAGE,
            prompt="test",
            model="jimeng-img2img",
            base_image="https://example.com/base.png",
            strength=1.5,
            steps=0,
            cfg_scale=-1,
            seed=-1,
        )
    )
    call = build_ai_manager_call(normalized)

    assert call["prefer_provider"] == "jimeng"
    assert call["strength"] == 1.0
    assert call["steps"] == 25
    assert call["cfg_scale"] == 7.0
    assert "seed" not in call
