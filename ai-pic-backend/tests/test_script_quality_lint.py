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


@pytest.mark.unit
def test_lint_accepts_commercial_vertical_drama_format():
    script = """
第1集
1-1 内. 皇宫偏殿 - 夜
人物： 林雪、陈默
▲【音效】砰！殿门被撞开，烛火猛地一晃。
林雪(冷笑)：你藏的账本，我找到了。
陈默(后退)：你不该碰它！
▲林雪把账本摔到案上，红色指印露出。
林雪(逼近)：那就告诉我，谁签的字？
陈默(压低声)：你真想知道？
▲【特写】最后一页翻开，另一个名字压在林雪指尖。
"""
    result = lint_script_content(script, options=ScriptLintOptions(pass_threshold=9.0))

    assert result.passed is True
    assert result.overall_score >= 9.0
    rule_ids = {r.rule_id for r in result.rules}
    assert "pacing_markers" in rule_ids
