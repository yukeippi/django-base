from django.contrib.auth.models import User
from django.db.models import Model
from app.permissions import rule_sets
from app.permissions.roles import get_applicable_management_groups


# 対象レコードを閲覧できるかどうかを判定する(fieldを指定するとカラム単位の判定になる)
def can_view(user: User, model_name: str, instance: Model, field: str | None = None) -> bool:
    return _check(user, model_name, 'view', instance=instance, field=field)


# 新規作成しようとしている未保存インスタンス(candidate)を作成できるかどうかを判定する
def can_create(user: User, model_name: str, candidate: Model) -> bool:
    return _check(user, model_name, 'create', instance=candidate)


# 対象レコードを編集できるかどうかを判定する(fieldを指定するとカラム単位の判定になる)
def can_edit(user: User, model_name: str, instance: Model, field: str | None = None) -> bool:
    return _check(user, model_name, 'edit', instance=instance, field=field)


# 対象レコードを削除できるかどうかを判定する
def can_delete(user: User, model_name: str, instance: Model) -> bool:
    return _check(user, model_name, 'delete', instance=instance)


# 対象レコードに対して実行系の操作ができるかどうかを判定する
def can_execute(user: User, model_name: str, instance: Model) -> bool:
    return _check(user, model_name, 'execute', instance=instance)


# 具体的な入力値が無い状態(newのGET)で、作成フォームを表示してよいかどうかを判定する
# (scopeによる絞り込みは行わず、createにallowのルールを持つグループが1つでもあればTrue)
def can_display_create_form(user: User, model_name: str) -> bool:
    for group in get_applicable_management_groups(user):
        if group.is_admin:
            return True
        rule_set = rule_sets.REGISTRY[group.permission_set_id]
        rule = _find_rule(rule_set, model_name, 'record', 'create')
        if rule is not None and rule['effect'] == 'allow':
            return True
    return False


# ============================================================
# ここから先はprivateヘルパー
# ============================================================


# ユーザーに適用される全ManagementGroupの判定をdeny優先でマージする
def _check(user, model_name, action, instance=None, field=None):
    level = 'field' if field is not None else 'record'
    decisions = [
        _decide(group, model_name, level, action, instance, field)
        for group in get_applicable_management_groups(user)
    ]
    decisions = [decision for decision in decisions if decision is not None]  # 棄権を除外
    if 'deny' in decisions:
        return False
    return 'allow' in decisions


# 1つのManagementGroupの判定を返す('allow'/'deny'/棄権を表すNone)
def _decide(group, model_name, level, action, instance, field):
    if group.is_admin:
        return 'allow'
    rule_set = rule_sets.REGISTRY[group.permission_set_id]
    rule = _find_rule(rule_set, model_name, level, action, field)
    if rule is None:
        return 'deny'
    if level == 'field':
        return rule['effect']
    if not _matches(instance, rule['scope']):
        return None  # 棄権
    return rule['effect']


# ルールセットの中から、model・level・action(・field)が一致するルールを1件探す
def _find_rule(rule_set, model_name, level, action, field=None):
    for rule in rule_set.RULES:
        if rule['model'] != model_name or rule['level'] != level or rule['action'] != action:
            continue
        if level == 'field' and rule.get('field') != field:
            continue
        return rule
    return None


# scopeの各条件がtargetに一致するかを判定する
def _matches(target, scope):
    for path, expected in scope.items():
        actual = _resolve_path(target, path)
        if isinstance(expected, (list, tuple, set)):
            if actual not in expected:
                return False
        elif actual != expected:
            return False
    return True


# 'company.name'のような'.'区切りのパスをtargetの属性から辿って値を取得する
def _resolve_path(target, path):
    value = target
    for attr in path.split('.'):
        value = getattr(value, attr)
    return value
