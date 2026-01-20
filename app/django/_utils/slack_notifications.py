import requests
from decouple import config
from django.conf import settings
from django.contrib.humanize.templatetags.humanize import intcomma
from django.db.models import Q

from cash.models import CashBook, ProjectCashBook
from contract.models import Contract, Succession, ContractorRelease
from docs.models import LawsuitCase, Document
from ledger.models import CompanyBankTransaction, ProjectBankTransaction
from project.models import Site, SiteOwner, SiteContract
from work.models.project import IssueProject

SYSTEM_NAME = 'IBS 업무관리시스템'


def send_bulk_import_summary(summary_data, user=None, target_instance=None):
    """Excel 대량 가져오기 완료 후 Slack 요약 알림 전송"""
    if not getattr(settings, 'SLACK_NOTIFICATIONS_ENABLED', True):
        return False

    # target_instance가 제공된 경우 해당 프로젝트의 웹훅 URL 찾기
    webhook_url = None
    if target_instance:
        issue_project = get_target_issue_project(target_instance)
        if issue_project:
            webhook_url = get_slack_webhook_url(issue_project)

    # target_instance가 없거나 웹훅 URL을 찾지 못한 경우 본사 URL 사용 (fallback)
    if not webhook_url:
        webhook_url = config('SLACK_COMPANY_URL', default=None)
        if not webhook_url:
            print("대량 가져오기 Slack 알림 - 웹훅 URL을 찾을 수 없음")
            return False

    # 메시지 구성
    model_name = summary_data.get('model_name', 'Unknown')
    total_records = summary_data.get('total_records', 0)
    new_records = summary_data.get('new_records', 0)
    updated_records = summary_data.get('updated_records', 0)
    skipped_records = summary_data.get('skipped_records', 0)
    error_count = summary_data.get('error_count', 0)

    user_name = user.username if user else "시스템"

    # 성공/실패 이모지 설정
    status_emoji = "✅" if error_count == 0 else "⚠️"

    message = {
        "text": f"{status_emoji} {model_name} Excel 대량 가져오기 완료",
        "attachments": [
            {
                "color": "good" if error_count == 0 else "warning",
                "fields": [
                    {"title": "담당자", "value": user_name, "short": True},
                    {"title": "모델", "value": model_name, "short": True},
                    {"title": "전체 처리", "value": f"{total_records}건", "short": True},
                    {"title": "신규 생성", "value": f"{new_records}건", "short": True},
                    {"title": "업데이트", "value": f"{updated_records}건", "short": True},
                    {"title": "건너뜀", "value": f"{skipped_records}건", "short": True},
                    {"title": "오류", "value": f"{error_count}건", "short": True}
                ],
                "footer": SYSTEM_NAME,
                "ts": int(__import__('time').time())
            }
        ]
    }

    # Slack으로 메시지 전송
    try:
        print(f"[BULK_IMPORT] Slack 메시지 전송 시도: {model_name} {total_records}건")

        response = requests.post(webhook_url, json=message, timeout=10)
        response.raise_for_status()
        print(f"대량 가져오기 Slack 알림 전송 성공: {model_name} {total_records}건 처리 완료")
        return True
    except requests.RequestException as e:
        print(f"대량 가져오기 Slack 알림 전송 실패: {e}")
        return False


def get_slack_webhook_url(issue_project):
    """IssueProject의 sort와 slug를 기반으로 환경변수에서 웹훅 URL 조회"""
    if issue_project.sort == '1':  # 본사관리
        key = 'SLACK_COMPANY_URL'
    else:  # 개별 프로젝트
        # slug에 하이픈(-)이 있으면 언더스코어로 변환 (환경변수 키 규칙)
        key = f"SLACK_PROJECT_{issue_project.slug.replace('-', '_').upper()}"

    webhook_url = config(key, default=None)
    if webhook_url:
        print(f"Slack 웹훅 URL 조회 성공: {key}")
    else:
        print(f"Slack 웹훅 URL 조회 실패 - 환경변수 '{key}'가 설정되지 않음")

    return webhook_url


def get_contract_page_number(contract_instance):
    """Contract 인스턴스가 위치한 페이지 번호 계산 (프로젝트별 필터링 기준)"""
    try:
        # 프론트엔드에서 항상 프로젝트별로 필터링하므로 같은 프로젝트 내에서만 계산
        queryset = Contract.objects.filter(project=contract_instance.project).order_by('-created')

        # 해당 인스턴스보다 앞에 있는 항목 개수 계산 (같은 프로젝트 내에서)
        items_before = queryset.filter(created__gt=contract_instance.created).count()

        # 프론트엔드에서 사용하는 페이지 크기 (기본값 10)
        page_size = 10
        page_number = (items_before // page_size) + 1

        return page_number
    except Exception as e:
        print(f"Contract 페이지 계산 오류: {e}")
        return 1  # 오류 시 첫 페이지로


def get_site_page_number(site_instance):
    """Site 인스턴스가 위치한 페이지 번호 계산 (프로젝트별 필터링 기준)"""
    try:
        # 프론트엔드에서 항상 프로젝트별로 필터링하므로 같은 프로젝트 내에서만 계산
        # Site 모델의 기본 정렬 순서: ('-project', 'order', 'lot_number')
        # 프로젝트별 필터링 후에는 ('order', 'lot_number') 순으로 정렬됨
        queryset = Site.objects.filter(project=site_instance.project).order_by('order', 'lot_number')

        # 해당 인스턴스의 위치를 찾기 위해 전체 목록에서 인덱스 확인
        site_list = list(queryset.values_list('pk', flat=True))
        try:
            site_index = site_list.index(site_instance.pk)
        except ValueError:
            # 해당 Site가 목록에 없으면 첫 페이지
            return 1

        # 프론트엔드에서 사용하는 페이지 크기 (기본값 10)
        page_size = 10
        page_number = (site_index // page_size) + 1

        return page_number
    except Exception as e:
        print(f"Site 페이지 계산 오류: {e}")
        return 1  # 오류 시 첫 페이지로


def get_succession_page_number(succession_instance):
    """Succession 인스턴스가 위치한 페이지 번호 계산 (프로젝트별 전체 목록 기준)"""
    try:
        # 프로젝트별 전체 Succession 목록에서 계산
        project_id = succession_instance.contract.project.id
        queryset = Succession.objects.filter(contract__project_id=project_id)

        # Succession 모델의 정확한 ordering: ['-apply_date', '-trading_date', '-id']
        # 해당 인스턴스보다 앞에 있는 항목 개수 계산
        items_before = queryset.filter(
            Q(apply_date__gt=succession_instance.apply_date) |
            Q(apply_date=succession_instance.apply_date, trading_date__gt=succession_instance.trading_date) |
            Q(apply_date=succession_instance.apply_date, trading_date=succession_instance.trading_date,
              id__gt=succession_instance.id)
        ).count()

        # 프론트엔드에서 사용하는 페이지 크기 (기본값 10)
        page_size = 10
        page_number = (items_before // page_size) + 1

        return page_number
    except Exception as e:
        print(f"Succession 페이지 계산 오류: {e}")
        return 1  # 오류 시 첫 페이지로


def get_contractor_release_page_number(contractor_release_instance):
    """ContractorRelease 인스턴스가 위치한 페이지 번호 계산 (프로젝트별 전체 목록 기준)"""
    try:
        # 프로젝트별 전체 ContractorRelease 목록에서 계산
        project_id = contractor_release_instance.project.id
        queryset = ContractorRelease.objects.filter(project_id=project_id)

        # ContractorRelease 모델의 정확한 ordering: ['-request_date', '-created']
        # 해당 인스턴스보다 앞에 있는 항목 개수 계산
        items_before = queryset.filter(
            Q(request_date__gt=contractor_release_instance.request_date) |
            Q(request_date=contractor_release_instance.request_date,
              created__gt=contractor_release_instance.created)
        ).count()

        # 프론트엔드에서 사용하는 페이지 크기 (기본값 10)
        page_size = 10
        page_number = (items_before // page_size) + 1

        return page_number
    except Exception as e:
        print(f"ContractorRelease 페이지 계산 오류: {e}")
        return 1  # 오류 시 첫 페이지로


def get_site_owner_page_number(site_owner_instance):
    """SiteOwner 인스턴스가 위치한 페이지 번호 계산 (프로젝트별 필터링 기준)"""
    try:
        # SiteOwner 모델의 기본 정렬이 -id 순(최신순)이므로 해당 순서로 정렬
        queryset = SiteOwner.objects.filter(project=site_owner_instance.project).order_by('-id')

        # 해당 인스턴스보다 앞에 있는 항목 개수 계산 (-id 순이므로 id가 더 큰 항목들)
        items_before = queryset.filter(id__gt=site_owner_instance.id).count()

        # 프론트엔드에서 사용하는 페이지 크기 (기본값 10개)
        page_size = 10
        page_number = (items_before // page_size) + 1

        return page_number
    except Exception as e:
        print(f"SiteOwner 페이지 계산 오류: {e}")
        return 1  # 오류 시 첫 페이지로


def get_site_contract_page_number(site_contract_instance):
    """SiteContract 인스턴스가 위치한 페이지 번호 계산 (프로젝트별 필터링 기준)"""
    try:
        # SiteContract 모델의 기본 정렬이 -id 순(최신순)이므로 해당 순서로 정렬
        queryset = SiteContract.objects.filter(project=site_contract_instance.project).order_by('-id')

        # 해당 인스턴스보다 앞에 있는 항목 개수 계산 (-id 순이므로 id가 더 큰 항목들)
        items_before = queryset.filter(id__gt=site_contract_instance.id).count()

        # 프론트엔드에서 사용하는 페이지 크기 (기본값 10개)
        page_size = 10
        page_number = (items_before // page_size) + 1

        return page_number
    except Exception as e:
        print(f"SiteContract 페이지 계산 오류: {e}")
        return 1  # 오류 시 첫 페이지로


def get_service_url(model_instance):
    """모델 인스턴스에 대한 서비스 URL 등록"""
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
        return f"{base_url}/#/cashes/index?highlight_id={model_instance.id}&company={model_instance.company_id}"
    elif isinstance(model_instance, ProjectCashBook):
        return f"{base_url}/#/project-cash/index?highlight_id={model_instance.id}&project={model_instance.project_id}"
    elif isinstance(model_instance, CompanyBankTransaction):
        return f"{base_url}/#/ledger/index?highlight_id={model_instance.id}&company={model_instance.company_id}"
    elif isinstance(model_instance, ProjectBankTransaction):
        return f"{base_url}/#/project-ledger/index?highlight_id={model_instance.id}&project={model_instance.project_id}"
    elif isinstance(model_instance, LawsuitCase):
        return f"{base_url}/#/{prefix}docs/lawsuit/case/{model_instance.id}?company={model_instance.issue_project.company_id}"
    elif isinstance(model_instance, Document):
        sort_docs = 'lawsuit' if model_instance.lawsuit else 'general'
        return f"{base_url}/#/{prefix}docs/{sort_docs}/docs/{model_instance.id}?company={model_instance.issue_project.company_id}"
    elif isinstance(model_instance, Contract):
        # Contract 인스턴스가 위치한 페이지 번호 계산
        page_number = get_contract_page_number(model_instance)

        # 페이지 정보와 프로젝트 정보를 포함한 URL 생성
        url = f"{base_url}/#/contracts/index?page={page_number}&highlight_id={model_instance.id}&project={model_instance.project_id}"
        return url
    elif isinstance(model_instance, Succession):
        # Succession 인스턴스가 위치한 페이지 번호 계산
        page_number = get_succession_page_number(model_instance)

        # 페이지 정보와 project, contractor, 하이라이트 정보를 포함한 URL 생성
        url = f"{base_url}/#/contracts/succession?page={page_number}&highlight_id={model_instance.id}&contractor={model_instance.contract.contractor.id}&project={model_instance.contract.project.id}"
        return url
    elif isinstance(model_instance, ContractorRelease):
        # ContractorRelease 인스턴스가 위치한 페이지 번호 계산
        page_number = get_contractor_release_page_number(model_instance)

        # 시그널에서 캐시된 데이터가 잘못될 수 있으므로 fresh lookup 수행
        try:
            fresh_instance = ContractorRelease.objects.select_related('project').get(id=model_instance.id)
            project_id = fresh_instance.project.id
        except ContractorRelease.DoesNotExist:
            # 인스턴스가 삭제된 경우 등 fallback
            project_id = model_instance.project.id

        # 페이지 정보와 project, 하이라이트 정보를 포함한 URL 생성
        url = f"{base_url}/#/contracts/release?page={page_number}&highlight_id={model_instance.id}&project={project_id}"
        return url
    elif isinstance(model_instance, Site):
        # Site 인스턴스가 위치한 페이지 번호 계산
        page_number = get_site_page_number(model_instance)
        # 페이지 정보와 프로젝트 정보를 포함한 URL 생성
        url = f"{base_url}/#/project/site/index?page={page_number}&highlight_id={model_instance.id}&project={model_instance.project_id}"
        return url
    elif isinstance(model_instance, SiteOwner):
        # SiteOwner 인스턴스가 위치한 페이지 번호 계산
        page_number = get_site_owner_page_number(model_instance)
        # 페이지 정보와 프로젝트 정보를 포함한 URL 생성
        return f"{base_url}/#/project/site/owner?page={page_number}&highlight_id={model_instance.id}&project={model_instance.project_id}"
    elif isinstance(model_instance, SiteContract):
        # SiteContract 인스턴스가 위치한 페이지 번호 계산
        page_number = get_site_contract_page_number(model_instance)
        # 페이지 정보와 프로젝트 정보를 포함한 URL 생성
        return f"{base_url}/#/project/site/contract?page={page_number}&highlight_id={model_instance.id}&project={model_instance.project_id}"

    return base_url


def get_target_issue_project(model_instance):
    """모델 인스턴스에서 대상 IssueProject 추출"""

    if hasattr(model_instance, 'company'):  # CashBook
        # Company의 본사관리 IssueProject 찾기
        return IssueProject.objects.filter(
            company=model_instance.company,
            sort='1',  # 본사관리
            slack_notifications_enabled=True
        ).first()

    elif hasattr(model_instance, 'project'):  # ProjectCashBook, Contract 등
        # Project의 연결된 IssueProject
        project = model_instance.project
        if hasattr(project, 'issue_project'):
            issue_project = project.issue_project
            if issue_project.slack_notifications_enabled:
                return issue_project

    elif hasattr(model_instance, 'contract') and hasattr(model_instance.contract,
                                                         'project'):  # Succession, ContractorRelease 등
        # Contract를 통한 Project 접근
        project = model_instance.contract.project
        if hasattr(project, 'issue_project'):
            issue_project = project.issue_project
            if issue_project.slack_notifications_enabled:
                return issue_project

    elif hasattr(model_instance, 'issue_project'):  # LawsuitCase, Document 등
        # 직접 IssueProject와 연결된 모델
        issue_project = model_instance.issue_project
        if issue_project.slack_notifications_enabled:
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


def get_site_owners_info(site_instance):
    """Site의 소유자 정보를 포맷팅하여 반환"""
    try:
        owners = site_instance.owners.all()
        owner_count = owners.count()

        if owner_count == 0:
            return ""
        elif owner_count == 1:
            return f" ({owners.first().owner})"
        else:
            first_owner = owners.first().owner
            return f" ({first_owner} 외{owner_count - 1})"
    except Exception as e:
        print(f"Site 소유자 정보 조회 오류: {e}")
        return ""


class SlackMessageBuilder:
    """Slack 메시지 포맷팅 클래스"""

    @staticmethod
    def build_bank_transaction_message(instance, action, user):
        """bank_transaction 또는 Project_bank_transaction 간소화된 메시지 등록"""
        service_url = get_service_url(instance)
        sort_name = instance.sort.name
        amount = instance.amount
        main_content = f'[{sort_name}][{amount:,}]'

        if isinstance(instance, CompanyBankTransaction):
            # 본사 입출금
            com_name = instance.company.name
            title = f"💵 [{com_name}]-{main_content} - {instance.content or '------'}"
        elif isinstance(instance, ProjectBankTransaction):
            # 프로젝트 입출금
            proj_name = instance.project.name
            title = f"🏗️ [{proj_name}]-{main_content} - {instance.content or '------'}"
        else:
            return None

        color = 'good' if action == '등록' else '#ff9500' if action == '편집' else 'danger'
        # 거래일 정보 포맷팅 (YYYY-MM-DD -> MM/DD 형식으로 변환)
        deal_date_str = instance.deal_date.strftime('%Y-%m-%d') if instance.deal_date else '미정'

        # 편집 시 updator와 creator 정보 표시
        if action == '편집' and hasattr(instance, 'updator') and instance.updator:
            user_text = f"편집자: {instance.updator.username}"
            if hasattr(instance, 'creator') and instance.creator:
                user_text += f" (등록자: {instance.creator.username})"
        else:
            # 등록 시나 updator가 없는 경우 기존 방식
            user_text = f"등록자: {user.username if user else '시스템'}"
        user_text = f"""거래일: {deal_date_str} {user_text}"""

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
                'ts': int(instance.updated_at.timestamp())
            }]
        }

    @staticmethod
    def build_cashbook_message(instance, action, user):
        """CashBook 또는 ProjectCashBook 간소화된 메시지 등록"""
        service_url = get_service_url(instance)
        income = instance.income
        outlay = instance.outlay
        main_content = f'[입금][{income:,}]' if income else f'[출금][{outlay:,}]'

        if isinstance(instance, CashBook):
            # 본사 입출금
            sort_name = instance.company.name
            title = f"💵 [{sort_name}]-{main_content} - {instance.content or '------'}"
        elif isinstance(instance, ProjectCashBook):
            # 프로젝트 입출금
            sort_name = instance.project.issue_project.name
            title = f"🏗️ [{sort_name}]-{main_content} - {instance.content or '------'}"
        else:
            return None

        color = 'good' if action == '등록' else '#ff9500' if action == '편집' else 'danger'
        # 거래일 정보 포맷팅 (YYYY-MM-DD -> MM/DD 형식으로 변환)
        deal_date_str = instance.deal_date.strftime('%Y-%m-%d') if instance.deal_date else '미정'

        # 편집 시 updator와 creator 정보 표시
        if action == '편집' and hasattr(instance, 'updator') and instance.updator:
            user_text = f"편집자: {instance.updator.username}"
            if hasattr(instance, 'creator') and instance.creator:
                user_text += f" (등록자: {instance.creator.username})"
        else:
            # 등록 시나 updator가 없는 경우 기존 방식
            user_text = f"등록자: {user.username if user else '시스템'}"
        user_text = f"""거래일: {deal_date_str} {user_text}"""

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
    def build_lawsuitcase_message(instance, action, user):
        """LawsuitCase 간소화된 메시지 등록"""
        service_url = get_service_url(instance)
        color = 'good' if action == '등록' else '#ff9500' if action == '편집' else 'danger'

        # 간소화된 제목: 법원 + 사건번호 + 사건명
        agency = instance.get_court_display() if instance.get_court_display() else instance.other_agency
        title = f"⚖️ {instance.issue_project.name}-[소송사건]-|{agency}| {instance.case_number} - {instance.case_name}"

        # 편집 시 updator와 creator 정보 표시
        if action == '편집' and hasattr(instance, 'updator') and instance.updator:
            user_text = f"편집자: {instance.updator.username}"
            if hasattr(instance, 'creator') and instance.creator:
                user_text += f" (등록자: {instance.creator.username})"
        else:
            # 등록 시나 updator가 없는 경우 기존 방식
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
        """Document 간소화된 메시지 등록"""
        service_url = get_service_url(instance)
        color = 'good' if action == '등록' else '#ff9500' if action == '편집' else 'danger'

        # 간소화된 제목: 문서유형 + 제목 + 보안표시
        doc_type = instance.doc_type.get_type_display()
        title = f"📄 {instance.issue_project.name}-[{doc_type}]-{instance.title}"

        # 보안 문서 표시
        if instance.is_secret:
            title = f"🔒 {title}"

        # 편집 시 updator와 creator 정보 표시
        if action == '편집' and hasattr(instance, 'updator') and instance.updator:
            user_text = f"편집자: {instance.updator.username}"
            if hasattr(instance, 'creator') and instance.creator:
                user_text += f" (등록자: {instance.creator.username})"
        else:
            # 등록 시나 updator가 없는 경우 기존 방식
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
        """Contract 간소화된 메시지 등록"""
        service_url = get_service_url(instance)
        color = 'good' if action == '등록' else '#ff9500' if action == '편집' else 'danger'

        # 간소화된 제목: 프로젝트명 + 계약번호
        title = f"📋 [PR-계약]-[{instance.project.name}] {instance.serial_number}"
        # sup_cont_date 안전하게 처리 (문자열/날짜 객체 모두 지원)
        if instance.sup_cont_date:
            if hasattr(instance.sup_cont_date, 'strftime'):
                # 날짜 객체인 경우
                cont_date_str = instance.sup_cont_date.strftime('%Y-%m-%d')
            else:
                # 문자열인 경우 그대로 사용
                cont_date_str = str(instance.sup_cont_date)
        else:
            cont_date_str = '미정'

        # 편집 시 updator와 creator 정보 표시
        if action == '편집' and hasattr(instance, 'updator') and instance.updator:
            user_text = f"편집자: {instance.updator.username}"
            if hasattr(instance, 'creator') and instance.creator:
                user_text += f" (등록자: {instance.creator.username})"
        else:
            # 등록 시나 updator가 없는 경우 기존 방식
            user_text = f"등록자: {user.username if user else '시스템'}"
        user_text = f"""계약일: {cont_date_str}
{user_text}"""

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
    def build_succession_message(instance, action, user):
        """Succession 간소화된 메시지 등록"""
        service_url = get_service_url(instance)
        color = 'good' if action == '등록' else '#ff9500' if action == '편집' else 'danger'

        # 간소화된 제목: 프로젝트명 + 양도승계 + 양도자→양수자
        title = f"🖇️ [PR-계약승계]-[{instance.contract.project.name}] :: {instance.seller.name} → {instance.buyer.name}"
        apply_date_str = instance.apply_date.strftime('%Y-%m-%d') if instance.apply_date else '미정'

        # 편집 시 updator와 creator 정보 표시
        if action == '편집' and hasattr(instance, 'updator') and instance.updator:
            user_text = f"편집자: {instance.updator.username}"
            if hasattr(instance, 'creator') and instance.creator:
                user_text += f" (등록자: {instance.creator.username})"
        else:
            # 등록 시나 updator가 없는 경우 기존 방식
            user_text = f"등록자: {user.username if user else '시스템'}"
        user_text = f"""신청일: {apply_date_str}
{user_text}"""

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
    def build_contractor_release_message(instance, action, user):
        """ContractorRelease 간소화된 메시지 등록"""
        service_url = get_service_url(instance)
        color = 'good' if action == '등록' else '#ff9500' if action == '편집' else 'danger'

        # 간소화된 제목: 프로젝트명 + 해지 + 계약자명
        status_display = instance.get_status_display()
        title = f"✖️ [PR-계약해지]-[{instance.project.name}] {status_display} - {instance.contractor.name}"
        request_date_str = instance.request_date.strftime('%Y-%m-%d') if instance.request_date else '미정'

        # 편집 시 updator와 creator 정보 표시
        if action == '편집' and hasattr(instance, 'updator') and instance.updator:
            user_text = f"편집자: {instance.updator.username}"
            if hasattr(instance, 'creator') and instance.creator:
                user_text += f" (등록자: {instance.creator.username})"
        else:
            # 등록 시나 updator가 없는 경우 기존 방식
            user_text = f"등록자: {user.username if user else '시스템'}"
        user_text = f"""신청일: {request_date_str}
{user_text}"""

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
    def build_site_message(instance, action, user):
        """Site 간소화된 메시지 등록"""
        service_url = get_service_url(instance)
        color = 'good' if action == '등록' else '#ff9500' if action == '편집' else 'danger'

        # 소유자 정보 조회
        owners_info = get_site_owners_info(instance)

        # 간소화된 제목: 프로젝트명 + 사업부지 + 지번주소 + 소유자 정보
        title = f"🏗️ [{instance.project.issue_project.name}]-[사업부지] - {instance.district} {instance.lot_number}{owners_info}"

        # 편집 시 updator와 creator 정보 표시
        if action == '편집' and hasattr(instance, 'updator') and instance.updator:
            user_text = f"편집자: {instance.updator.username}"
            if hasattr(instance, 'creator') and instance.creator:
                user_text += f" (등록자: {instance.creator.username})"
        else:
            # 등록 시나 updator가 없는 경우 기존 방식
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
    def build_site_owner_message(instance, action, user):
        """SiteOwner 간소화된 메시지 등록"""
        service_url = get_service_url(instance)
        color = 'good' if action == '등록' else '#ff9500' if action == '편집' else 'danger'

        # 간소화된 제목: 프로젝트명 + 토지소유자 + 소유자명
        title = f"👤 [{instance.project.issue_project.name}]-[토지-소유자] - {instance.owner}"

        # 편집 시 updator와 creator 정보 표시
        if action == '편집' and hasattr(instance, 'updator') and instance.updator:
            user_text = f"편집자: {instance.updator.username}"
            if hasattr(instance, 'creator') and instance.creator:
                user_text += f" (등록자: {instance.creator.username})"
        else:
            # 등록 시나 updator가 없는 경우 기존 방식
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
    def build_site_contract_message(instance, action, user):
        """SiteContract 간소화된 메시지 등록"""
        service_url = get_service_url(instance)
        color = 'good' if action == '등록' else '#ff9500' if action == '편집' else 'danger'

        # 간소화된 제목: 프로젝트명 + 토지계약 + 소유자명 + 매매대금
        price_display = intcomma(instance.total_price) if instance.total_price else '미정'
        title = f"📋 [{instance.project.issue_project.name}]-[토지-계약] - {instance.owner.owner} - [{price_display}원]"
        contract_date_str = instance.contract_date.strftime('%Y-%m-%d') if instance.contract_date else '미정'

        # 편집 시 updator와 creator 정보 표시
        if action == '편집' and hasattr(instance, 'updator') and instance.updator:
            user_text = f"편집자: {instance.updator.username}"
            if hasattr(instance, 'creator') and instance.creator:
                user_text += f" (등록자: {instance.creator.username})"
        else:
            # 등록 시나 updator가 없는 경우 기존 방식
            user_text = f"등록자: {user.username if user else '시스템'}"
        user_text = f"""계약일: {contract_date_str}
{user_text}"""

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
            print(f"Slack 메시지 전송 성공: {webhook_url}")
            return True
        else:
            print(f"Slack 메시지 전송 실패 ({response.status_code}): {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"Slack 메시지 전송 중 오류: {str(e)}")
        return False


def send_slack_notification(instance, action, user=None):
    """통합 Slack 알림 전송 함수"""

    # Slack 알림이 비활성화된 경우 종료
    if not getattr(settings, 'SLACK_NOTIFICATIONS_ENABLED', True):
        return

    # 대상 IssueProject 찾기
    issue_project = get_target_issue_project(instance)
    if not issue_project:
        print(f"Slack 알림 대상 프로젝트를 찾을 수 없음: {instance}")
        return

    # 메시지 등록
    message_data = None
    if isinstance(instance, (CashBook, ProjectCashBook)):
        message_data = SlackMessageBuilder.build_cashbook_message(instance, action, user)
    elif isinstance(instance, (CompanyBankTransaction, ProjectBankTransaction)):
        message_data = SlackMessageBuilder.build_bank_transaction_message(instance, action, user)
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
    elif isinstance(instance, Site):
        message_data = SlackMessageBuilder.build_site_message(instance, action, user)
    elif isinstance(instance, SiteOwner):
        message_data = SlackMessageBuilder.build_site_owner_message(instance, action, user)
    elif isinstance(instance, SiteContract):
        message_data = SlackMessageBuilder.build_site_contract_message(instance, action, user)

    if not message_data:
        print(f"지원하지 않는 모델 타입: {type(instance)}")
        return

    # 환경변수에서 Slack 웹훅 URL 조회
    slack_webhook_url = get_slack_webhook_url(issue_project)
    if not slack_webhook_url:
        print(f"Slack 웹훅 URL을 찾을 수 없음: {issue_project.name} (slug: {issue_project.slug})")
        return

    # Slack 메시지 전송
    success = send_slack_message(slack_webhook_url, message_data)

    if success:
        # 권한 있는 멤버들 로그 (선택적)
        members = get_authorized_members(issue_project)
        member_names = [member.user.username for member in members if member.user]
        print(f"Slack 알림 전송 완료 - 프로젝트: {issue_project.name}, 멤버: {', '.join(member_names)}")
