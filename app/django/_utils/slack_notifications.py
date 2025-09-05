import json
import requests
import logging
from django.conf import settings

from work.models.project import IssueProject, Member
from cash.models import CashBook, ProjectCashBook

logger = logging.getLogger(__name__)


def get_target_issue_project(model_instance):
    """모델 인스턴스에서 대상 IssueProject 추출"""
    
    if hasattr(model_instance, 'company'):  # CashBook
        # Company의 본사관리 IssueProject 찾기
        return IssueProject.objects.filter(
            company=model_instance.company,
            sort='1',  # 본사관리
            slack_notifications_enabled=True,
            slack_webhook_url__isnull=False
        ).first()
        
    elif hasattr(model_instance, 'project'):  # ProjectCashBook, Contract 등
        # Project의 연결된 IssueProject
        project = model_instance.project
        if hasattr(project, 'issue_project'):
            issue_project = project.issue_project
            if (issue_project.slack_notifications_enabled and 
                issue_project.slack_webhook_url):
                return issue_project
    
    return None


def get_authorized_members(issue_project, action_type='view'):
    """해당 IssueProject의 알림 권한이 있는 멤버 조회"""
    
    # 모든 멤버를 대상으로 하거나, 특정 권한을 가진 멤버만 선택
    members = issue_project.members.all()
    
    # TODO: 추후 더 세밀한 권한 제어 필요 시 Role의 Permission 체크
    # members = issue_project.members.filter(
    #     roles__permissions__code__in=[
    #         'cashbook_view', 'project_manage', 'finance_manage'
    #     ]
    # ).distinct()
    
    return members


class SlackMessageBuilder:
    """Slack 메시지 포맷팅 클래스"""
    
    @staticmethod
    def build_cashbook_message(instance, action, user):
        """CashBook 또는 ProjectCashBook 메시지 생성"""
        
        if isinstance(instance, CashBook):
            # 본사 업무 메시지
            color = 'good' if action == '생성' else '#ff9500' if action == '수정' else 'danger'
            
            fields = [
                {'title': '회사', 'value': instance.company.name, 'short': True},
                {'title': '구분', 'value': str(instance.sort), 'short': True},
                {'title': '거래처', 'value': instance.trader or '-', 'short': True},
                {'title': '적요', 'value': instance.content or '-', 'short': True},
            ]
            
            if instance.income:
                fields.append({'title': '입금액', 'value': f'{instance.income:,}원', 'short': True})
            if instance.outlay:
                fields.append({'title': '출금액', 'value': f'{instance.outlay:,}원', 'short': True})
                
            fields.extend([
                {'title': '거래일', 'value': str(instance.deal_date), 'short': True},
                {'title': '등록자', 'value': user.username if user else '시스템', 'short': True}
            ])
            
            return {
                'text': f"💰 *본사 입출금 {action}*",
                'attachments': [{
                    'color': color,
                    'fields': fields,
                    'footer': f'CashBook ID: {instance.id}',
                    'ts': int(instance.updated_at.timestamp())
                }]
            }
        
        elif isinstance(instance, ProjectCashBook):
            # 프로젝트 업무 메시지  
            color = 'good' if action == '생성' else '#ff9500' if action == '수정' else 'danger'
            
            fields = [
                {'title': '프로젝트', 'value': instance.project.name, 'short': True},
                {'title': '구분', 'value': str(instance.sort), 'short': True},
                {'title': '거래처', 'value': instance.trader or '-', 'short': True},
                {'title': '적요', 'value': instance.content or '-', 'short': True},
            ]
            
            if instance.income:
                fields.append({'title': '입금액', 'value': f'{instance.income:,}원', 'short': True})
            if instance.outlay:
                fields.append({'title': '출금액', 'value': f'{instance.outlay:,}원', 'short': True})
                
            fields.extend([
                {'title': '거래일', 'value': str(instance.deal_date), 'short': True},
                {'title': '등록자', 'value': user.username if user else '시스템', 'short': True}
            ])
            
            return {
                'text': f"🏗️ *프로젝트 입출금 {action}*",
                'attachments': [{
                    'color': color,
                    'fields': fields,
                    'footer': f'ProjectCashBook ID: {instance.id}',
                    'ts': int(instance.updated_at.timestamp())
                }]
            }
        
        return None


def send_slack_message(webhook_url, message_data):
    """Slack 웹훅으로 메시지 전송"""
    
    try:
        response = requests.post(
            webhook_url,
            json=message_data,
            timeout=10,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            logger.info(f"Slack 메시지 전송 성공: {webhook_url}")
            return True
        else:
            logger.error(f"Slack 메시지 전송 실패 ({response.status_code}): {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Slack 메시지 전송 중 오류: {str(e)}")
        return False


def send_slack_notification(instance, action, user=None):
    """통합 Slack 알림 전송 함수"""
    
    # Slack 알림이 비활성화된 경우 종료
    if not getattr(settings, 'SLACK_NOTIFICATIONS_ENABLED', True):
        return
    
    # 대상 IssueProject 찾기
    issue_project = get_target_issue_project(instance)
    if not issue_project:
        logger.info(f"Slack 알림 대상 프로젝트를 찾을 수 없음: {instance}")
        return
    
    # 메시지 생성
    message_data = None
    if isinstance(instance, (CashBook, ProjectCashBook)):
        message_data = SlackMessageBuilder.build_cashbook_message(instance, action, user)
    
    if not message_data:
        logger.warning(f"지원하지 않는 모델 타입: {type(instance)}")
        return
    
    # Slack 메시지 전송
    success = send_slack_message(issue_project.slack_webhook_url, message_data)
    
    if success:
        # 권한 있는 멤버들 로그 (선택적)
        members = get_authorized_members(issue_project)
        member_names = [member.user.username for member in members if member.user]
        logger.info(f"Slack 알림 전송 완료 - 프로젝트: {issue_project.name}, 멤버: {', '.join(member_names)}")