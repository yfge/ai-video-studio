from app.schemas.generation import ScriptModel
from app.schemas.script_beat_contract import StructuredScriptContract


class ProductionScriptModel(ScriptModel):
    structured_script_contract: StructuredScriptContract
