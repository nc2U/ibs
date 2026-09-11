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
    공문과 연동된 ApprovalDocument 또는 수동 정보로부터 렌더링용 결재선 정보 추출
    표기 규칙:
    - 기안자: 무조건 '담당' [성명]
    - 중간단계: 직책(duty)이 있으면 '[직책] [성명]', 팀원이면 '[성명]'만 표기
    - 최종권자: 상단에 승인/전결/시행 일자 배치
    - 대표이사 단독 기안/결재 시: 기안란(담당)은 생략하고 최종권자(대표이사)만 단독 표기
    """
    approval_doc = letter.approval_document
    ceo_name = letter.company.ceo if (letter.company and letter.company.ceo) else ''

    if not approval_doc:
        # 전자결재 연동이 없는 수동 발송의 경우
        drafter_name = letter.drafter_name or ''
        final_date = letter.issue_date.strftime('%Y. %m. %d.') if letter.issue_date else ''
        final_title = '대표이사'

        # 대표이사가 직접 기안/발송한 경우: 기안란은 None으로 두어 단독 표기
        is_ceo_solo = bool(drafter_name and ceo_name and drafter_name.strip() == ceo_name.strip())

        return {
            'is_solo': is_ceo_solo,
            'drafter': None if is_ceo_solo else {'display_title': '담당', 'name': drafter_name},
            'middle_steps': [],
            'final_approver': {
                'display_title': final_title,
                'name': ceo_name or drafter_name,
            },
            'final_date': final_date,
            'date_label': '시행' if letter.dispatched_at else '승인',
        }

    def _get_staff_duty_or_name(user, assignment=None, is_final=False):
        staff = getattr(user, 'staff', None) if user else None
        name = staff.name if staff else (user.username if user else '')
        if not staff:
            return '', name

        # 1. 대표이사/임원 확인
        if hasattr(staff, 'executive') and staff.executive and staff.executive.rank:
            rank_name = staff.executive.rank.name
            return rank_name, name

        # 2. 보직의 직책(duty) 확인
        duty_obj = assignment.duty if (assignment and assignment.duty) else (staff.duty if hasattr(staff, 'duty') else None)
        if duty_obj:
            return duty_obj.name, name

        # 3. 직책이 없는 일반 팀원인 경우 직위(position)를 쓸지 혹은 생략할지
        # 최종 결재권자인 경우는 직위라도 표기, 중간 단계인 경우는 직책 없으면 이름만
        if is_final:
            pos_name = staff.position.name if staff.position else '전결'
            return pos_name, name
        return '', name

    # 1. 기안자 정보
    drafter = approval_doc.drafter
    drafter_staff = getattr(drafter, 'staff', None) if drafter else None
    drafter_name = drafter_staff.name if drafter_staff else (drafter.username if drafter else '')

    # 2. 결재 단계 순회
    steps = approval_doc.steps.all().order_by('step_order').prefetch_related('approvers', 'actions__approver')
    total_steps = len(steps)

    middle_steps = []
    final_approver_info = None
    final_date = ''

    for idx, step in enumerate(steps):
        is_final = (idx == total_steps - 1)

        approved_action = None
        for action in step.actions.all():
            if action.action == 'approved':
                approved_action = action
                break

        approver_obj = approved_action.approver if approved_action else step.approvers.first()
        duty_title, person_name = _get_staff_duty_or_name(approver_obj, is_final=is_final)

        if is_final:
            if not duty_title:
                duty_title = step.role_label or '대표이사'
            final_approver_info = {
                'display_title': duty_title,
                'name': person_name,
            }
            if approved_action and approved_action.acted_at:
                final_date = approved_action.acted_at.strftime('%Y. %m. %d.')
        else:
            # 중간 단계: 직책이 있으면 직책 표기, 팀원이면 이름만
            middle_steps.append({
                'display_title': duty_title, # 빈 문자열이면 템플릿에서 이름만 렌더링
                'name': person_name,
            })

    if not final_approver_info:
        duty_title, person_name = _get_staff_duty_or_name(drafter, is_final=True)
        final_approver_info = {
            'display_title': duty_title or '대표이사',
            'name': person_name,
        }

    if not final_date:
        if approval_doc.completed_at:
            final_date = approval_doc.completed_at.strftime('%Y. %m. %d.')
        elif letter.issue_date:
            final_date = letter.issue_date.strftime('%Y. %m. %d.')

    # 대표이사가 직접 기안하여 결재한 1인 결재 여부 확인
    is_ceo_solo = False
    if len(middle_steps) == 0:
        if drafter_name and final_approver_info['name'] and drafter_name.strip() == final_approver_info['name'].strip():
            is_ceo_solo = True
        elif ceo_name and drafter_name.strip() == ceo_name.strip():
            is_ceo_solo = True

    date_label = '승인'
    if final_approver_info.get('display_title') in ['현장소장', '소장', '본부장', '팀장']:
        date_label = '전결'

    return {
        'is_solo': is_ceo_solo,
        'drafter': None if is_ceo_solo else {'display_title': '담당', 'name': drafter_name},
        'middle_steps': middle_steps,
        'final_approver': final_approver_info,
        'final_date': final_date,
        'date_label': date_label,
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

    # 발신자 연락처 추출 (기안자 Staff 직통 연락처 우선, 미등록 시 회사 대표 연락처)
    drafter_user = letter.approval_document.drafter if letter.approval_document else letter.creator
    drafter_staff = getattr(drafter_user, 'staff', None) if drafter_user else None
    company = letter.company

    sender_contact = {
        'phone': (drafter_staff.direct_phone if drafter_staff and drafter_staff.direct_phone else getattr(company, 'phone', '')) or '',
        'fax': (drafter_staff.direct_fax if drafter_staff and drafter_staff.direct_fax else getattr(company, 'fax', '')) or '',
        'email': (drafter_staff.email if drafter_staff and drafter_staff.email else getattr(company, 'email', '')) or '',
    }

    # 템플릿 컨텍스트 준비
    context = {
        'letter': letter,
        'company': company,
        'logo_url': logo_url,
        'seal_url': seal_url,
        'approval_line': approval_line,
        'sender_contact': sender_contact,
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
