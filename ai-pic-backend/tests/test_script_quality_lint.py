from types import SimpleNamespace

import pytest

from app.api.v1.endpoints.scripts import quality as quality_endpoint
from app.models.task import TaskStatus
from app.schemas.script_quality import ScriptLintOptions
from app.services.script_quality import lint_script_content, lint_script_content_async
from app.services.script_quality import task_entrypoints


class _CliffhangerManager:
    def __init__(self, passed=True, score=1.0, success=True):
        self.passed = passed
        self.score = score
        self.success = success
        self.calls = []

    async def generate_text(self, **kwargs):
        self.calls.append(kwargs)
        if not self.success:
            return SimpleNamespace(success=False, error="provider down")
        return SimpleNamespace(
            success=True,
            provider="fake",
            model=kwargs.get("model") or "fake-model",
            data={
                "passed": self.passed,
                "score": self.score,
                "reason": "结尾制造了继续看的问题" if self.passed else "结尾收束",
                "evidence": "最后三行",
                "suggestion": "补一个新问题",
            },
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_lint_passes_minimal_compliant_script():
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
    result = await lint_script_content_async(
        script,
        options=ScriptLintOptions(pass_threshold=9.0),
        ai_manager=_CliffhangerManager(),
    )
    assert result.passed is True
    assert result.overall_score >= 9.0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_lint_flags_unfilmable_language_and_long_dialogue():
    script = """
他感到悲伤。
小明：我真的非常非常非常生气你为什么这样做
你好。
结束了。
"""
    result = await lint_script_content_async(
        script,
        options=ScriptLintOptions(pass_threshold=9.0),
        ai_manager=_CliffhangerManager(passed=False, score=0.0),
    )
    assert result.passed is False
    rule_ids = {r.rule_id for r in result.rules}
    assert "visual_language" in rule_ids
    assert "dialogue_length" in rule_ids
    issue_rule_ids = {i.rule_id for i in result.issues}
    assert "visual_language" in issue_rule_ids
    assert "dialogue_length" in issue_rule_ids
    assert "cliffhanger" in issue_rule_ids


@pytest.mark.unit
@pytest.mark.asyncio
async def test_lint_accepts_commercial_vertical_drama_format():
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
    manager = _CliffhangerManager()
    result = await lint_script_content_async(
        script, options=ScriptLintOptions(pass_threshold=9.0), ai_manager=manager
    )

    assert result.passed is True
    assert result.overall_score >= 9.0
    rule_ids = {r.rule_id for r in result.rules}
    assert "pacing_markers" in rule_ids
    assert manager.calls


@pytest.mark.unit
@pytest.mark.asyncio
async def test_lint_accepts_alarm_blackout_cliffhanger():
    script = """
第1集
▲【音效】砰！画面直接切入冲突现场。

1-1 内. 客厅 - 夜
人物： 文闻、老拐
▲文闻把手机转向老拐，终端光照在两人脸上。
文闻(冷静)：别动。
老拐(慌乱)：你做了什么？
▲文闻指尖悬在回车键上。
文闻(威胁)：十秒后销毁。
老拐(失控)：你疯了！
▲文闻指尖落下，按下回车键。
▲【音效】警报声持续，客厅陷入黑暗。
"""

    result = await lint_script_content_async(
        script,
        options=ScriptLintOptions(pass_threshold=9.0),
        ai_manager=_CliffhangerManager(passed=True, score=0.95),
        model="deepseek:deepseek-v4-flash",
        prefer_provider="deepseek",
    )

    assert result.passed is True
    cliffhanger = next(rule for rule in result.rules if rule.rule_id == "cliffhanger")
    assert cliffhanger.passed is True
    assert cliffhanger.details["model"] == "deepseek:deepseek-v4-flash"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_lint_fails_when_cliffhanger_llm_unavailable():
    result = await lint_script_content_async(
        "第1集\n【音效】砰！\nScene 1 客厅 - 夜\n苏辰：谁？\n",
        options=ScriptLintOptions(pass_threshold=9.0),
        ai_manager=None,
    )

    assert result.passed is False
    cliffhanger = next(rule for rule in result.rules if rule.rule_id == "cliffhanger")
    assert cliffhanger.details["error"] == "cliffhanger_llm_unavailable"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_lint_uses_strong_local_cliffhanger_when_llm_unavailable():
    script = """
第1集
1-1 内. 会议室 - 夜
人物： AP、陈默
▲投影数字变红，客户手指重重敲在错误数据上。
AP(冷静)：证据在这。
陈默(慌乱)：我不知道。
▲AP把手机举到镜头前，短信倒计时从30秒跳到29秒。
▲【特写】镜头停在关键线索上，所有声音突然压低。
AP(压低声)：你真以为，这就是全部真相？
"""

    result = await lint_script_content_async(
        script,
        options=ScriptLintOptions(pass_threshold=0.0),
        ai_manager=None,
    )

    cliffhanger = next(rule for rule in result.rules if rule.rule_id == "cliffhanger")
    assert cliffhanger.passed is True
    assert cliffhanger.details["provider"] == "local_strong_cliffhanger_fallback"


@pytest.mark.unit
def test_sync_lint_requires_async_cliffhanger_judgement():
    result = lint_script_content(
        "第1集\n【音效】砰！\nScene 1 客厅 - 夜\n苏辰：谁？\n",
        options=ScriptLintOptions(pass_threshold=9.0),
    )

    cliffhanger = next(rule for rule in result.rules if rule.rule_id == "cliffhanger")
    assert result.passed is False
    assert cliffhanger.details["error"] == "cliffhanger_llm_unavailable"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_quality_endpoint_uses_default_model_when_no_generation_model(
    monkeypatch,
):
    manager = _CliffhangerManager()
    monkeypatch.setattr(
        quality_endpoint,
        "ai_service",
        SimpleNamespace(ai_manager=manager),
    )

    class _Service:
        def get_script(self, script_id, user):
            return SimpleNamespace(content="第1集\n【音效】砰！\nScene 1\n苏辰：谁？")

    result = await quality_endpoint.quality_check_script(
        script_id=1,
        options=ScriptLintOptions(pass_threshold=0.0),
        current_user=SimpleNamespace(id=1),
        service=_Service(),
    )

    assert manager.calls
    assert manager.calls[0].get("model") is None
    assert result.rules


@pytest.mark.unit
def test_script_quality_task_uses_default_model_without_generation_metadata(
    monkeypatch,
):
    manager = _CliffhangerManager()
    task = SimpleNamespace(
        parameters=None,
        status=TaskStatus.PENDING,
        description=None,
        error_message=None,
        result_file_path=None,
    )
    script = SimpleNamespace(
        content="第1集\n【音效】砰！\nScene 1 客厅 - 夜\n苏辰：谁？",
        is_deleted=False,
        extra_metadata={},
    )

    class _Session:
        def __init__(self):
            self.commits = 0

        def commit(self):
            self.commits += 1

        def close(self):
            pass

    class _TaskRepository:
        def __init__(self, session):
            self.session = session

        def get_by_id(self, task_id):
            return task

    class _ScriptRepository:
        def __init__(self, session):
            self.session = session

        def get_by_id(self, script_id):
            return script

    session = _Session()
    monkeypatch.setattr(task_entrypoints, "SessionLocal", lambda: session)
    monkeypatch.setattr(task_entrypoints, "TaskRepository", _TaskRepository)
    monkeypatch.setattr(task_entrypoints, "ScriptRepository", _ScriptRepository)
    monkeypatch.setattr(
        task_entrypoints,
        "ai_service",
        SimpleNamespace(ai_manager=manager),
    )

    task_entrypoints.process_script_quality_task(
        task_id=1, payload={"script_id": 2}, user_id=3
    )

    assert task.status == TaskStatus.COMPLETED
    assert task.result_file_path == "script:2:quality"
    assert manager.calls
    assert manager.calls[0].get("model") is None
    assert script.extra_metadata["script_quality"]["result"]["rules"]
