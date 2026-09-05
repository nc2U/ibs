import html
from django.db import migrations
from django.utils.html import strip_tags


def backfill_activity_logs(apps, schema_editor):
    ActivityLogEntry = apps.get_model('work', 'ActivityLogEntry')
    Issue = apps.get_model('work', 'Issue')
    Meeting = apps.get_model('work', 'Meeting')
    Post = apps.get_model('forum', 'Post')

    # 1. Post (id 1 ~ 7)
    for post_id in range(1, 8):
        try:
            p = Post.objects.get(pk=post_id)
            clean_text = ' '.join(html.unescape(strip_tags(p.content or '')).split())
            ActivityLogEntry.objects.filter(id=post_id, target_id__isnull=True).update(
                target_id=p.id,
                parent_id=p.forum_id,
                title=f"[게시물] {p.title}"[:250],
                summary=clean_text[:150],
            )
        except Post.DoesNotExist:
            pass

    # 2. Meetings (id=10: meeting 10, id=11: meeting 11, id=15: meeting 12, id=16: meeting 13, id=17: meeting 14)
    meeting_map = {
        10: 10,
        11: 11,
        15: 12,
        16: 13,
        17: 14,
    }
    for log_id, meeting_id in meeting_map.items():
        try:
            m = Meeting.objects.get(pk=meeting_id)
            raw_summary = m.agenda or m.content or ''
            clean_text = ' '.join(html.unescape(strip_tags(raw_summary)).split())
            ActivityLogEntry.objects.filter(id=log_id, target_id__isnull=True).update(
                target_id=m.id,
                title=f"[회의록] #{m.pk} (등록) {m.title}"[:250],
                summary=clean_text[:150],
            )
        except Meeting.DoesNotExist:
            pass

    # 3. Issues
    # id=8: issue 336 (완료 상태 변경)
    # id=9: issue 333 (완료 상태 변경)
    # id=12: issue 324 (완료 상태 변경)
    # id=13: issue 337 (생성 - 등록 당시 상태 '준비')
    # id=14: issue 337 (완료 상태 변경)
    # id=18: issue 338 (생성 - 등록 당시 상태 '진행')
    # id=19: issue 338 (완료 상태 변경)
    issue_configs = {
        8: {'issue_id': 336, 'status': '완료', 'subject_override': None},
        9: {'issue_id': 333, 'status': '완료', 'subject_override': None},
        12: {'issue_id': 324, 'status': '완료', 'subject_override': None},
        13: {'issue_id': 337, 'status': '준비', 'subject_override': '업무 검색 시 검색 필터 데이터 pinia 로 이관'},
        14: {'issue_id': 337, 'status': '완료', 'subject_override': None},
        18: {'issue_id': 338, 'status': '진행', 'subject_override': None},
        19: {'issue_id': 338, 'status': '완료', 'subject_override': None},
    }

    for log_id, config in issue_configs.items():
        try:
            i = Issue.objects.get(pk=config['issue_id'])
            tracker_name = i.tracker.name if i.tracker else ''
            status_name = config['status']
            subject = config['subject_override'] or i.subject
            raw_summary = i.description or ''
            clean_summary = ' '.join(html.unescape(strip_tags(raw_summary)).split())

            ActivityLogEntry.objects.filter(id=log_id).update(
                target_id=i.id,
                title=f"[{tracker_name}] #{i.pk} ({status_name}) {subject}"[:250],
                summary=clean_summary[:150],
            )
        except Issue.DoesNotExist:
            pass


def reverse_backfill(apps, schema_editor):
    ActivityLogEntry = apps.get_model('work', 'ActivityLogEntry')
    ActivityLogEntry.objects.filter(id__in=range(1, 20)).update(
        target_id=None,
        parent_id=None,
        title='',
        summary='',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('work', '0009_remove_activitylogentry_comment_and_more'),
        ('forum', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(backfill_activity_logs, reverse_backfill),
    ]
