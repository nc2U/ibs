import json
import requests
import logging
from django.conf import settings

from work.models.project import IssueProject, Member
from cash.models import CashBook, ProjectCashBook
from docs.models import LawsuitCase, Document
from contract.models import Contract, Succession, ContractorRelease

logger = logging.getLogger(__name__)
SYSTEM_NAME = 'IBS 건설관리시스템'


def get_service_url(model_instance):
    """모델 인스턴스에 대한 서비스 URL 생성"""
    base_url = getattr(settings, 'DOMAIN_HOST', 'http://localhost:5173')
    base_url = base_url.rstrip('/')  # DOMAIN_HOST가 '/'로 끝나면 제거

    # issue_project 접근 방식 결정
    if hasattr(model_instance, 'issue_project'):
        issue_project = model_instance.issue_project
    elif hasattr(model_instance, 'project') and hasattr(model_instance.project, 'issue_project'):
        issue_project = model_instance.project.issue_project
    else:
        issue_project = None

    prefix = '' if (issue_project and issue_project.sort == '1') else 'project-'

    if isinstance(model_instance, CashBook):
        return f"{base_url}/#/cashes/index"  # /{model_instance.id}"
    elif isinstance(model_instance, ProjectCashBook):
        return f"{base_url}/#/project-cash/index"  # /{model_instance.id}"
    elif isinstance(model_instance, LawsuitCase):
        return f"{base_url}/#/{prefix}docs/lawsuit/case/{model_instance.id}"
    elif isinstance(model_instance, Document):
        sort_docs = 'lawsuit' if model_instance.lawsuit else 'general'
        return f"{base_url}/#/{prefix}docs/{sort_docs}/docs/{model_instance.id}"
    elif isinstance(model_instance, Contract):
        return f"{base_url}/#/contracts/index/{model_instance.id}"
    elif isinstance(model_instance, Succession):
        return f"{base_url}/#/contracts/succession/{model_instance.id}"
    elif isinstance(model_instance, ContractorRelease):
        return f"{base_url}/#/contracts/release/{model_instance.id}"

    return base_url


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
        """CashBook 또는 ProjectCashBook 간소화된 메시지 생성"""
        service_url = get_service_url(instance)

        if isinstance(instance, CashBook):
            # 본사 입출금
            title = f"💰 [본사 입출금]-{instance.company.name} - {instance.content or '------'}"
        elif isinstance(instance, ProjectCashBook):
            # 프로젝트 입출금
            title = f"🏗️ [프로젝트 입출금]-{instance.project.name} - {instance.content or '------'}"
        else:
            return None

        color = 'good' if action == '생성' else '#ff9500' if action == '수정' else 'danger'

        # 수정 시 updator와 creator 정보 표시
        if action == '수정' and hasattr(instance, 'updator') and instance.updator:
            user_text = f"수정자: {instance.updator.username}"
            if hasattr(instance, 'creator') and instance.creator:
                user_text += f" (등록자: {instance.creator.username})"
        else:
            # 생성 시나 updator가 없는 경우 기존 방식
            user_text = f"등록자: {user.username if user else '시스템'}"

        return {
            'attachments': [{
                'color': color,
                'title': f"{title} ({action})",
                'title_link': service_url,
                'text': user_text,
                'actions': [{
                    'type': 'button',
                    'text': '상세보기',
                    'url': service_url,
                    'style': 'primary'
                }],
                'footer': f'{SYSTEM_NAME}',
                'ts': int((instance.updated_at if hasattr(instance, 'updated_at') else instance.updated).timestamp())
            }]
        }

    @staticmethod
    def build_lawsuitcase_message(instance, action, user):
        """LawsuitCase 간소화된 메시지 생성"""
        service_url = get_service_url(instance)
        color = 'good' if action == '생성' else '#ff9500' if action == '수정' else 'danger'

        # 간소화된 제목: 법원 + 사건번호 + 사건명
        agency = instance.get_court_display() if instance.get_court_display() else instance.other_agency
        title = f"⚖️ {agency} {instance.case_number} - {instance.case_name}"

        # 수정 시 updator와 creator 정보 표시
        if action == '수정' and hasattr(instance, 'updator') and instance.updator:
            user_text = f"수정자: {instance.updator.username}"
            if hasattr(instance, 'creator') and instance.creator:
                user_text += f" (등록자: {instance.creator.username})"
        else:
            # 생성 시나 updator가 없는 경우 기존 방식
            user_text = f"등록자: {user.username if user else '시스템'}"

        return {
            'attachments': [{
                'color': color,
                'title': f"{title} ({action})",
                'title_link': service_url,
                'text': user_text,
                'actions': [{
                    'type': 'button',
                    'text': '상세보기',
                    'url': service_url,
                    'style': 'primary'
                }],
                'footer': f'{SYSTEM_NAME}',
                'ts': int(instance.updated.timestamp())
            }]
        }

    @staticmethod
    def build_document_message(instance, action, user):
        """Document 간소화된 메시지 생성"""
        service_url = get_service_url(instance)
        color = 'good' if action == '생성' else '#ff9500' if action == '수정' else 'danger'

        # 간소화된 제목: 문서유형 + 제목 + 보안표시
        doc_type = instance.doc_type.get_type_display()
        title = f"📄 [{doc_type}] {instance.title}"

        # 보안 문서 표시
        if instance.is_secret:
            title = f"🔒 {title}"

        # 수정 시 updator와 creator 정보 표시
        if action == '수정' and hasattr(instance, 'updator') and instance.updator:
            user_text = f"수정자: {instance.updator.username}"
            if hasattr(instance, 'creator') and instance.creator:
                user_text += f" (등록자: {instance.creator.username})"
        else:
            # 생성 시나 updator가 없는 경우 기존 방식
            user_text = f"등록자: {user.username if user else '시스템'}"

        return {
            'attachments': [{
                'color': color,
                'title': f"{title} ({action})",
                'title_link': service_url,
                'text': user_text,
                'actions': [{
                    'type': 'button',
                    'text': '상세보기',
                    'url': service_url,
                    'style': 'primary'
                }],
                'footer': f'{SYSTEM_NAME}',
                'ts': int(instance.updated.timestamp())
            }]
        }

    @staticmethod
    def build_contract_message(instance, action, user):
        """Contract 간소화된 메시지 생성"""
        service_url = get_service_url(instance)
        color = 'good' if action == '생성' else '#ff9500' if action == '수정' else 'danger'

        # 간소화된 제목: 프로젝트명 + 계약번호
        title = f"📋 [계약]-[{instance.project.name}] {instance.serial_number}"

        return {
            'attachments': [{
                'color': color,
                'title': f"{title} ({action})",
                'title_link': service_url,
                'text': f"등록자: {user.username if user else '시스템'}",
                'actions': [{
                    'type': 'button',
                    'text': '상세보기',
                    'url': service_url,
                    'style': 'primary'
                }],
                'footer': f'{SYSTEM_NAME}',
                'ts': int(instance.updated_at.timestamp())
            }]
        }

    @staticmethod
    def build_succession_message(instance, action, user):
        """Succession 간소화된 메시지 생성"""
        service_url = get_service_url(instance)
        color = 'good' if action == '생성' else '#ff9500' if action == '수정' else 'danger'

        # 간소화된 제목: 프로젝트명 + 양도승계 + 양도자→양수자
        title = f"🔄 [계약승계]-[{instance.contract.project.name}] :: {instance.seller.name} → {instance.buyer.name}"

        return {
            'attachments': [{
                'color': color,
                'title': f"{title} ({action})",
                'title_link': service_url,
                'text': f"등록자: {user.username if user else '시스템'}",
                'actions': [{
                    'type': 'button',
                    'text': '상세보기',
                    'url': service_url,
                    'style': 'primary'
                }],
                'footer': f'{SYSTEM_NAME}',
                'ts': int(instance.updated_at.timestamp())
            }]
        }

    @staticmethod
    def build_contractor_release_message(instance, action, user):
        """ContractorRelease 간소화된 메시지 생성"""
        service_url = get_service_url(instance)
        color = 'good' if action == '생성' else '#ff9500' if action == '수정' else 'danger'

        # 간소화된 제목: 프로젝트명 + 해지 + 계약자명
        status_display = instance.get_status_display()
        title = f"❌ [계약해지]-[{instance.project.name}] {status_display} - {instance.contractor.name}"

        return {
            'attachments': [{
                'color': color,
                'title': f"{title} ({action})",
                'title_link': service_url,
                'text': f"등록자: {user.username if user else '시스템'}",
                'actions': [{
                    'type': 'button',
                    'text': '상세보기',
                    'url': service_url,
                    'style': 'primary'
                }],
                'footer': f'{SYSTEM_NAME}',
                'ts': int(instance.updated_at.timestamp())
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
    elif isinstance(instance, Contract):
        message_data = SlackMessageBuilder.build_contract_message(instance, action, user)
    elif isinstance(instance, Succession):
        message_data = SlackMessageBuilder.build_succession_message(instance, action, user)
    elif isinstance(instance, ContractorRelease):
        message_data = SlackMessageBuilder.build_contractor_release_message(instance, action, user)

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
