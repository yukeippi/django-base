# Django Development Guidelines

## File Structure Rules

models、forms、views、tests、templatesはディレクトリ化し、機能ごとにファイル分割してください。

### Examples
- models/todo.py
- tests/models/todo_test.py
- tests/e2e/todo_crud_test.py

各ディレクトリに__init__.pyを配置すること。
