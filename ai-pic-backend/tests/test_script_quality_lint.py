import pytest
from app.schemas.script_quality import ScriptLintOptions
from app.services.script_quality import lint_script_content


@pytest.mark.unit
def test_lint_passes_minimal_compliant_script():
    script = """
[第1场] [豪宅门外] [雨夜/外]
【音效】：啪！
【快】【情绪目的：羞辱】
丈母娘：离婚！
苏辰：现在就滚？
【慢】【情绪目的：反击】
（特写）苏辰抬头，擦掉血。
苏辰：看清楚？
"""
    result = lint_script_content(script, options=ScriptLintOptions(pass_threshold=9.0))
    assert result.passed is True
    assert result.overall_score >= 9.0


@pytest.mark.unit
def test_lint_flags_unfilmable_language_and_long_dialogue():
    script = """
他感到悲伤。
小明：我真的非常非常非常生气你为什么这样做
你好。
结束了。
"""
    result = lint_script_content(script, options=ScriptLintOptions(pass_threshold=9.0))
    assert result.passed is False
    rule_ids = {r.rule_id for r in result.rules}
    assert "visual_language" in rule_ids
    assert "dialogue_length" in rule_ids
    issue_rule_ids = {i.rule_id for i in result.issues}
    assert "visual_language" in issue_rule_ids
    assert "dialogue_length" in issue_rule_ids
