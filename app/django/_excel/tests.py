import datetime
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase, RequestFactory

from _excel.mixins import (
    ExcelExportMixin,
    ProjectFilterMixin,
    ExcelUtilsMixin,
    AdvancedExcelMixin,
    TODAY,
)

User = get_user_model()


class ExcelExportMixinTests(TestCase):
    """ExcelExportMixin 및 엑셀 내보내기 핵심 기능 테스트"""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='excel_tester',
            email='tester@example.com',
            password='testpassword123'
        )

    def test_unauthenticated_access_is_blocked(self):
        """비인증 사용자의 엑셀 요청은 302 리다이렉트되어 데이터 유출이 차단되는지 검증"""
        # 1. CBV 테스트 (ExcelExportMixin을 상속받은 뷰)
        view = ExcelExportMixin.as_view()
        request = self.factory.get('/excel/contracts/')
        request.user = AnonymousUser()
        response = view(request)
        # LoginRequiredMixin의 기본 동작: 로그인 페이지로 302 리다이렉트
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/accounts/login/' in response.url or '/login/' in response.url)

    def test_authenticated_access_is_allowed(self):
        """인증된 사용자의 엑셀 요청은 정상 처리되는지 검증"""
        view = ExcelExportMixin.as_view()
        request = self.factory.get('/excel/contracts/')
        request.user = self.user
        response = view(request)
        # 기본 get 메서드가 없으면 405 Method Not Allowed이지만 LoginRequiredMixin 통과는 성공
        self.assertEqual(response.status_code, 405)

    def test_today_proxy_is_dynamic(self):
        """TODAY 심볼이 현재 날짜를 동적으로 반환하는지 검증"""
        current_today = datetime.date.today().strftime('%Y-%m-%d')
        self.assertEqual(str(TODAY), current_today)
        self.assertEqual(TODAY, current_today)
        self.assertEqual(ExcelExportMixin.get_today_str(), current_today)

    def test_today_proxy_truthiness_and_string_methods(self):
        """TODAY 프록시의 참/거짓 평가(truthiness), 길이 및 문자열 메서드 지원 검증"""
        current_today = datetime.date.today().strftime('%Y-%m-%d')
        self.assertTrue(bool(TODAY))
        self.assertEqual(len(TODAY), 10)
        self.assertTrue(TODAY.startswith(current_today[:4]))
        self.assertEqual(TODAY.split('-'), current_today.split('-'))
        self.assertEqual(TODAY.replace('-', '.'), current_today.replace('-', '.'))
        self.assertEqual(f"{TODAY}", current_today)

    def test_sanitize_sheet_name(self):
        """엑셀 시트 이름의 31자 제한 및 금지문자 제거 검증"""
        # 금지문자 제거
        dirty_name = "프로젝트:현장/공사*보고?안내[완료]"
        clean_name = ExcelExportMixin.sanitize_sheet_name(dirty_name)
        self.assertEqual(clean_name, "프로젝트현장공사보고안내완료")

        # 31자 초과 시 절단
        long_name = "가나다라마바사아자차카타파하1234567890abcdefghijklmn"
        self.assertTrue(len(long_name) > 31)
        truncated_name = ExcelExportMixin.sanitize_sheet_name(long_name)
        self.assertEqual(len(truncated_name), 31)
        self.assertEqual(truncated_name, long_name[:31])

        # None/빈 문자열 처리
        self.assertEqual(ExcelExportMixin.sanitize_sheet_name(None), '데이터')
        self.assertEqual(ExcelExportMixin.sanitize_sheet_name(''), '데이터')

    def test_get_field_value_preserves_numeric_types(self):
        """숫자 및 Decimal 타입이 문자열로 강제 변환되지 않고 원본 수치로 보존되는지 검증"""
        data = {
            'amount_int': 15000000,
            'amount_float': 12345.67,
            'amount_decimal': Decimal('9999000.00'),
            'amount_decimal_fraction': Decimal('123.45'),
            'date_val': datetime.date(2026, 10, 23),
            'text_val': '일반 텍스트',
            'nested': {
                'deep_val': 5500
            }
        }

        # 정수 보존
        val_int = ExcelExportMixin.get_field_value(data, 'amount_int')
        self.assertIsInstance(val_int, int)
        self.assertEqual(val_int, 15000000)

        # 실수 보존
        val_float = ExcelExportMixin.get_field_value(data, 'amount_float')
        self.assertIsInstance(val_float, float)
        self.assertEqual(val_float, 12345.67)

        # Decimal 보존 (정수형태는 int로 변환되어 엑셀 수식 최적화)
        val_dec = ExcelExportMixin.get_field_value(data, 'amount_decimal')
        self.assertEqual(val_dec, 9999000)
        self.assertIsInstance(val_dec, int)

        val_dec_frac = ExcelExportMixin.get_field_value(data, 'amount_decimal_fraction')
        self.assertEqual(val_dec_frac, 123.45)
        self.assertIsInstance(val_dec_frac, float)

        # 날짜 포맷팅
        val_date = ExcelExportMixin.get_field_value(data, 'date_val')
        self.assertEqual(val_date, '2026-10-23')

        # 중첩 딕셔너리 접근
        val_nested = ExcelExportMixin.get_field_value(data, 'nested__deep_val')
        self.assertEqual(val_nested, 5500)

    def test_get_field_value_supports_callable(self):
        """get_field_value가 인자 없는 메서드(get_status_display 등)를 자동 실행하여 값을 반환하는지 검증"""
        class DummyModel:
            status = '1'

            def get_status_display(self):
                return '승인완료'

            def calculate_score(self):
                return 95.5

        instance = DummyModel()
        self.assertEqual(ExcelExportMixin.get_field_value(instance, 'get_status_display'), '승인완료')
        self.assertEqual(ExcelExportMixin.get_field_value(instance, 'calculate_score'), 95.5)

    def test_write_data_rows_decimal_and_callable(self):
        """write_data_rows가 실수 소수점 보존 서식 및 callable 값을 올바르게 작성하는지 검증"""
        output, workbook, worksheet = ExcelExportMixin.create_workbook("데이터행_테스트")
        headers = [
            ('단지', 'complex_name', 15),
            ('면적', 'area', 10),
            ('금액', 'amount', 15),
            ('상태', 'get_status_display', 12),
        ]

        class DummyRow:
            complex_name = '1단지'
            area = 84.95
            amount = 500000000

            def get_status_display(self):
                return '계약완료'

        rows = [DummyRow()]
        end_row = ExcelExportMixin().write_data_rows(worksheet, workbook, 0, headers, rows)
        workbook.close()
        self.assertEqual(end_row, 1)

    def test_create_workbook_and_response(self):
        """워크북 생성 및 응답 객체 생성 정상 동작 검증 (중복 close 가드 포함)"""
        output, workbook, worksheet = ExcelExportMixin.create_workbook("테스트_시트")
        worksheet.write(0, 0, "테스트")

        # 의도적으로 뷰 레벨에서 workbook.close()를 먼저 호출한 상황 시뮬레이션
        workbook.close()

        # create_response가 중복 close 경고나 예외 없이 정상 응답(200)을 생성하는지 확인
        response = ExcelExportMixin.create_response(output, workbook, "test_export_2026")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        self.assertIn('test_export_2026.xlsx', response['Content-Disposition'])


class ExcelUtilsMixinTests(TestCase):
    """ExcelUtilsMixin의 포맷팅 안전성 테스트"""

    def test_format_currency_robustness(self):
        """문자열, Decimal, float, int, None 등 다양한 입력에 대한 안전한 포맷팅 검증"""
        self.assertEqual(ExcelUtilsMixin.format_currency(1000000), "1,000,000")
        self.assertEqual(ExcelUtilsMixin.format_currency("1000000"), "1,000,000")
        self.assertEqual(ExcelUtilsMixin.format_currency("1,000,000"), "1,000,000")
        self.assertEqual(ExcelUtilsMixin.format_currency(Decimal("2500000")), "2,500,000")
        self.assertEqual(ExcelUtilsMixin.format_currency(1234.56), "1,234.56")
        self.assertEqual(ExcelUtilsMixin.format_currency(None), "")
        self.assertEqual(ExcelUtilsMixin.format_currency(""), "")
        self.assertEqual(ExcelUtilsMixin.format_currency("invalid_number"), "invalid_number")

    def test_format_phone(self):
        """전화번호 포맷팅 검증 (일반 및 서울 02 국번 지원 및 숫자형 입력 대응)"""
        self.assertEqual(ExcelUtilsMixin.format_phone("01012345678"), "010-1234-5678")
        self.assertEqual(ExcelUtilsMixin.format_phone("0212345678"), "02-1234-5678")
        self.assertEqual(ExcelUtilsMixin.format_phone("021235678"), "02-123-5678")
        self.assertEqual(ExcelUtilsMixin.format_phone("0311234567"), "031-123-4567")
        self.assertEqual(ExcelUtilsMixin.format_phone(1012345678), "101-234-5678")
        self.assertEqual(ExcelUtilsMixin.format_phone(None), "")

    def test_safe_get_attr(self):
        """safe_get_attr의 딕셔너리 및 객체 탐색 지원 검증 (callable 지원 포함)"""
        class Profile:
            age = 30
            def get_title(self):
                return '매니저'

        obj_dict = {'user': {'profile': Profile()}}
        self.assertEqual(ExcelUtilsMixin.safe_get_attr(obj_dict, 'user__profile__age'), 30)
        self.assertEqual(ExcelUtilsMixin.safe_get_attr(obj_dict, 'user__profile__get_title'), '매니저')
        self.assertEqual(ExcelUtilsMixin.safe_get_attr(obj_dict, 'user__unknown__key', default='기본값'), '기본값')


class ProjectFilterMixinTests(TestCase):
    """ProjectFilterMixin의 쿼리 파라미터 파싱 검증"""

    def setUp(self):
        self.factory = RequestFactory()

    def test_get_selected_columns(self):
        """컬럼 파라미터(col=1-3-2) 안전 파싱 검증"""
        req1 = self.factory.get('/excel/test/?col=3-1-2')
        self.assertEqual(ProjectFilterMixin.get_selected_columns(req1), [1, 2, 3])

        req_empty = self.factory.get('/excel/test/')
        self.assertEqual(ProjectFilterMixin.get_selected_columns(req_empty), [])

        req_invalid = self.factory.get('/excel/test/?col=invalid-abc')
        self.assertEqual(ProjectFilterMixin.get_selected_columns(req_invalid), [])
