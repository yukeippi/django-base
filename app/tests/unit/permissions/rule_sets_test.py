import pytest
from app.permissions import rule_sets

RECORD_ACTIONS = {'view', 'create', 'edit', 'delete', 'execute'}
FIELD_ACTIONS = {'view', 'edit'}
REQUIRED_RECORD_KEYS = {'model', 'level', 'action', 'scope', 'effect'}
REQUIRED_FIELD_KEYS = {'model', 'level', 'field', 'action', 'effect'}


# rule_sets.REGISTRYの構造をテストするクラス
class TestRuleSetsRegistry:

    # REGISTRYのキーが各ルールセットファイルのIDと一致することを確認
    def test_registry_keys_match_rule_set_ids(self):
        for permission_set_id, rule_set in rule_sets.REGISTRY.items():
            assert rule_set.ID == permission_set_id

    # 各ルールセットがNAME/DESCRIPTION/RULESを持つことを確認
    def test_each_rule_set_has_required_attributes(self):
        for rule_set in rule_sets.REGISTRY.values():
            assert isinstance(rule_set.NAME, str) and rule_set.NAME
            assert isinstance(rule_set.DESCRIPTION, str) and rule_set.DESCRIPTION
            assert isinstance(rule_set.RULES, list) and rule_set.RULES

    # 各ルールが定義形式(必須キーの組み合わせ)を満たすことを確認
    def test_each_rule_has_required_keys(self):
        for rule_set in rule_sets.REGISTRY.values():
            for rule in rule_set.RULES:
                if rule['level'] == 'record':
                    assert REQUIRED_RECORD_KEYS <= rule.keys()
                    assert rule['action'] in RECORD_ACTIONS
                    assert 'field' not in rule
                elif rule['level'] == 'field':
                    assert REQUIRED_FIELD_KEYS <= rule.keys()
                    assert rule['action'] in FIELD_ACTIONS
                    assert 'scope' not in rule
                else:
                    pytest.fail(f"未知のlevel: {rule['level']}")

    # 同じmodel・level・action(・field)の組み合わせのルールが重複していないことを確認
    def test_no_duplicate_rules(self):
        for rule_set in rule_sets.REGISTRY.values():
            keys = [
                (rule['model'], rule['level'], rule['action'], rule.get('field'))
                for rule in rule_set.RULES
            ]
            assert len(keys) == len(set(keys))
