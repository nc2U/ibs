"""
PDF Export Common Mixins

공통 PDF 내보내기 기능을 제공하는 믹스인 클래스들
"""
import re
import tempfile
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from urllib.parse import quote, urlparse
from urllib.request import url2pathname

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.generic import View
from weasyprint import HTML
from weasyprint.urls import URLFetcher

from contract.models import Contract
from payment.models import InstallmentPaymentOrder

_base_fetcher = URLFetcher()


class PdfExportMixin(LoginRequiredMixin, View):
    """PDF 내보내기 공통 기능 믹스인 (세션 및 JWT 로그인 인증 지원, SSRF 방어)"""
    raise_exception = False

    def dispatch(self, request, *args, **kwargs):
        # 1. 미인증 사용자인 경우 토큰 기반 인증 시도 (Authorization 헤더, 쿠키, 쿼리 파라미터)
        if not request.user.is_authenticated:
            raw_token = None
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if auth_header.startswith('Bearer '):
                raw_token = auth_header.split(' ', 1)[1].strip()

            if not raw_token:
                raw_token = request.COOKIES.get('accessToken') or request.COOKIES.get('token')

            if not raw_token:
                raw_token = request.GET.get('token')

            if raw_token:
                from rest_framework_simplejwt.authentication import JWTAuthentication
                try:
                    jwt_auth = JWTAuthentication()
                    validated_token = jwt_auth.get_validated_token(raw_token)
                    request.user = jwt_auth.get_user(validated_token)
                    request.auth = validated_token
                except Exception:
                    pass

        # 2. 여전히 인증되지 않은 경우
        if not request.user.is_authenticated:
            # 토큰이 전송되었으나 유효하지 않은 경우 명시적 401 반환 (다운로드 시 HTML이 PDF로 저장되는 현상 방지)
            if (
                request.META.get('HTTP_AUTHORIZATION') or
                request.COOKIES.get('accessToken') or
                request.COOKIES.get('token') or
                request.GET.get('token') or
                request.headers.get('x-requested-with') == 'XMLHttpRequest' or
                'application/json' in request.META.get('HTTP_ACCEPT', '')
            ):
                return HttpResponse(
                    '유효하지 않거나 만료된 인증 토큰입니다. 다시 로그인해 주세요.',
                    status=401,
                    content_type='text/plain; charset=utf-8',
                )

        return super().dispatch(request, *args, **kwargs)

    @staticmethod
    def safe_url_fetcher(url, *args, **kwargs):
        """SSRF 및 LFI 방어를 위한 WeasyPrint URL Fetcher (내부 사설망, 메타데이터 및 비인가 로컬 파일 차단)"""
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()

        # data: URI 및 상대경로는 인라인 리소스/폰트용으로 허용
        if scheme in ('data', ''):
            return _base_fetcher(url, *args, **kwargs)

        # file: URI는 BASE_DIR, MEDIA_ROOT, STATIC_ROOT 또는 시스템 임시 디렉토리 내부 경로만 허용 (LFI 차단)
        if scheme == 'file':
            file_path = url2pathname(parsed.path)
            try:
                resolved = Path(file_path).resolve()
                base_dir = Path(settings.BASE_DIR).resolve()
                media_root = Path(settings.MEDIA_ROOT).resolve() if getattr(settings, 'MEDIA_ROOT', None) else None
                static_root = Path(settings.STATIC_ROOT).resolve() if getattr(settings, 'STATIC_ROOT', None) else None
                temp_dir = Path(tempfile.gettempdir()).resolve()

                resolved_str = str(resolved).lower()
                is_safe = (
                    resolved_str.startswith(str(base_dir).lower()) or
                    (media_root and resolved_str.startswith(str(media_root).lower())) or
                    (static_root and resolved_str.startswith(str(static_root).lower())) or
                    resolved_str.startswith(str(temp_dir).lower()) or
                    resolved_str.startswith('/tmp') or
                    resolved_str.startswith('/var/tmp')
                )
                if not is_safe:
                    raise ValueError(f"Access to file path {url} outside BASE_DIR is forbidden.")
            except (ValueError, OSError) as e:
                if isinstance(e, ValueError) and "forbidden" in str(e):
                    raise
                raise ValueError(f"Invalid file URL: {url}")
            return _base_fetcher(url, *args, **kwargs)

        if scheme in ('http', 'https'):
            hostname = (parsed.hostname or '').lower()
            # 내부망/메타데이터 IP, localhost 및 k8s 내부 도메인 차단
            blocked_hosts = ('localhost', '127.0.0.1', '::1', '169.254.169.254')
            if hostname in blocked_hosts or hostname.startswith('10.') or hostname.startswith('192.168.') \
                    or hostname.endswith('.cluster.local') or hostname.endswith('.svc'):
                raise ValueError(f"Access to internal network URL {url} is forbidden.")
            if hostname.startswith('172.'):
                parts = hostname.split('.')
                if len(parts) >= 2 and parts[1].isdigit() and 16 <= int(parts[1]) <= 31:
                    raise ValueError(f"Access to internal network URL {url} is forbidden.")

        return _base_fetcher(url, *args, **kwargs)

    @classmethod
    def create_pdf_response_from_string(cls, html_string, filename):
        """직접 생성된 HTML 문자열로부터 PDF 응답 생성 (메모리 버퍼 기반 및 SSRF 방어)"""
        html = HTML(string=html_string, base_url=str(settings.BASE_DIR), url_fetcher=cls.safe_url_fetcher)
        pdf_bytes = html.write_pdf()

        clean_filename = re.sub(r'["\r\n]', '', str(filename)).strip() or 'document'
        if not clean_filename.lower().endswith('.pdf'):
            clean_filename = f"{clean_filename}.pdf"

        encoded_filename = quote(clean_filename)

        # RFC 6266: ASCII fallback 파일명 생성 (헤더 깨짐 방지)
        ascii_name = clean_filename.encode('ascii', 'ignore').decode('ascii').strip()
        if not ascii_name or ascii_name == '.pdf':
            ascii_name = 'download.pdf'

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = (
            f'attachment; filename="{ascii_name}"; filename*=UTF-8\'\'{encoded_filename}'
        )
        return response

    @classmethod
    def create_pdf_response(cls, template_name, context, filename, request=None):
        """PDF 응답 생성 (메모리 버퍼 기반 생성 및 base_url/SSRF 방어 지원)"""
        html_string = render_to_string(template_name, context)
        return cls.create_pdf_response_from_string(html_string, filename)

    @staticmethod
    def get_base_context(**kwargs):
        """기본 컨텍스트 생성 (호출 시점의 현재 날짜 적용)"""
        context = {
            'pub_date': kwargs.get('pub_date', date.today()),
        }
        context.update(kwargs)
        return context


class ContractPdfMixin:
    """계약 관련 PDF 공통 기능"""

    @staticmethod
    def get_contract(cont_id):
        """계약 가져오기"""
        try:
            return Contract.objects.filter(pk=cont_id).first()
        except (ValueError, TypeError):
            return None

    @staticmethod
    def get_contract_unit(contract):
        """계약 동호수 정보 가져오기"""
        if not contract:
            return None
        try:
            return contract.key_unit.houseunit
        except AttributeError:
            return None

    @staticmethod
    def get_contract_content(contract, unit):
        """계약 내용 정보 구성"""
        if not contract:
            return {}

        contractor = getattr(contract, 'contractor', None)
        return {
            'contractor': contractor.name if contractor else '',
            'cont_date': contractor.contract_date if contractor else None,
            'cont_no': unit if unit else getattr(contract, 'serial_number', ''),
            'cont_type': getattr(contract, 'unit_type', None),
        }


class PaymentPdfMixin:
    """납부 관련 PDF 공통 기능"""

    @staticmethod
    def get_payment_orders(project):
        """납부 회차 정보 가져오기"""
        if not project:
            return InstallmentPaymentOrder.objects.none()
        return InstallmentPaymentOrder.objects.filter(project=project)

    @staticmethod
    def get_paid_list(contract, pub_date=None):
        """기 납부 목록 가져오기 (_pdf.utils.get_paid 래핑)"""
        from _pdf.utils import get_paid
        if not contract:
            return [], 0
        ref_date = pub_date or date.today()
        try:
            paid_dict_list, paid_sum_total, _ = get_paid(contract, [], ref_date)
            return paid_dict_list, paid_sum_total
        except Exception:
            return [], 0


class DateUtilMixin:
    """날짜 관련 유틸리티"""

    @staticmethod
    def parse_date(date_string, default=None):
        """날짜 문자열 파싱 (기본값 미지정 시 호출 시점의 현재 날짜 적용)"""
        fallback_date = default if default is not None else date.today()
        if not date_string:
            return fallback_date

        try:
            return datetime.strptime(date_string, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return fallback_date

    @staticmethod
    def format_date(date_obj, format_str='%Y-%m-%d'):
        """날짜 포맷팅"""
        if not date_obj:
            return ''
        return date_obj.strftime(format_str)

    @staticmethod
    def get_date_range_filter(start_date, end_date):
        """날짜 범위 필터 생성"""
        filters = {}
        if start_date:
            filters['deal_date__gte'] = start_date
        if end_date:
            filters['deal_date__lte'] = end_date
        return filters


class FormattingMixin:
    """데이터 포맷팅 관련 기능"""

    @staticmethod
    def format_currency(amount):
        """통화 형식으로 포맷 (문자열, Decimal, float, int 완벽 방어)"""
        if amount is None or amount == '':
            return '0'
        try:
            if isinstance(amount, str):
                clean_str = amount.replace(',', '').strip()
                amount = float(clean_str) if '.' in clean_str else int(clean_str)
            elif isinstance(amount, Decimal):
                amount = float(amount) if amount % 1 else int(amount)
            return f"{amount:,}"
        except (ValueError, TypeError):
            return str(amount)

    @staticmethod
    def format_percentage(value, decimal_places=2):
        """퍼센티지 형식으로 포맷"""
        if value is None:
            return "0%"
        try:
            val_float = float(value)
            return f"{val_float:.{decimal_places}f}%"
        except (ValueError, TypeError):
            return "0%"

    @staticmethod
    def safe_division(dividend, divisor, default=0):
        """안전한 나눗셈"""
        try:
            return dividend / divisor if divisor != 0 else default
        except (TypeError, ZeroDivisionError):
            return default


class PdfUtilsMixin:
    """PDF 관련 유틸리티 기능"""

    @staticmethod
    def get_blank_line_count(content_count, max_lines=14):
        """공백 라인 수 계산"""
        blank_count = max_lines - content_count
        return max(0, blank_count)

    @staticmethod
    def create_filename(base_name, identifier=None, extension='pdf'):
        """파일명 생성"""
        filename_parts = [base_name]

        if identifier:
            filename_parts.append(str(identifier))

        filename = '_'.join(filename_parts)
        return f"{filename}.{extension}"

    @staticmethod
    def paginate_data(data_list, items_per_page=20):
        """데이터 페이지네이션"""
        paginated_data = []
        for i in range(0, len(data_list), items_per_page):
            paginated_data.append(data_list[i:i + items_per_page])
        return paginated_data
