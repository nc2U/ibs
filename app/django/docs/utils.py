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
    # 회사의 공식 장부(Executive/Staff)로부터 단독 대표이사 성명 추출
    representative_name = (
        letter.company.get_representative_staff_name()
        if (letter.company and hasattr(letter.company, 'get_representative_staff_name'))
        else ''
    )
    # 대표이사 직함이나 공백 제거 후 순수 성명 비교용
    raw_drafter_name = letter.drafter_name or ''
    clean_drafter_name = (
        raw_drafter_name.replace('대표이사', '')
        .replace('대표', '')
        .replace('사장', '')
        .strip()
    )

    if not approval_doc:
        # 전자결재 연동이 없는 수동 발송의 경우
        # 발송 완료일시가 있으면 발송일(시행), 없으면 발신 요청일(승인)
        if letter.dispatched_at:
            final_date = letter.dispatched_at.strftime('%Y. %m. %d.')
            date_label = '시행'
        elif letter.issue_date:
            final_date = letter.issue_date.strftime('%Y. %m. %d.')
            date_label = '승인'
        else:
            final_date = ''
            date_label = '승인'

        final_title = '대표이사'
        if letter.seal and letter.seal.final_approval_duty:
            final_title = letter.seal.final_approval_duty.name

        date_label = '시행' if letter.dispatched_at else ('전결' if final_title in ['현장소장', '소장', '본부장', '팀장'] else '승인')

        # 승인권자 직무(전결직책)에 따른 최종 결재권자 성명 결정:
        # 1) 대표이사 결재인 경우: 회사 대표이사 성명 우선
        # 2) 현장소장/본부장 등 전결인 경우: 전결권자 직접 기안 시 기안자 성명이 곧 최종 결재권자 성명
        if final_title in ['현장소장', '소장', '본부장', '팀장']:
            final_person_name = clean_drafter_name or raw_drafter_name
        else:
            final_person_name = representative_name or clean_drafter_name

        # 승인(전결)권자 직접 기안 단독 결재 판단:
        # 1순위: 모델의 is_solo_approval 명시적 플래그
        # 2순위: 성명 일치 여부 (폴백)
        if letter.is_solo_approval:
            is_solo = True
        else:
            is_solo = bool(
                clean_drafter_name
                and final_person_name
                and clean_drafter_name == final_person_name
            )

        return {
            'is_solo': is_solo,
            'drafter': None if is_solo else {'display_title': '담당', 'name': clean_drafter_name or raw_drafter_name},
            'middle_steps': [],
            'final_approver': {
                'display_title': final_title,
                'name': final_person_name,
            },
            'final_date': final_date,
            'date_label': date_label,
        }

    def _get_staff_duty_or_name(user, assignment=None, is_final=False):
        """
        결재 선상의 이름 및 직책 추출 원칙:
        - 이름: 무조건 회사의 공식 장부인 Staff 모델의 name(직원 성명) 사용
        - 직책: 임원인 경우 ExecutiveRank 직위명, 보직이 있는 경우 DutyTitle 직책명 사용
        """
        staff = getattr(user, 'staff', None) if user else None
        if not staff and user:
            # 혹시 역참조나 캐싱 문제 방지를 위해 Staff 모델 직접 조회
            from company.models import Staff
            staff = Staff.objects.filter(user=user).first()

        name = staff.name if staff else ''
        if not name and user:
            # Staff가 등록되지 않은 비정상 계정의 경우에만 최소한의 식별용 표시
            name = getattr(getattr(user, 'profile', None), 'name', '') or user.username

        # 1. 대표이사/임원 확인 (ExecutiveRank)
        if staff and hasattr(staff, 'executive') and staff.executive and staff.executive.rank:
            rank_name = staff.executive.rank.name
            return rank_name, name

        # 2. 보직의 직책(DutyTitle) 확인
        duty_obj = None
        if assignment and assignment.duty:
            duty_obj = assignment.duty
        elif staff and hasattr(staff, 'duty') and staff.duty:
            duty_obj = staff.duty

        if duty_obj and duty_obj.name:
            return duty_obj.name, name

        # 3. 직책이 없는 일반 팀원인 경우
        # 최종 결재권자인 경우는 직위라도 표기, 중간 단계인 경우는 직책 없으면 이름만
        if is_final and staff and staff.position:
            return staff.position.name, name

        return '', name

    # 1. 기안자 정보 (Staff 모델의 직원 성명 원칙)
    drafter = approval_doc.drafter
    drafter_staff = getattr(drafter, 'staff', None) if drafter else None
    if not drafter_staff and drafter:
        from company.models import Staff
        drafter_staff = Staff.objects.filter(user=drafter).first()

    drafter_name = drafter_staff.name if drafter_staff else (
        getattr(getattr(drafter, 'profile', None), 'name', '') or (drafter.username if drafter else '')
    )

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

    # 승인(전결)권자 직접 기안 1인 단독 결재 여부 확인
    if letter.is_solo_approval:
        is_solo = True
    else:
        is_solo = False
        clean_drafter_name = (
            drafter_name.replace('대표이사', '')
            .replace('대표', '')
            .replace('사장', '')
            .strip()
        )
        final_name = (final_approver_info.get('name') or '').strip()
        if len(middle_steps) == 0:
            if clean_drafter_name and final_name and clean_drafter_name == final_name:
                is_solo = True
            elif representative_name and clean_drafter_name == representative_name:
                is_solo = True

    date_label = '시행' if letter.dispatched_at else '승인'
    if not letter.dispatched_at and final_approver_info.get('display_title') in ['현장소장', '소장', '본부장', '팀장']:
        date_label = '전결'

    return {
        'is_solo': is_solo,
        'drafter': None if is_solo else {'display_title': '담당', 'name': drafter_name},
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

    # 공문 본문 마크다운 -> HTML 변환 (표, 줄바꿈 유지)
    import markdown2
    letter_content_html = ''
    if letter.content:
        letter_content_html = markdown2.markdown(
            letter.content,
            extras=['tables', 'break-on-newline', 'crlf']
        )

    # 템플릿 컨텍스트 준비
    context = {
        'letter': letter,
        'letter_content_html': letter_content_html,
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
