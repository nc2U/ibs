import datetime
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase, RequestFactory

from _pdf.mixins import (
    PdfExportMixin,
    FormattingMixin,
    DateUtilMixin,
    PdfUtilsMixin,
    PaymentPdfMixin,
    ContractPdfMixin,
)
from _pdf.utils import TODAY, get_today, get_late_fee

User = get_user_model()


class PdfExportMixinTests(TestCase):
    """PdfExportMixin 및 PDF 내보내기 핵심 기능 테스트"""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='pdf_tester',
            email='pdftester@example.com',
            password='testpassword123'
        )

    def test_unauthenticated_access_is_blocked(self):
        """비인증 사용자의 PDF 요청은 302 리다이렉트되어 정보 유출이 차단되는지 검증"""
        view = PdfExportMixin.as_view()
        request = self.factory.get('/pdf/work/meeting/1/')
        request.user = AnonymousUser()
        response = view(request)
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/accounts/login/' in response.url or '/login/' in response.url)

    def test_authenticated_access_is_allowed(self):
        """인증된 사용자는 LoginRequired를 정상 통과하는지 검증"""
        view = PdfExportMixin.as_view()
        request = self.factory.get('/pdf/work/meeting/1/')
        request.user = self.user
        response = view(request)
        # get() 미구현 시 405 Method Not Allowed이지만 LoginRequired 통과는 성공
        self.assertEqual(response.status_code, 405)

    def test_safe_url_fetcher_blocks_ssrf(self):
        """WeasyPrint safe_url_fetcher가 내부망, 메타데이터 IP 및 비인가 로컬 파일을 차단하는지 검증 (SSRF/LFI 방어)"""
        # 1. AWS/클라우드 메타데이터 차단
        with self.assertRaises(ValueError):
            PdfExportMixin.safe_url_fetcher('http://169.254.169.254/latest/meta-data/')

        # 2. 로컬 루프백 차단
        with self.assertRaises(ValueError):
            PdfExportMixin.safe_url_fetcher('http://127.0.0.1:8000/secret')
        with self.assertRaises(ValueError):
            PdfExportMixin.safe_url_fetcher('http://localhost:8080/')

        # 3. K8s 내부 서비스 및 사설망 IP 차단
        with self.assertRaises(ValueError):
            PdfExportMixin.safe_url_fetcher('http://minio.default.svc.cluster.local:9000/bucket')
        with self.assertRaises(ValueError):
            PdfExportMixin.safe_url_fetcher('http://10.0.0.5/api')
        with self.assertRaises(ValueError):
            PdfExportMixin.safe_url_fetcher('http://192.168.1.100/')
        with self.assertRaises(ValueError):
            PdfExportMixin.safe_url_fetcher('http://172.20.0.1/')

        # 4. data: URI 허용 (폰트 및 인라인 이미지용)
        result = PdfExportMixin.safe_url_fetcher('data:text/plain;base64,SGVsbG8=')
        self.assertIsNotNone(result)

        # 5. 비인가 시스템 파일 경로 차단 (LFI 방어)
        with self.assertRaises(ValueError):
            PdfExportMixin.safe_url_fetcher('file:///etc/passwd')
        with self.assertRaises(ValueError):
            PdfExportMixin.safe_url_fetcher('file:///etc/shadow')

    def test_today_proxy_is_dynamic(self):
        """TODAY 심볼 및 get_today()가 현재 날짜를 동적으로 반환하고 해시를 지원하는지 검증"""
        current_today = datetime.date.today()
        self.assertEqual(get_today(), current_today)
        self.assertEqual(str(TODAY), str(current_today))
        self.assertEqual(TODAY.year, current_today.year)
        self.assertEqual(TODAY.month, current_today.month)
        self.assertEqual(TODAY.day, current_today.day)
        # 해시 지원 및 딕셔너리/Set 키 사용성 검증
        self.assertEqual(hash(TODAY), hash(current_today))
        self.assertEqual({TODAY: 'val'}[TODAY], 'val')
        self.assertIn(TODAY, {TODAY})

    def test_get_late_fee_returns_zero_when_no_rules(self):
        """연체 규정 미등록 프로젝트에 대한 get_late_fee 호출 시 None이 아닌 0 반환 검증"""
        fee = get_late_fee(None, 5000000, 15)
        self.assertEqual(fee, 0)
        self.assertIsInstance(fee, int)

    def test_create_pdf_response(self):
        """create_pdf_response가 유효한 PDF 응답을 생성하고 표준 Content-Disposition을 설정하는지 검증"""
        request = self.factory.get('/')
        response = PdfExportMixin.create_pdf_response(
            'pdf/bill_control.html',
            {},
            '테스트 공문 (2026)',
            request=request
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(len(response.content) > 500)
        # Content-Disposition 헤더에 ASCII filename 및 RFC 5987 filename* 동시 지원 확인
        self.assertIn('filename=', response['Content-Disposition'])
        self.assertIn("filename*=UTF-8''", response['Content-Disposition'])


class FormattingMixinTests(TestCase):
    """FormattingMixin 데이터 포맷팅 안전성 테스트"""

    def test_format_currency_robustness(self):
        """다양한 타입 입력에 대한 안전한 통화 포맷팅 검증"""
        self.assertEqual(FormattingMixin.format_currency(1000000), "1,000,000")
        self.assertEqual(FormattingMixin.format_currency("1000000"), "1,000,000")
        self.assertEqual(FormattingMixin.format_currency("1,000,000"), "1,000,000")
        self.assertEqual(FormattingMixin.format_currency(Decimal("2500000")), "2,500,000")
        self.assertEqual(FormattingMixin.format_currency(1234.56), "1,234.56")
        self.assertEqual(FormattingMixin.format_currency(None), "0")
        self.assertEqual(FormattingMixin.format_currency(""), "0")
        self.assertEqual(FormattingMixin.format_currency("invalid_number"), "invalid_number")

    def test_format_percentage(self):
        """퍼센티지 포맷팅 검증"""
        self.assertEqual(FormattingMixin.format_percentage(12.3456), "12.35%")
        self.assertEqual(FormattingMixin.format_percentage(0), "0.00%")
        self.assertEqual(FormattingMixin.format_percentage(None), "0%")

    def test_safe_division(self):
        """안전한 나눗셈(ZeroDivisionError 방어) 검증"""
        self.assertEqual(FormattingMixin.safe_division(10, 2), 5.0)
        self.assertEqual(FormattingMixin.safe_division(10, 0), 0)
        self.assertEqual(FormattingMixin.safe_division(10, 0, default=-1), -1)


class DateUtilMixinTests(TestCase):
    """DateUtilMixin 날짜 파싱 및 유틸리티 검증"""

    def test_parse_date(self):
        self.assertEqual(DateUtilMixin.parse_date('2026-10-23'), datetime.date(2026, 10, 23))
        self.assertEqual(DateUtilMixin.parse_date('invalid'), datetime.date.today())
        fallback = datetime.date(2020, 1, 1)
        self.assertEqual(DateUtilMixin.parse_date('invalid', default=fallback), fallback)

    def test_format_date(self):
        d = datetime.date(2026, 10, 23)
        self.assertEqual(DateUtilMixin.format_date(d), '2026-10-23')
        self.assertEqual(DateUtilMixin.format_date(None), '')


class PdfUtilsMixinTests(TestCase):
    """PdfUtilsMixin 유틸리티 기능 검증"""

    def test_get_blank_line_count(self):
        self.assertEqual(PdfUtilsMixin.get_blank_line_count(10, max_lines=14), 4)
        self.assertEqual(PdfUtilsMixin.get_blank_line_count(20, max_lines=14), 0)

    def test_create_filename(self):
        self.assertEqual(PdfUtilsMixin.create_filename('meeting', '2026'), 'meeting_2026.pdf')
        self.assertEqual(PdfUtilsMixin.create_filename('report'), 'report.pdf')

    def test_paginate_data(self):
        items = list(range(25))
        pages = PdfUtilsMixin.paginate_data(items, items_per_page=10)
        self.assertEqual(len(pages), 3)
        self.assertEqual(len(pages[0]), 10)
        self.assertEqual(len(pages[2]), 5)
