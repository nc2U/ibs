"""
공문 PDF 생성 유틸리티
"""
import io

from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from weasyprint import HTML

from company.models import Logo


def get_letter_approval_line(letter):
    """
    공문과 연동된 ApprovalDocument로부터 렌더링용 결재선 정보 추출
    반환 구조:
    {
        'items': [
            {'display_title': '담당', 'name': '홍길동'},
            {'display_title': '팀장', 'name': '김팀장'},
            {'display_title': '본부장', 'name': '이본부'},
        ],
        'final_date': '2026. 09. 08.', # 최종 전결/승인 일자
    }
    """
    approval_doc = letter.approval_document
    if not approval_doc:
        # 전자결재 연동이 없는 경우: 공문의 작성자(creator)를 담당으로 표기
        name = ''
        title = letter.sender_position or '담당'
        if letter.creator:
            staff = getattr(letter.creator, 'staff', None)
            name = staff.name if staff else (letter.creator.username or '')
            if staff:
                primary = staff.primary_assignment
                pos_duty = primary.duty.name if (primary and primary.duty) else (staff.position.name if staff.position else '')
                if pos_duty:
                    title = pos_duty
        if not name:
            name = letter.sender_name or ''

        final_date = letter.issue_date.strftime('%Y. %m. %d.') if letter.issue_date else ''
        return {
            'drafter': {'display_title': title or '담당', 'name': name},
            'middle_steps': [],
            'final_approver': {'display_title': '대표', 'name': letter.company.ceo if letter.company and letter.company.ceo else name},
            'final_date': final_date,
        }

    items = []
    final_date = ''

    def _get_staff_title(user, assignment=None, default='담당'):
        staff = getattr(user, 'staff', None) if user else None
        if not staff:
            return default
        # 1. 대표이사/임원 직위 우선 확인
        if hasattr(staff, 'executive') and staff.executive and staff.executive.rank:
            return staff.executive.rank.name
        # 2. 보직의 직책(duty) 확인
        if assignment and assignment.duty:
            return assignment.duty.name
        primary = staff.primary_assignment
        if primary and primary.duty:
            return primary.duty.name
        # 3. 직위(position) 확인
        if staff.position:
            return staff.position.name
        return default

    # 1. 기안자 (담당/기안)
    drafter = approval_doc.drafter
    drafter_staff = getattr(drafter, 'staff', None) if drafter else None
    drafter_title = _get_staff_title(drafter, approval_doc.drafter_assignment, default='담당')
    # 기안자가 대표이사인 경우에도 기안란에는 '기안' 또는 '담당'으로 명확히 구분
    drafter_role_label = '기안' if drafter_title in ['대표이사', '대표', '사내이사'] else drafter_title

    drafter_info = {
        'display_title': drafter_role_label,
        'name': drafter_staff.name if drafter_staff else (drafter.username if drafter else ''),
    }

    # 2. 결재 단계 순회
    steps = approval_doc.steps.all().order_by('step_order').prefetch_related('approvers', 'actions__approver')
    total_steps = len(steps)

    middle_steps = []
    final_approver_info = None

    for idx, step in enumerate(steps):
        is_final = (idx == total_steps - 1)

        # 승인된 액션 확인
        approved_action = None
        for action in step.actions.all():
            if action.action == 'approved':
                approved_action = action
                break

        approver_obj = approved_action.approver if approved_action else step.approvers.first()
        staff = getattr(approver_obj, 'staff', None) if approver_obj else None
        name = staff.name if staff else (approver_obj.username if approver_obj else '')

        step_title = _get_staff_title(approver_obj, default='')
        if not step_title:
            step_title = step.role_label or ('대표' if is_final else '검토')

        step_data = {
            'display_title': step_title,
            'name': name,
        }

        if is_final:
            final_approver_info = step_data
            if approved_action and approved_action.acted_at:
                final_date = approved_action.acted_at.strftime('%Y. %m. %d.')
        else:
            middle_steps.append(step_data)

    # 만약 결재 step이 전혀 없는 단독 문서인 경우 drafter를 final_approver로도 설정
    if not final_approver_info:
        final_title = _get_staff_title(drafter, default='대표')
        final_approver_info = {
            'display_title': final_title,
            'name': drafter_info['name'],
        }

    if not final_date:
        if approval_doc.completed_at:
            final_date = approval_doc.completed_at.strftime('%Y. %m. %d.')
        elif letter.issue_date:
            final_date = letter.issue_date.strftime('%Y. %m. %d.')

    return {
        'drafter': drafter_info,
        'middle_steps': middle_steps,
        'final_approver': final_approver_info,
        'final_date': final_date,
    }


def generate_official_letter_pdf(letter):
    """
    공문 PDF 생성

    Args:
        letter: OfficialLetter 인스턴스

    Returns:
        ContentFile: 생성된 PDF 파일
    """
    # 회사 로고 URL 가져오기
    logo_url = None
    try:
        logo = Logo.objects.get(company=letter.company)
        if logo.generic_logo:
            logo_url = logo.generic_logo.url
    except Logo.DoesNotExist:
        pass

    # 날인 인감 이미지 URL 가져오기
    seal_url = None
    if letter.seal and letter.seal.seal_image:
        try:
            seal_url = letter.seal.seal_image.url
        except Exception:
            pass

    # 결재선 추출
    approval_line = get_letter_approval_line(letter)

    # 템플릿 컨텍스트 준비
    context = {
        'letter': letter,
        'company': letter.company,
        'logo_url': logo_url,
        'seal_url': seal_url,
        'approval_line': approval_line,
    }

    # HTML 템플릿 렌더링
    html_string = render_to_string('pdf/official_letter.html', context)

    # PDF 생성
    html = HTML(string=html_string, base_url='/')
    pdf_buffer = io.BytesIO()
    html.write_pdf(target=pdf_buffer)

    # ContentFile 생성
    pdf_buffer.seek(0)
    filename = letter.get_pdf_filename()

    return ContentFile(pdf_buffer.read(), name=filename)
