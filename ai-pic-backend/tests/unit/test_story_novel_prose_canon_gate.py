import pytest
from app.services.story.story_novel_prose_canon_gate import prose_canon_violations


@pytest.fixture
def canon():
    return {
        "world_rules": [
            {
                "id": "rule-6",
                "statement": (
                    "旱海六城是内陆干旱文明；澄砂港的“港”指陆路货运沙港，"
                    "不临天然海洋，不存在海岸、海船、渔业或海水景观。"
                ),
                "exceptions": [],
            }
        ],
        "entities": [
            {
                "id": "char-current",
                "kind": "character",
                "name": "闻峤",
                "aliases": ["闻管理员"],
            },
            {
                "id": "char-future",
                "kind": "character",
                "name": "岑野",
                "aliases": [],
            },
            {
                "id": "loc-port",
                "kind": "location",
                "name": "澄砂港",
                "aliases": [],
            },
        ],
    }


@pytest.mark.parametrize(
    "content",
    [
        "车队驶过东海岸。",
        "远处就是海岸。",
        "一艘海船停在港外。",
        "墙上展示着海水景观。",
        "孩子第一次看见海洋。",
        "这里曾是一座海港。",
        "城中保留着渔业传统。",
    ],
)
def test_explicit_world_rule_terms_are_rejected(canon, content):
    violations = prose_canon_violations(canon, {}, content)

    assert violations
    assert {item["code"] for item in violations} == {"canon_violation"}
    assert any(
        term in content for term in ("海岸", "海船", "海水景观", "海洋", "海港", "渔业")
    )


def test_dryland_vocabulary_does_not_merge_forbidden_terms(canon):
    content = "旱海水网沿着陆路延伸，货车驶入澄砂港这座沙港。"

    assert prose_canon_violations(canon, {}, content) == []


def test_negated_restatement_and_rule_exceptions_do_not_false_positive(canon):
    assert prose_canon_violations(canon, {}, "这里不存在海岸，也不是海港。") == []
    canon["world_rules"][0]["exceptions"] = ["历史档案可提及海岸"]
    assert prose_canon_violations(canon, {}, "档案写着东海岸。") == []


def test_forbidden_landscape_term_in_a_simile_is_not_a_world_fact(canon):
    assert (
        prose_canon_violations(
            canon,
            {},
            "旱海在晨光中延展开来，像一片凝固的海洋。",
        )
        == []
    )
    assert prose_canon_violations(canon, {}, "沙丘起伏，呈海洋般的纹理。") == []


def test_current_plan_character_name_and_alias_are_allowed(canon):
    chapter_plan = {
        "character_focus": ["闻峤"],
        "key_events": ["闻管理员检查货运清单"],
    }

    assert (
        prose_canon_violations(
            canon,
            chapter_plan,
            "闻峤走进大厅，闻管理员随后检查货运清单。",
        )
        == []
    )


def test_current_plan_entity_id_allows_character_name(canon):
    chapter_plan = {
        "state_transitions": [
            {"subject_id": "char-current", "field": "status", "to_value": "值守"}
        ]
    }

    assert prose_canon_violations(canon, chapter_plan, "闻峤继续值守。") == []


def test_character_from_visible_prior_chapter_remains_allowed(canon):
    violations = prose_canon_violations(
        canon,
        {"position": 2, "key_events": ["检查货运清单"]},
        "闻峤继续核对昨天留下的记录。",
        visible_chapter_plans=[{"position": 1, "character_focus": ["闻峤"]}],
    )

    assert violations == []


def test_canon_character_missing_from_current_plan_is_rejected(canon):
    violations = prose_canon_violations(canon, {}, "岑野敲响了值班室的门。")

    assert violations == [
        {
            "code": "canon_violation",
            "message": "正文引入未授权具名角色: 岑野",
        }
    ]


def test_non_canon_prose_does_not_guess_character_names(canon):
    for content in (
        "管理员陆辞走进大厅，说要查账。",
        "管理员是谁？“叫陆辞。他已经离开了。”",
        "镜芯是一种她叫不出名字的深灰色材质。",
    ):
        assert prose_canon_violations(canon, {}, content) == []


def test_role_and_location_prose_do_not_create_fake_character(canon):
    content = (
        "管理员打开大门，记者查看。医生问何时来，警员向前走，"
        "向导许可，随后车队驶入澄砂港。"
    )

    assert prose_canon_violations(canon, {}, content) == []
