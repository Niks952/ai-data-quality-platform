from services.dq.rule_repository import get_enabled_rules


def test_get_enabled_rules():

    rules = get_enabled_rules("transactions")

    assert len(rules) == 8

    rule_types = {
        rule["rule_type"]
        for rule in rules
    }

    assert "NOT_NULL" in rule_types
    assert "RANGE" in rule_types
    assert "ENUM" in rule_types