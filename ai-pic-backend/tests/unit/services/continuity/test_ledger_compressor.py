"""Tests for priority-based continuity ledger compression."""

import pytest

from app.services.continuity.ledger_compressor import (
    CompressionConfig,
    compress_ledger_by_priority,
    score_fact,
    score_info_event,
    score_thread,
    score_timeline_item,
)


class TestScoreFact:
    """Tests for fact scoring function."""

    def test_empty_fact_returns_zero(self):
        assert score_fact("", set()) == 0.0
        assert score_fact(None, set()) == 0.0

    def test_base_score_for_simple_fact(self):
        score = score_fact("张三去了商店", set())
        assert score >= 1.0  # Base score

    def test_high_importance_keywords_boost_score(self):
        base = score_fact("张三去了商店", set())
        important = score_fact("张三的真相身份被揭示", set())
        assert important > base

    def test_character_involvement_boosts_score(self):
        chars = {"张三", "李四"}
        no_chars = score_fact("有人去了商店", chars)
        one_char = score_fact("张三去了商店", chars)
        two_chars = score_fact("张三和李四去了商店", chars)

        assert one_char > no_chars
        assert two_chars > one_char

    def test_longer_facts_get_slight_bonus(self):
        short = score_fact("张三去了商店", set())  # 6 chars
        # Need > 50 chars for first bonus, > 100 for second bonus
        medium_text = "张三在深夜独自去了城东的商店买东西回家" * 3  # ~54 chars (>50)
        medium = score_fact(medium_text, set())
        very_long_text = "张三在深夜独自去了城东的商店买了一些食物和生活用品然后回家" * 4  # ~116 chars (>100)
        long = score_fact(very_long_text, set())
        assert medium > short
        assert long > medium

    def test_english_keywords_detected(self):
        base = score_fact("person went to store", set())
        important = score_fact("the critical truth about identity was revealed", set())
        assert important > base


class TestScoreTimelineItem:
    """Tests for timeline item scoring function."""

    def test_empty_item_returns_zero(self):
        assert score_timeline_item({}, 10, set()) == 0.0
        assert score_timeline_item(None, 10, set()) == 0.0

    def test_recent_episodes_score_higher(self):
        older = {"episode_number": 1}
        newer = {"episode_number": 10}
        score_old = score_timeline_item(older, 10, set())
        score_new = score_timeline_item(newer, 10, set())
        assert score_new > score_old

    def test_reveals_boost_score(self):
        no_reveals = {"episode_number": 5, "reveals": []}
        with_reveals = {"episode_number": 5, "reveals": ["揭示A", "揭示B"]}
        assert score_timeline_item(with_reveals, 10, set()) > score_timeline_item(
            no_reveals, 10, set()
        )

    def test_end_state_boosts_score(self):
        no_state = {"episode_number": 5}
        with_state = {"episode_number": 5, "end_state": "张三离开了城市"}
        assert score_timeline_item(with_state, 10, set()) > score_timeline_item(
            no_state, 10, set()
        )

    def test_anchors_boost_score(self):
        no_anchors = {"episode_number": 5}
        with_anchors = {
            "episode_number": 5,
            "time_anchor": "第二天",
            "location_anchor": "城市中心",
        }
        assert score_timeline_item(with_anchors, 10, set()) > score_timeline_item(
            no_anchors, 10, set()
        )


class TestScoreThread:
    """Tests for thread scoring function."""

    def test_empty_thread_returns_zero(self):
        assert score_thread("", set()) == 0.0
        assert score_thread(None, set()) == 0.0

    def test_question_marks_boost_score(self):
        statement = "张三离开了城市"
        question = "张三为什么离开了城市？"
        assert score_thread(question, set()) > score_thread(statement, set())

    def test_importance_keywords_boost_score(self):
        simple = "张三在等待"
        suspense = "关键悬念：张三的秘密身份"
        assert score_thread(suspense, set()) > score_thread(simple, set())

    def test_character_mention_boosts_score(self):
        chars = {"张三", "李四"}
        no_char = "有人在等待"
        with_char = "张三在等待"
        assert score_thread(with_char, chars) > score_thread(no_char, chars)


class TestScoreInfoEvent:
    """Tests for info acquisition event scoring function."""

    def test_empty_event_returns_zero(self):
        assert score_info_event({}, 10, set()) == 0.0
        assert score_info_event(None, 10, set()) == 0.0

    def test_recent_episodes_score_higher(self):
        older = {"episode_number": 1, "who": "观众", "what": "信息", "how": "揭示"}
        newer = {"episode_number": 10, "who": "观众", "what": "信息", "how": "揭示"}
        assert score_info_event(newer, 10, set()) > score_info_event(older, 10, set())

    def test_known_character_boosts_score(self):
        chars = {"张三"}
        unknown_who = {"episode_number": 5, "who": "路人", "what": "信息", "how": "揭示"}
        known_who = {"episode_number": 5, "who": "张三", "what": "信息", "how": "揭示"}
        assert score_info_event(known_who, 10, chars) > score_info_event(
            unknown_who, 10, chars
        )

    def test_audience_knowledge_boosts_score(self):
        other = {"episode_number": 5, "who": "路人", "what": "信息", "how": "对话"}
        audience = {"episode_number": 5, "who": "观众", "what": "信息", "how": "对话"}
        assert score_info_event(audience, 10, set()) > score_info_event(other, 10, set())

    def test_important_how_method_boosts_score(self):
        simple = {"episode_number": 5, "who": "观众", "what": "信息", "how": "对话"}
        reveal = {"episode_number": 5, "who": "观众", "what": "信息", "how": "揭示真相"}
        assert score_info_event(reveal, 10, set()) > score_info_event(simple, 10, set())


class TestCompressionConfig:
    """Tests for compression configuration."""

    def test_default_config_values(self):
        config = CompressionConfig()
        assert config.max_facts == 25
        assert config.max_timeline == 30
        assert config.max_open_threads == 25
        assert config.max_resolved_threads == 25
        assert config.max_info_events == 60

    def test_custom_config_values(self):
        config = CompressionConfig(max_facts=10, max_timeline=5)
        assert config.max_facts == 10
        assert config.max_timeline == 5


class TestCompressLedgerByPriority:
    """Tests for the main compression function."""

    def test_empty_ledger(self):
        result = compress_ledger_by_priority({})
        assert result["version"] == 1
        assert result["facts"] == []
        assert result["timeline"] == []
        assert result["characters"] == {}
        assert result["info_acquisition_events"] == []
        assert result["open_threads"] == []
        assert result["resolved_threads"] == []

    def test_preserves_characters_unchanged(self):
        ledger = {
            "characters": {
                "张三": {"status": "active", "goal": "找到真相"},
                "李四": {"status": "hidden", "goal": "保守秘密"},
            }
        }
        result = compress_ledger_by_priority(ledger)
        assert result["characters"] == ledger["characters"]

    def test_respects_max_limits(self):
        # Create ledger with many items
        ledger = {
            "facts": [f"事实{i}" for i in range(50)],
            "open_threads": [f"线索{i}" for i in range(50)],
        }
        config = CompressionConfig(max_facts=5, max_open_threads=3)
        result = compress_ledger_by_priority(ledger, config)

        assert len(result["facts"]) == 5
        assert len(result["open_threads"]) == 3

    def test_prioritizes_important_facts(self):
        ledger = {
            "facts": [
                "普通事实1",
                "关键身份真相被揭示",
                "普通事实2",
                "重要秘密发现",
                "普通事实3",
            ],
        }
        config = CompressionConfig(max_facts=2)
        result = compress_ledger_by_priority(ledger, config)

        # Important facts should be kept
        assert "关键身份真相被揭示" in result["facts"]
        assert "重要秘密发现" in result["facts"]
        assert "普通事实1" not in result["facts"]

    def test_prioritizes_recent_timeline_items(self):
        ledger = {
            "timeline": [
                {"episode_number": 1, "events": ["事件1"]},
                {"episode_number": 5, "reveals": ["重大揭示"], "end_state": "关键结局"},
                {"episode_number": 3, "events": ["事件3"]},
            ],
        }
        config = CompressionConfig(max_timeline=2)
        result = compress_ledger_by_priority(ledger, config)

        # Episode 5 has most content, should be kept
        ep_numbers = [item["episode_number"] for item in result["timeline"]]
        assert 5 in ep_numbers

    def test_timeline_sorted_chronologically_after_compression(self):
        ledger = {
            "timeline": [
                {"episode_number": 3, "reveals": ["揭示"]},
                {"episode_number": 1, "reveals": ["揭示"]},
                {"episode_number": 5, "reveals": ["揭示"]},
                {"episode_number": 2, "reveals": ["揭示"]},
            ],
        }
        result = compress_ledger_by_priority(ledger)

        # Should be sorted chronologically
        ep_numbers = [item["episode_number"] for item in result["timeline"]]
        assert ep_numbers == sorted(ep_numbers)

    def test_prioritizes_threads_with_characters(self):
        ledger = {
            "characters": {"张三": {}, "李四": {}},
            "open_threads": [
                "某人在等待",
                "张三的秘密身份悬念",
                "天气变化",
                "李四的关键任务？",
            ],
        }
        config = CompressionConfig(max_open_threads=2)
        result = compress_ledger_by_priority(ledger, config)

        # Threads mentioning characters should be prioritized
        assert any("张三" in t or "李四" in t for t in result["open_threads"])

    def test_preserves_version_number(self):
        ledger = {"version": 3}
        result = compress_ledger_by_priority(ledger)
        assert result["version"] == 3

    def test_handles_non_dict_items_gracefully(self):
        ledger = {
            "facts": ["正常事实", None, "", "另一个事实"],
            "timeline": [{"episode_number": 1}, None, "invalid"],
        }
        result = compress_ledger_by_priority(ledger)

        # Should filter out invalid items
        assert None not in result["facts"]
        assert "" not in result["facts"]
        assert all(isinstance(item, dict) for item in result["timeline"])

    def test_integration_with_realistic_ledger(self):
        """Test with a realistic ledger structure."""
        ledger = {
            "version": 2,
            "facts": [
                "张三是公司高管",
                "关键真相：李四是卧底",
                "办公室在市中心",
                "秘密身份尚未揭示",
            ],
            "timeline": [
                {
                    "episode_number": 1,
                    "time_anchor": "周一",
                    "location_anchor": "公司",
                    "events": ["张三到达"],
                    "end_state": "故事开始",
                    "reveals": [],
                },
                {
                    "episode_number": 2,
                    "time_anchor": "周二",
                    "location_anchor": "会议室",
                    "events": ["重要会议"],
                    "end_state": "发现线索",
                    "reveals": ["关键信息揭示"],
                },
            ],
            "characters": {
                "张三": {
                    "status": "调查中",
                    "goal": "找出真相",
                    "relationships": {"李四": "同事"},
                    "known_info": ["公司有问题"],
                    "unknown_info": ["李四是卧底"],
                },
                "李四": {
                    "status": "隐藏身份",
                    "goal": "完成任务",
                    "relationships": {"张三": "目标"},
                    "known_info": ["张三在调查"],
                    "unknown_info": [],
                },
            },
            "info_acquisition_events": [
                {
                    "episode_number": 1,
                    "who": "观众",
                    "what": "张三的背景",
                    "how": "旁白",
                },
                {
                    "episode_number": 2,
                    "who": "张三",
                    "what": "发现证据",
                    "how": "目击",
                },
            ],
            "open_threads": [
                "李四的真实身份是什么？",
                "公司的秘密？",
            ],
            "resolved_threads": ["张三的动机已明确"],
        }

        result = compress_ledger_by_priority(ledger)

        # Verify structure preserved
        assert result["version"] == 2
        assert len(result["characters"]) == 2
        assert "张三" in result["characters"]
        assert "李四" in result["characters"]

        # Verify important items preserved
        assert any("真相" in f or "身份" in f for f in result["facts"])
        assert len(result["timeline"]) == 2
        assert len(result["open_threads"]) == 2


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_none_ledger(self):
        result = compress_ledger_by_priority(None)
        assert result["version"] == 1
        assert result["facts"] == []

    def test_non_dict_ledger(self):
        result = compress_ledger_by_priority("invalid")
        assert result["version"] == 1
        assert result["facts"] == []

    def test_missing_fields(self):
        ledger = {"version": 1}  # Only version, no other fields
        result = compress_ledger_by_priority(ledger)
        assert result["facts"] == []
        assert result["timeline"] == []
        assert result["characters"] == {}

    def test_wrong_type_fields(self):
        ledger = {
            "facts": "not a list",
            "timeline": 123,
            "characters": ["not", "a", "dict"],
        }
        result = compress_ledger_by_priority(ledger)
        assert result["facts"] == []
        assert result["timeline"] == []
        assert result["characters"] == {}

    def test_zero_max_config(self):
        """Test with zero limits returns empty lists."""
        ledger = {
            "facts": ["fact1", "fact2"],
            "timeline": [{"episode_number": 1}],
        }
        config = CompressionConfig(
            max_facts=0,
            max_timeline=0,
            max_open_threads=0,
            max_resolved_threads=0,
            max_info_events=0,
        )
        result = compress_ledger_by_priority(ledger, config)
        assert result["facts"] == []
        assert result["timeline"] == []
