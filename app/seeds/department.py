from app.models import Company, Department


# 部門のシードデータを作成する
def create():
    sample = Company.objects.get(name='サンプル株式会社')
    Department.objects.create(company=sample, name='開発部')
    Department.objects.create(company=sample, name='営業部')

    test_industries = Company.objects.get(name='テスト工業株式会社')
    Department.objects.create(company=test_industries, name='総務部')
