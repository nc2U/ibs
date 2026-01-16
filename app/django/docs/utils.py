"""
공문 PDF 생성 유틸리티
"""
import io
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from weasyprint import HTML
from company.models import Logo


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

    # 템플릿 컨텍스트 준비
    context = {
        'letter': letter,
        'company': letter.company,
        'logo_url': logo_url,
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
