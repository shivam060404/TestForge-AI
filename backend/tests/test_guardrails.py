import pytest

from core.ai.guardrails import GuardrailViolation, parse_and_validate_steps, validate_intent


def test_validates_safe_steps_and_normalizes_order():
    steps = parse_and_validate_steps({
        "steps": [
            {"order": 99, "action": "goto", "target": "/login"},
            {"order": 99, "action": "assert", "assertion": {"type": "visible", "expected": True}},
        ]
    })

    assert [step["order"] for step in steps] == [0, 1]


def test_rejects_unsupported_actions():
    with pytest.raises(GuardrailViolation):
        parse_and_validate_steps({"steps": [{"action": "delete_database"}]})


def test_rejects_empty_intent():
    with pytest.raises(GuardrailViolation):
        validate_intent(" ")
