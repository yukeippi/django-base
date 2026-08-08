# 「会社情報は全員閲覧可能、特定の会社の部門情報のみ閲覧・編集できる」権限セットの例

ID = 2
NAME = 'サンプル株式会社 部門管理者'
DESCRIPTION = 'サンプル株式会社に属する部門情報のみ閲覧・編集できる権限セット。会社情報は全社共通で閲覧のみ許可する。'

RULES = [
    {'model': 'Company', 'level': 'record', 'action': 'view', 'scope': {}, 'effect': 'allow'},

    {'model': 'Department', 'level': 'record', 'action': 'view',
     'scope': {'company.name': 'サンプル株式会社'}, 'effect': 'allow'},
    {'model': 'Department', 'level': 'record', 'action': 'edit',
     'scope': {'company.name': 'サンプル株式会社'}, 'effect': 'allow'},
    {'model': 'Department', 'level': 'record', 'action': 'create',
     'scope': {'company.name': 'サンプル株式会社'}, 'effect': 'allow'},
    {'model': 'Department', 'level': 'record', 'action': 'delete',
     'scope': {'company.name': 'サンプル株式会社'}, 'effect': 'deny'},

    # --- カラム権限(record権限がallowの範囲でのみ意味を持つ。テンプレート・フォームへの組み込みは別プランで行う) ---
    {'model': 'Department', 'level': 'field', 'field': 'company', 'action': 'edit', 'effect': 'deny',
     'note': '所属会社の変更(会社をまたぐ移動)はこの権限セットからは行えない'},
]
