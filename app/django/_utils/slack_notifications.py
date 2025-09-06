import json
import requests
import logging
from django.conf import settings

from work.models.project import IssueProject, Member
from cash.models import CashBook, ProjectCashBook
from docs.models import LawsuitCase, Document

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
                
    elif hasattr(model_instance, 'issue_project'):  # LawsuitCase, Document 등
        # 직접 IssueProject와 연결된 모델
        issue_project = model_instance.issue_project
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
    
    @staticmethod
    def build_lawsuitcase_message(instance, action, user):
        """LawsuitCase 메시지 생성"""
        color = 'good' if action == '생성' else '#ff9500' if action == '수정' else 'danger'
        
        # 법원명 또는 기타 처리기관
        agency = instance.get_court_display() if instance.get_court_display() else instance.other_agency
        
        fields = [
            {'title': '사건유형', 'value': instance.get_sort_display(), 'short': True},
            {'title': '심급', 'value': instance.get_level_display() if instance.level else '-', 'short': True},
            {'title': '법원/기관', 'value': agency, 'short': True},
            {'title': '사건번호', 'value': instance.case_number, 'short': True},
            {'title': '사건명', 'value': instance.case_name, 'short': False},
            {'title': '원고(신청인)', 'value': instance.plaintiff or '-', 'short': True},
            {'title': '피고(피신청인)', 'value': instance.defendant, 'short': True},
            {'title': '사건개시일', 'value': str(instance.case_start_date), 'short': True},
            {'title': '등록자', 'value': user.username if user else '시스템', 'short': True}
        ]
        
        if instance.case_end_date:
            fields.append({'title': '사건종결일', 'value': str(instance.case_end_date), 'short': True})
        
        return {
            'text': f"⚖️ *소송사건 {action}*",
            'attachments': [{
                'color': color,
                'fields': fields,
                'footer': f'LawsuitCase ID: {instance.id}',
                'ts': int(instance.updated.timestamp())
            }]
        }
    
    @staticmethod
    def build_document_message(instance, action, user):
        """Document 메시지 생성"""
        color = 'good' if action == '생성' else '#ff9500' if action == '수정' else 'danger'
        
        fields = [
            {'title': '문서유형', 'value': instance.doc_type.get_type_display(), 'short': True},
            {'title': '카테고리', 'value': instance.category.name if instance.category else '-', 'short': True},
            {'title': '제목', 'value': instance.title, 'short': False},
            {'title': '등록자', 'value': user.username if user else '시스템', 'short': True}
        ]
        
        if instance.lawsuit:
            fields.append({'title': '관련사건', 'value': str(instance.lawsuit), 'short': False})
        
        if instance.execution_date:
            fields.append({'title': '시행일자', 'value': str(instance.execution_date), 'short': True})
        
        # 보안 문서 표시
        if instance.is_secret:
            fields.append({'title': '보안', 'value': '🔒 비밀문서', 'short': True})
        
        return {
            'text': f"📄 *문서 {action}*",
            'attachments': [{
                'color': color,
                'fields': fields,
                'footer': f'Document ID: {instance.id}',
                'ts': int(instance.updated.timestamp())
            }]
        }


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
    elif isinstance(instance, LawsuitCase):
        message_data = SlackMessageBuilder.build_lawsuitcase_message(instance, action, user)
    elif isinstance(instance, Document):
        message_data = SlackMessageBuilder.build_document_message(instance, action, user)
    
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