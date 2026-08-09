# 「部門情報は原則アクセス不可だが、全部門を閲覧できる」権限セットの例

ID = 1
NAME = '全部門閲覧者'
DESCRIPTION = '部門情報を、会社・部門を問わず全件閲覧できる権限セット。編集・削除・作成は不可。'

RULES = [
    {'model': 'Department', 'level': 'record', 'action': 'view', 'scope': {}, 'effect': 'allow'},
    {'model': 'Department', 'level': 'record', 'action': 'create', 'scope': {}, 'effect': 'deny'},
    {'model': 'Department', 'level': 'record', 'action': 'edit', 'scope': {}, 'effect': 'deny'},
    {'model': 'Department', 'level': 'record', 'action': 'delete', 'scope': {}, 'effect': 'deny'},
    {'model': 'Department', 'level': 'record', 'action': 'execute', 'scope': {}, 'effect': 'deny'},
]
