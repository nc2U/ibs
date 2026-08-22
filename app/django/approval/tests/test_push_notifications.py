from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from approval.models import (
    DocCategory,
    DocumentType,
    ApprovalDocument,
    ApprovalStep,
)
from approval.tasks import notify_approvers_task, notify_drafter_task
from accounts.models import Notification, FCMDevice
from _utils.push_service import send_push_notification

User = get_user_model()


class ApprovalPushNotificationTestCase(TestCase):
    """결재 알림 및 FCM 푸시 발송 파이프라인 자동화 단위/통합 테스트"""

    def setUp(self):
        # 1. 테스트 사용자 생성 (기안자, 결재자 1, 결재자 2)
        self.drafter = User.objects.create_user(
            username='drafter_user', email='drafter@example.com', password='password123'
        )
        self.approver1 = User.objects.create_user(
            username='approver_user1', email='approver1@example.com', password='password123'
        )
        self.approver2 = User.objects.create_user(
            username='approver_user2', email='approver2@example.com', password='password123'
        )

        # 2. 결재자 모바일 FCM 기기 토큰 등록
        self.device1 = FCMDevice.objects.create(
            user=self.approver1,
            registration_id='mock_fcm_token_approver_1_android',
            platform='android',
            is_active=True,
        )
        self.device2 = FCMDevice.objects.create(
            user=self.approver2,
            registration_id='mock_fcm_token_approver_2_ios',
            platform='ios',
            is_active=True,
        )

        # 3. 문서 카테고리 및 유형 생성
        self.category = DocCategory.objects.create(name='인사/총무')
        self.doc_type = DocumentType.objects.create(
            category=self.category,
            name='휴가신청서',
            code='VACATION',
        )

        # 4. 결재 문서 및 결재선 단계 생성
        self.document = ApprovalDocument.objects.create(
            doc_type=self.doc_type,
            drafter=self.drafter,
            title='[연차] 하계 휴가 신청의 건',
            content={'reason': '개인 휴가'},
            status=ApprovalDocument.STATUS_PENDING,
            current_step=1,
        )

        self.step1 = ApprovalStep.objects.create(
            document=self.document,
            step_order=1,
            role_label='팀장 결재',
            status=ApprovalStep.STATUS_PENDING,
        )
        self.step1.approvers.add(self.approver1)

    @patch('_utils.push_service._get_firebase_app')
    def test_send_push_notification_creates_db_records_and_dispatches_fcm(self, mock_firebase_app):
        """1. 푸시 발송 서비스가 DB Notification을 생성하고 FCM Multicast 전송을 올바르게 호출하는지 검증"""
        mock_firebase_app.return_value = True

        with patch('firebase_admin.messaging.send_each_for_multicast') as mock_send_fcm:
            # FCM 성공 응답 모킹
            mock_response = MagicMock()
            mock_response.success_count = 1
            mock_response.failure_count = 0
            mock_send_fcm.return_value = mock_response

            created_count = send_push_notification(
                user_ids=[self.approver1.id],
                title='[결재 요청] 휴가신청서',
                body='drafter_user님이 결재를 요청했습니다.',
                category='approval',
                target_type='approval_document',
                target_id=str(self.document.id),
                extra_data={'badge': '1'},
            )

            # DB Notification 레코드 생성 검증
            self.assertEqual(created_count, 1)
            notif = Notification.objects.filter(user=self.approver1).first()
            self.assertIsNotNone(notif)
            self.assertEqual(notif.title, '[결재 요청] 휴가신청서')
            self.assertEqual(notif.category, 'approval')
            self.assertFalse(notif.is_read)

            # FCM Multicast 호출 파라미터 검증 (채널 ID: ibs_high_importance_channel 및 토큰)
            mock_send_fcm.assert_called_once()
            multicast_arg = mock_send_fcm.call_args[0][0]
            self.assertIn(self.device1.registration_id, multicast_arg.tokens)
            self.assertEqual(multicast_arg.android.notification.channel_id, 'ibs_high_importance_channel')

    @patch('_utils.push_service.send_push_notification')
    def test_notify_approvers_task_execution(self, mock_send_push):
        """2. Celery notify_approvers_task 비동기 작업 실행 시 올바른 파라미터로 푸시 발송을 트리거하는지 검증"""
        notify_approvers_task(self.document.pk, self.step1.pk)

        mock_send_push.assert_called_once()
        call_kwargs = mock_send_push.call_args[1]

        self.assertEqual(call_kwargs['user_ids'], [self.approver1.id])
        self.assertIn('휴가신청서', call_kwargs['title'])
        self.assertIn('결재를 요청했습니다', call_kwargs['body'])
        self.assertEqual(call_kwargs['category'], 'approval')
        self.assertEqual(call_kwargs['target_id'], str(self.document.pk))

    @patch('_utils.push_service.send_push_notification')
    def test_notify_drafter_task_on_approved(self, mock_send_push):
        """3. 결재 최종 승인 시 기안자에게 알림이 정상 발송되는지 검증"""
        notify_drafter_task(self.document.pk, action='approved')

        mock_send_push.assert_called_once()
        call_kwargs = mock_send_push.call_args[1]

        self.assertEqual(call_kwargs['user_ids'], [self.drafter.id])
        self.assertIn('최종 승인', call_kwargs['body'])
