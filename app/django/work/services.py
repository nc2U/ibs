from work.models.logging import ActivityLogEntry, IssueLogEntry


class IssueService:
    @staticmethod
    def track_changes(instance):
        """이슈 저장 전 변경사항 추적"""
        if instance.pk:
            try:
                from work.models.issue import Issue
                old_instance = Issue.objects.get(pk=instance.pk)
                fields_to_track = [
                    'project', 'tracker', 'status', 'priority', 'subject',
                    'description', 'category', 'fixed_version', 'assigned_to',
                    'parent', 'watchers', 'is_private', 'expected_duration',
                    'start_date', 'due_date', 'done_ratio', 'closed'
                ]
                for field in fields_to_track:
                    old_val = getattr(old_instance, field)
                    new_val = getattr(instance, field)
                    if old_val != new_val:
                        setattr(instance, f'old_{field}', old_val)
            except Exception:
                pass

    @staticmethod
    def log_and_notify(instance, created, user):
        """이슈 변경 로그 기록 및 메일 알림"""
        action = "Created" if created else "Updated"
        status_log = ""
        details = f"**업무** - *{instance}(#{instance.id})*업무가 *{action}* 되었습니다." if created else ""
        diff = ""
        parent_details = ""

        # 변경 필드별 상세 내용 구성 (signals.py 로직 기반)
        tracked_fields = {
            'project': '프로젝트', 'tracker': '유형', 'status': '상태',
            'priority': '우선순위', 'subject': '제목', 'description': '설명',
            'category': '범주', 'fixed_version': '목표 단계', 'assigned_to': '담당자',
            'parent': '상위 업무', 'watchers': '업무 관람자', 'is_private': '비공개 설정',
            'expected_duration': '예상 처리기간', 'start_date': '시작 일자',
            'due_date': '완료일', 'done_ratio': '진척도', 'closed': '해당 업무'
        }

        for field, label in tracked_fields.items():
            old_attr = f'old_{field}'
            if hasattr(instance, old_attr):
                old_val = getattr(instance, old_attr)
                new_val = getattr(instance, field)

                if field == 'status':
                    status_log = instance.status.name

                if field == 'description':
                    details += f"|- **{label}**이 변경되었습니다."
                    diff += f"**변경전 :**\n{old_val}\n---\n**변경후 :**\n{new_val}"
                elif field == 'expected_duration':
                    old_display = instance.get_expected_duration_display() if not old_val else next(
                        (c[1] for c in instance._meta.get_field('expected_duration').choices if c[0] == old_val),
                        old_val)
                    new_display = instance.get_expected_duration_display()
                    desc = f" *{old_display}*에서 " if old_val else ""
                    act = "변경" if old_val else "지정"
                    details += f"|- **{label}**가 {desc}*{new_display}*(으)로 {act}되었습니다."
                elif field == 'parent':
                    desc = f" *{old_val}*에서 " if old_val else ""
                    act = "변경" if old_val else "지정"
                    details += f"|- **{label}**가 {desc}#{instance.parent.pk} *{instance.parent}*(으)로 {act}되었습니다."
                    parent_details = f"|- **하위 업무**에 #{instance.pk} *{instance}*이(가) 추가되었습니다."
                elif field == 'closed':
                    details += f"|- **{label}**가 *{instance.closed}*에 종료되었습니다."
                else:
                    desc = f" *{old_val}*에서 " if old_val else ""
                    act = "변경" if old_val else "지정"
                    details += f"|- **{label}**가 {desc}*{new_val}*(으)로 {act}되었습니다."

        if created:
            # 생성 로그 및 알림
            ActivityLogEntry.objects.create(sort='1', project=instance.project, issue=instance, creator=user)
            IssueService.send_issue_mail(instance, user, "create")
        else:
            # 워처 관리 로직 추가
            watchers = set(instance.watchers.all())
            old_assigned_to = getattr(instance, "old_assigned_to", None)

            if old_assigned_to and old_assigned_to not in {instance.creator, user} and old_assigned_to in watchers:
                instance.watchers.remove(old_assigned_to)
            if instance.creator and instance.creator not in watchers:
                instance.watchers.add(instance.creator)
            if instance.assigned_to and instance.assigned_to not in watchers:
                instance.watchers.add(instance.assigned_to)
            if user and user != instance.assigned_to and user not in watchers:
                instance.watchers.add(user)

            # 수정 로그 및 알림
            if details:
                IssueLogEntry.objects.create(issue=instance, action=action, details=details, diff=diff, creator=user)
                if hasattr(instance, 'old_parent') and parent_details and instance.parent:
                    IssueLogEntry.objects.create(issue=instance.parent, action=action, details=parent_details,
                                                 diff=diff, creator=user)

                if hasattr(instance, 'old_status'):
                    ActivityLogEntry.objects.create(sort='1', project=instance.project, issue=instance,
                                                    status_log=status_log, creator=user)
                    IssueService.send_issue_mail(instance, user, "progress")

                if hasattr(instance, 'old_assigned_to'):
                    IssueService.send_issue_mail(instance, user, "reassign")

    @staticmethod
    def send_issue_mail(instance, user, mail_type):
        """이슈 관련 메일 발송 유틸리티 (Celery 비동기 호출)"""
        from work.tasks import send_issue_mail_task
        send_issue_mail_task.delay(instance.pk, user.pk, mail_type)
