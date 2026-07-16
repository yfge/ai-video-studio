from app.services.production_canvas.asset_provisioning import parse_canvas_asset_prompt


def test_canvas_asset_prompt_extracts_named_ip_and_environment():
    intent = parse_canvas_asset_prompt(
        "创建一个名为阿青的角色，以雨夜码头为场景制作短剧"
    )

    assert intent.virtual_ip_name == "阿青"
    assert intent.environment_name == "雨夜码头"


def test_canvas_asset_prompt_keeps_role_word_inside_named_asset():
    intent = parse_canvas_asset_prompt(
        "创建一个名为画布验收角色0716A的角色，以办公室为场景"
    )

    assert intent.virtual_ip_name == "画布验收角色0716A"


def test_canvas_asset_prompt_extracts_existing_style_reference():
    intent = parse_canvas_asset_prompt("基于林妹妹做第 4 集，办公室轻喜剧")

    assert intent.virtual_ip_name == "林妹妹"
    assert intent.environment_name == "办公室"


def test_canvas_asset_prompt_does_not_invent_ambiguous_assets():
    intent = parse_canvas_asset_prompt("做一个都市轻喜剧短剧链路")

    assert intent.virtual_ip_name is None
    assert intent.environment_name is None
