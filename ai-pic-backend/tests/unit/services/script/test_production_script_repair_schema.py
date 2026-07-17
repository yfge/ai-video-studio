from app.schemas.production_script import ProductionScriptModel


def test_production_repair_schema_includes_complete_beat_contract():
    schema = ProductionScriptModel.model_json_schema()
    contract_ref = schema["properties"]["structured_script_contract"]["$ref"]
    contract_name = contract_ref.rsplit("/", 1)[-1]
    contract = schema["$defs"][contract_name]
    scene_ref = contract["properties"]["scenes"]["items"]["$ref"]
    scene_name = scene_ref.rsplit("/", 1)[-1]
    scene = schema["$defs"][scene_name]
    beat_ref = scene["properties"]["beats"]["items"]["$ref"]
    beat_name = beat_ref.rsplit("/", 1)[-1]
    beat = schema["$defs"][beat_name]

    assert "visible_event" in beat["properties"]
    assert "action_lines" in beat["properties"]
    assert "dialogue_lines" in beat["properties"]
