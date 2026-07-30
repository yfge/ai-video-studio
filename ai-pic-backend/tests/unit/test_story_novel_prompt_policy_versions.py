from app.prompts.template_audit import sha256_text
from app.services.story.story_novel_prompt_renderer import (
    v3_prompt_template_policy,
    valid_v3_prompt_template_policy,
)


def test_v3_policy_remains_valid_as_a_frozen_historical_snapshot():
    policy = v3_prompt_template_policy(version=3)
    policy["templates"]["story_novel_proof_audit_v3"]["sources_hash"] = "historical"
    policy["hash"] = _policy_hash(policy["templates"])

    assert valid_v3_prompt_template_policy(policy)
    policy["hash"] = "tampered"
    assert not valid_v3_prompt_template_policy(policy)


def test_v4_policy_remains_readable_as_a_frozen_historical_snapshot():
    policy = v3_prompt_template_policy(version=4)

    assert valid_v3_prompt_template_policy(policy)
    policy["templates"]["story_novel_proof_audit_v3"]["sources_hash"] = "changed"
    policy["hash"] = _policy_hash(policy["templates"])
    assert valid_v3_prompt_template_policy(policy)


def test_v5_policy_remains_readable_as_a_frozen_historical_snapshot():
    policy = v3_prompt_template_policy(version=5)

    assert valid_v3_prompt_template_policy(policy)
    policy["templates"]["story_novel_proof_audit_v3"]["sources_hash"] = "changed"
    policy["hash"] = _policy_hash(policy["templates"])
    assert valid_v3_prompt_template_policy(policy)


def test_v6_policy_remains_readable_as_a_frozen_historical_snapshot():
    policy = v3_prompt_template_policy(version=6)

    assert valid_v3_prompt_template_policy(policy)
    policy["templates"]["story_novel_proof_audit_v3"]["sources_hash"] = "changed"
    policy["hash"] = _policy_hash(policy["templates"])
    assert valid_v3_prompt_template_policy(policy)


def test_v7_policy_remains_readable_as_a_frozen_historical_snapshot():
    policy = v3_prompt_template_policy(version=7)

    assert valid_v3_prompt_template_policy(policy)
    policy["templates"]["story_novel_proof_audit_v3"]["sources_hash"] = "changed"
    policy["hash"] = _policy_hash(policy["templates"])
    assert valid_v3_prompt_template_policy(policy)


def test_v8_policy_remains_readable_as_a_frozen_historical_snapshot():
    policy = v3_prompt_template_policy(version=8)

    assert valid_v3_prompt_template_policy(policy)
    policy["templates"]["story_novel_proof_audit_v3"]["sources_hash"] = "changed"
    policy["hash"] = _policy_hash(policy["templates"])
    assert valid_v3_prompt_template_policy(policy)


def test_v9_policy_must_match_current_template_sources():
    policy = v3_prompt_template_policy(version=9)

    assert valid_v3_prompt_template_policy(policy)
    policy["templates"]["story_novel_proof_audit_v3"]["sources_hash"] = "changed"
    policy["hash"] = _policy_hash(policy["templates"])
    assert not valid_v3_prompt_template_policy(policy)


def _policy_hash(templates):
    return sha256_text(
        "\n".join(
            f"{name}:{templates[name]['version']}:{templates[name]['sources_hash']}"
            for name in sorted(templates)
        )
    )
