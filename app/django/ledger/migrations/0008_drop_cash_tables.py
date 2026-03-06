"""
cash 앱 테이블 정리 마이그레이션

cash 앱 데이터는 ledger 앱(ProjectBankTransaction, ProjectAccountingEntry 등)으로
이관 완료되었으므로 cash 앱 테이블과 django_migrations 기록을 제거합니다.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ledger', '0007_companyaccount_is_transfer_fee_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                DROP TABLE IF EXISTS cash_projectcashbookcalculation CASCADE;
                DROP TABLE IF EXISTS cash_companycashbookcalculation CASCADE;
                DROP TABLE IF EXISTS cash_projectcashbook CASCADE;
                DROP TABLE IF EXISTS cash_cashbook CASCADE;
                DROP TABLE IF EXISTS cash_projectbankaccount CASCADE;
                DROP TABLE IF EXISTS cash_companybankaccount CASCADE;
                DROP TABLE IF EXISTS cash_importjob CASCADE;
                DROP TABLE IF EXISTS cash_bankcode CASCADE;
                DELETE FROM django_migrations WHERE app = 'cash';
            """,
            reverse_sql=migrations.RunSQL.noop,
        )
    ]
