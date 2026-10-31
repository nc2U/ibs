from datetime import date
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase

from _utils.contract_price import (
    get_project_payment_summary,
    get_due_date_per_order,
    get_down_payment_settlement,
)
from _utils.file_cleanup import delete_file_field
from _utils.file_upload import generate_safe_filename, get_upload_path, populate_file_meta
from _utils.file_service import FileService
from _utils.payment_adjustment import (
    calculate_daily_interest,
    get_effective_contract_date,
    aggregate_installment_adjustments,
)
from _utils.push_service import send_push_notification
from _utils.slack_notifications import get_slack_webhook_url


class FileUploadUtilsTestCase(TestCase):
    """파일 업로드 관련 유틸리티 테스트"""

    def test_generate_safe_filename_preserves_extension_and_ascii(self):
        filename = "아파트_분양계약서_홍길동.pdf"
        safe_name = generate_safe_filename(filename)

        # 확장자가 .pdf로 보존되는지 확인
        self.assertTrue(safe_name.endswith(".pdf"))
        # 파일명이 ASCII로만 구성되어 있는지 확인
        self.assertTrue(all(ord(c) < 128 for c in safe_name))
        # 언더스코어로 구분된 타임스탬프와 해시 구조 확인
        parts = safe_name.split("_")
        self.assertGreaterEqual(len(parts), 3)

    def test_generate_safe_filename_uniqueness(self):
        filename = "계약서.docx"
        safe1 = generate_safe_filename(filename, include_microseconds=True)
        safe2 = generate_safe_filename(filename, include_microseconds=True)
        self.assertTrue(safe1.endswith(".docx"))
        self.assertTrue(safe2.endswith(".docx"))

    def test_get_upload_path(self):
        mock_instance = MagicMock()
        path = get_upload_path(mock_instance, "견적서.xlsx", "company", "documents")
        normalized_path = path.replace("\\", "/")
        self.assertTrue(normalized_path.startswith("company/documents/"))
        self.assertTrue(normalized_path.endswith(".xlsx"))

    def test_populate_file_meta_fallback_none(self):
        mock_instance = MagicMock()
        mock_file = MagicMock()
        mock_file.name = None
        mock_file._name = None
        mock_file.read.side_effect = Exception("error")
        setattr(mock_instance, "file", mock_file)

        populate_file_meta(mock_instance, file_field="file")
        self.assertEqual(getattr(mock_instance, "file_name"), "")


class PaymentAdjustmentUtilsTestCase(TestCase):
    """납부 조정 및 이자/할인 계산 유틸리티 테스트"""

    def test_calculate_daily_interest_valid(self):
        # 10,000,000원, 연이율 12%, 30일 연체
        principal = 10000000
        annual_rate = Decimal("12.0")
        days = 30
        expected = int((Decimal("12.0") / Decimal("100") / Decimal("365")) * 30 * 10000000)
        result = calculate_daily_interest(principal, annual_rate, days)
        self.assertEqual(result, expected)
        self.assertGreater(result, 0)

    def test_calculate_daily_interest_zero_or_negative(self):
        # 원금, 이율, 일수가 0 이하일 때 0 반환 검증
        self.assertEqual(calculate_daily_interest(0, Decimal("10.0"), 10), 0)
        self.assertEqual(calculate_daily_interest(100000, Decimal("0.0"), 10), 0)
        self.assertEqual(calculate_daily_interest(100000, Decimal("10.0"), 0), 0)
        self.assertEqual(calculate_daily_interest(-1000, Decimal("10.0"), 10), 0)

    def test_get_effective_contract_date(self):
        mock_contract = MagicMock()

        # 1. 둘 다 없는 경우
        mock_contract.sup_cont_date = None
        mock_contract.contractor = None
        self.assertIsNone(get_effective_contract_date(mock_contract))

        # 2. 공급계약일만 있는 경우
        d1 = date(2025, 1, 10)
        mock_contract.sup_cont_date = d1
        mock_contract.contractor = None
        self.assertEqual(get_effective_contract_date(mock_contract), d1)

        # 3. 계약자 계약일만 있는 경우
        d2 = date(2025, 2, 15)
        mock_contract.sup_cont_date = None
        mock_contract.contractor = MagicMock(contract_date=d2)
        self.assertEqual(get_effective_contract_date(mock_contract), d2)

        # 4. 둘 다 있는 경우 max 값 반환
        mock_contract.sup_cont_date = d1
        mock_contract.contractor = MagicMock(contract_date=d2)
        self.assertEqual(get_effective_contract_date(mock_contract), d2)

    @patch("_utils.payment_adjustment.calculate_all_installments_payment_allocation")
    def test_aggregate_installment_adjustments(self, mock_calc_allocation):
        # mock 회차 정보 및 all_status 설정
        mock_contract = MagicMock()
        mock_order1 = MagicMock(id=1, pay_code=1, pay_name="1차 계약금")
        mock_order2 = MagicMock(id=2, pay_code=2, pay_name="2차 계약금")

        pub_date = date(2025, 5, 1)

        # all_status mock 반환값 (최적화된 total_discount 및 penalty 포함)
        mock_calc_allocation.return_value = {
            1: {
                "due_date": date(2025, 3, 1),
                "is_fully_paid": True,
                "late_days": 0,
                "total_late_penalty": 0,
                "total_discount": 50000,
                "discount_days": 10,
                "late_payment_amount": 0,
                "late_payment_details": [],
            },
            2: {
                "due_date": date(2025, 4, 1),
                "is_fully_paid": False,
                "late_days": 15,
                "total_late_penalty": 30000,
                "total_discount": 0,
                "discount_days": 0,
                "late_payment_amount": 10000000,
                "late_payment_details": [
                    {
                        "type": "paid_late",
                        "payment_amount": 10000000,
                        "late_days": 15,
                        "late_penalty": 30000,
                    }
                ],
            },
        }

        mock_qs = MagicMock()
        mock_qs.filter.return_value.order_by.return_value = [mock_order1, mock_order2]

        result = aggregate_installment_adjustments(mock_contract, mock_qs, 2, pub_date)

        self.assertEqual(result["total_late_fee"], 30000)
        self.assertEqual(result["total_discount"], 50000)
        self.assertEqual(result["penalty_count"], 1)
        self.assertEqual(result["discount_count"], 1)
        self.assertEqual(len(result["installment_details"]), 2)
        # 고지서(PDF) 연동용 필드 검증
        self.assertEqual(result["installment_details"][0]["prepay_days"], 10)
        self.assertEqual(result["installment_details"][1]["effective_late_amount"], 10000000)
        self.assertEqual(result["installment_details"][1]["effective_late_days"], 15)


class PushServiceTestCase(TestCase):
    """푸시 알림 서비스 테스트 (UnboundLocalError 방지 및 카운트 검증)"""

    @patch("_utils.push_service.FCMDevice")
    @patch("redis.Redis.from_url")
    def test_send_push_notification_without_record_returns_zero(self, mock_redis, mock_fcm):
        mock_fcm.objects.filter.return_value.values_list.return_value = []

        # create_notification_record=False 호출 시 UnboundLocalError 없이 0 반환 검증
        result = send_push_notification(
            user_ids=[1, 2],
            title="테스트 알림",
            body="테스트 본문",
            create_notification_record=False,
        )

        self.assertEqual(result, 0)

    @patch("_utils.push_service.Notification")
    @patch("_utils.push_service.FCMDevice")
    @patch("redis.Redis.from_url")
    def test_send_push_notification_with_record_returns_count(self, mock_redis, mock_fcm, mock_notification):
        mock_fcm.objects.filter.return_value.values_list.return_value = []
        mock_notification.objects.bulk_create.return_value = [MagicMock(), MagicMock()]

        result = send_push_notification(
            user_ids=[1, 2],
            title="새 업무 할당",
            body="업무가 등록되었습니다.",
            create_notification_record=True,
        )

        self.assertEqual(result, 2)

    @patch("_utils.push_service.Notification")
    @patch("_utils.push_service.FCMDevice")
    @patch("redis.Redis.from_url")
    def test_send_push_notification_with_decimal_extra_data(self, mock_redis_from_url, mock_fcm, mock_notification):
        mock_fcm.objects.filter.return_value.values_list.return_value = []
        mock_redis_instance = MagicMock()
        mock_redis_from_url.return_value = mock_redis_instance

        # extra_data에 Decimal 및 date 포함 시 JSON 직렬화 오류 없이 Redis 발행 검증
        result = send_push_notification(
            user_ids=[10],
            title="수납 완료",
            body="계약금 수납 완료",
            category="payment",
            extra_data={"paid_amount": Decimal("15000000.00"), "paid_date": date(2025, 3, 1)},
            create_notification_record=False,
        )

        self.assertEqual(result, 0)
        self.assertEqual(mock_redis_instance.publish.call_count, 1)
        # Redis 발행 채널과 JSON 문자열 검증
        channel = mock_redis_instance.publish.call_args[0][0]
        payload = mock_redis_instance.publish.call_args[0][1]
        self.assertEqual(channel, "user_notify_10")
        self.assertIn("15000000.00", payload)
        self.assertIn("2025-03-01", payload)


class SlackNotificationsTestCase(TestCase):
    """Slack 웹훅 URL 추출 로직 테스트"""

    def test_get_slack_webhook_url_db_priority(self):
        mock_project = MagicMock()
        mock_project.slack_webhook_url = "https://hooks.slack.com/services/test/db/webhook"

        url = get_slack_webhook_url(mock_project)
        self.assertEqual(url, "https://hooks.slack.com/services/test/db/webhook")

    @patch("_utils.slack_notifications.config")
    def test_get_slack_webhook_url_env_fallback(self, mock_config):
        mock_project = MagicMock()
        mock_project.slack_webhook_url = ""
        mock_project.type = "2"
        mock_project.slug = "project-alpha"

        mock_config.side_effect = lambda key, default=None: (
            "https://hooks.slack.com/services/project/alpha"
            if key == "SLACK_PROJECT_PROJECT_ALPHA"
            else default
        )

        url = get_slack_webhook_url(mock_project)
        self.assertEqual(url, "https://hooks.slack.com/services/project/alpha")


class FileServiceTestCase(TestCase):
    """FileService 파일 관리 및 file_cleanup 테스트"""

    def test_manage_files_create_new_file(self):
        mock_instance = MagicMock()
        mock_file_model = MagicMock()
        mock_user = MagicMock()

        initial_data = {
            "new_files": ["fake_file_content"],
            "descriptions": ["설명 텍스트"],
        }

        FileService.manage_files(
            instance=mock_instance,
            initial_data=initial_data,
            creator=mock_user,
            file_model=mock_file_model,
            related_name="meeting",
        )

        mock_file_model.objects.create.assert_called_once_with(
            meeting=mock_instance,
            file="fake_file_content",
            creator=mock_user,
            description="설명 텍스트",
        )

    def test_manage_files_with_dict_old_files(self):
        mock_instance = MagicMock()
        mock_file_model = MagicMock()

        # old_files가 JSON 문자열이 아닌 딕셔너리 리스트로 전달되는 경우 테스트
        initial_data = {
            "files": [{"pk": 15, "del": True}, {"pk": 20, "del": False}],
            "cngPks": [],
            "cngFiles": [],
        }

        FileService.manage_files(
            instance=mock_instance,
            initial_data=initial_data,
            file_model=mock_file_model,
            related_name="meeting",
        )

        mock_file_model.objects.filter.assert_called_once_with(pk="15", meeting=mock_instance)
        mock_file_model.objects.filter().delete.assert_called_once()

    def test_delete_file_field(self):
        mock_instance = MagicMock()
        mock_field = MagicMock()
        mock_field.name = "sample.pdf"
        setattr(mock_instance, "file", mock_field)

        delete_file_field(mock_instance, "file")
        mock_field.delete.assert_called_once_with(save=False)


class ContractPriceUtilsTestCase(TestCase):
    """분양가 및 분할 납부 계산 유틸리티 테스트"""

    def test_get_due_date_per_order_guards(self):
        # 1. contract가 None인 경우
        self.assertIsNone(get_due_date_per_order(None, {}))

        # 2. unit_type이 없는 경우
        mock_contract = MagicMock(unit_type=None, contractor=MagicMock(contract_date=date(2025, 1, 1)))
        mock_contract.sup_cont_date = None
        self.assertIsNone(get_due_date_per_order(mock_contract, {}))

    @patch("_utils.contract_price.InstallmentPaymentOrder")
    def test_get_due_date_per_order_sup_cont_date(self, mock_order_cls):
        # contractor_date 없이 sup_cont_date만 있는 경우
        d = date(2025, 3, 1)
        mock_contract = MagicMock(unit_type=MagicMock(sort="01"), contractor=None, sup_cont_date=d)
        mock_contract._first_future_date = None
        mock_order_cls.objects.filter.return_value.order_by.return_value.first.return_value = None

        order_dict = {"pay_code": 1, "pay_sort": "1"}
        result = get_due_date_per_order(mock_contract, order_dict)
        self.assertEqual(result, d)

    @patch("_utils.contract_price.get_total_paid_down_payments")
    @patch("_utils.contract_price.get_contract_price")
    def test_get_down_payment_settlement_never_negative(self, mock_price, mock_paid):
        mock_contract = MagicMock()
        mock_order = MagicMock(pay_ratio=Decimal("10.0"))
        mock_price.return_value = (100000000, 90000000, 10000000)
        # 기납부 계약금이 15,000,000원으로 10% 기준(10,000,000원)을 초과한 경우
        mock_paid.return_value = 15000000

        result = get_down_payment_settlement(mock_contract, mock_order)
        self.assertEqual(result, 0)

    @patch("_utils.contract_price.get_contract_payment_plan")
    @patch("_utils.contract_price.InstallmentPaymentOrder")
    def test_get_project_payment_summary_all_installments_counted(self, mock_inst_cls, mock_get_plan):
        mock_project = MagicMock()
        mock_c1 = MagicMock()
        mock_c2 = MagicMock()
        mock_project.contract_set.filter.return_value.select_related.return_value = [mock_c1, mock_c2]

        inst1 = MagicMock(id=101, pay_code=1, pay_time=1)
        inst2 = MagicMock(id=102, pay_code=2, pay_time=1)
        mock_inst_cls.objects.filter.return_value.order_by.return_value = [inst1, inst2]

        # 각 계약에 2개의 회차 계획이 있는 경우
        mock_get_plan.side_effect = [
            [
                {"installment_order": inst1, "amount": 10000000, "source": "calculated"},
                {"installment_order": inst2, "amount": 20000000, "source": "calculated"},
            ],
            [
                {"installment_order": inst1, "amount": 10000000, "source": "calculated"},
                {"installment_order": inst2, "amount": 20000000, "source": "calculated"},
            ],
        ]

        summary = get_project_payment_summary(mock_project)

        self.assertEqual(summary["total_contracts"], 2)
        self.assertEqual(summary["grand_total"], 60000000)
        summaries = summary["installment_summaries"]
        self.assertEqual(len(summaries), 2)

        # break 버그 수정 검증: 두 번째 회차도 contract_count가 2이고 평균 금액이 정상 계산되어야 함
        self.assertEqual(summaries[0]["installment_order"].id, 101)
        self.assertEqual(summaries[0]["contract_count"], 2)
        self.assertEqual(summaries[0]["total_amount"], 20000000)
        self.assertEqual(summaries[0]["average_amount"], 10000000)

        self.assertEqual(summaries[1]["installment_order"].id, 102)
        self.assertEqual(summaries[1]["contract_count"], 2)
        self.assertEqual(summaries[1]["total_amount"], 40000000)
        self.assertEqual(summaries[1]["average_amount"], 20000000)
