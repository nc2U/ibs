from django.db import migrations
from django.contrib.postgres.operations import TrigramExtension


class Migration(migrations.Migration):

    dependencies = [
        ('work', '0003_issuecomment_is_blocked_issuecomment_updater'),
    ]

    operations = [
        # pg_trgm 확장 활성화 (이미 설치된 경우 무시됨)
        TrigramExtension(),

        # Issue: 제목 + 설명 GIN 인덱스
        migrations.RunSQL(
            sql="""
                CREATE INDEX IF NOT EXISTS work_issue_subject_trgm
                    ON work_issue USING GIN (subject gin_trgm_ops);
                CREATE INDEX IF NOT EXISTS work_issue_description_trgm
                    ON work_issue USING GIN (description gin_trgm_ops);
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS work_issue_subject_trgm;
                DROP INDEX IF EXISTS work_issue_description_trgm;
            """,
        ),

        # IssueComment: 댓글 내용 GIN 인덱스
        migrations.RunSQL(
            sql="""
                CREATE INDEX IF NOT EXISTS work_issuecomment_content_trgm
                    ON work_issuecomment USING GIN (content gin_trgm_ops);
            """,
            reverse_sql="DROP INDEX IF EXISTS work_issuecomment_content_trgm;",
        ),

        # Meeting: 제목 + 의제 + 결정사항 GIN 인덱스
        migrations.RunSQL(
            sql="""
                CREATE INDEX IF NOT EXISTS work_meeting_title_trgm
                    ON work_meeting USING GIN (title gin_trgm_ops);
                CREATE INDEX IF NOT EXISTS work_meeting_agenda_trgm
                    ON work_meeting USING GIN (agenda gin_trgm_ops);
                CREATE INDEX IF NOT EXISTS work_meeting_decisions_trgm
                    ON work_meeting USING GIN (decisions gin_trgm_ops);
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS work_meeting_title_trgm;
                DROP INDEX IF EXISTS work_meeting_agenda_trgm;
                DROP INDEX IF EXISTS work_meeting_decisions_trgm;
            """,
        ),

        # News: 제목 + 요약 + 내용 GIN 인덱스
        migrations.RunSQL(
            sql="""
                CREATE INDEX IF NOT EXISTS work_news_title_trgm
                    ON work_news USING GIN (title gin_trgm_ops);
                CREATE INDEX IF NOT EXISTS work_news_summary_trgm
                    ON work_news USING GIN (summary gin_trgm_ops);
                CREATE INDEX IF NOT EXISTS work_news_content_trgm
                    ON work_news USING GIN (content gin_trgm_ops);
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS work_news_title_trgm;
                DROP INDEX IF EXISTS work_news_summary_trgm;
                DROP INDEX IF EXISTS work_news_content_trgm;
            """,
        ),
    ]
