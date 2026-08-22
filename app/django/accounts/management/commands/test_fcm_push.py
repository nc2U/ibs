import sys
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import FCMDevice
from _utils.push_service import send_push_notification, _get_firebase_app

User = get_user_model()


class Command(BaseCommand):
    help = '특정 사용자 또는 전체 활성 기기로 FCM 테스트 푸시 발송 및 파이프라인 검증'

    def add_arguments(self, parser):
        parser.add_argument('--user', type=str, help='푸시를 보낼 대상 사용자 username (미지정 시 전체 활성 기기)')
        parser.add_argument('--title', type=str, default='[IBS 웍스] 푸시 알림 테스트', help='푸시 알림 제목')
        parser.add_argument('--body', type=str, default='이동 중 결재 및 업무 알림 파이프라인 정상 검증 완료', help='푸시 알림 내용')
        parser.add_argument('--check-only', action='store_true', help='발송하지 않고 Firebase 설정 및 활성 토큰 현황만 점검')

    def handle(self, *args, **options):
        username = options.get('user')
        title = options.get('title')
        body = options.get('body')
        check_only = options.get('check_only')

        self.stdout.write(self.style.NOTICE("🔍 [1/3] Firebase Admin SDK 설정 상태 점검..."))
        try:
            import firebase_admin
            from firebase_admin import credentials
            from django.conf import settings
            import base64
            import json
            import os

            b64_cred = getattr(settings, 'FIREBASE_CREDENTIALS_BASE64', None)
            cred_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', None)
            self.stdout.write(f"  - FIREBASE_CREDENTIALS_BASE64 길이: {len(b64_cred) if b64_cred else 0}")
            self.stdout.write(f"  - FIREBASE_CREDENTIALS_PATH: {cred_path}")

            if b64_cred:
                cred_dict = json.loads(base64.b64decode(b64_cred).decode('utf-8'))
                self.stdout.write(f"  - Project ID: {cred_dict.get('project_id')}")
                self.stdout.write(f"  - Client Email: {cred_dict.get('client_email')}")
            
            is_firebase_ok = _get_firebase_app()
            if is_firebase_ok:
                self.stdout.write(self.style.SUCCESS("  ✅ Firebase Admin SDK가 정상적으로 초기화되었습니다."))
            else:
                self.stdout.write(self.style.ERROR("  ❌ Firebase Admin SDK 초기화 실패 (_get_firebase_app returned False)"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ❌ Firebase Admin SDK 초기화 예외 발생: {type(e).__name__}: {e}"))

        self.stdout.write(self.style.NOTICE("\n📱 [2/3] 등록된 모바일 기기(FCMDevice) 토큰 점검..."))
        if username:
            try:
                target_user = User.objects.get(username=username)
                devices = FCMDevice.objects.filter(user=target_user)
                user_ids = [target_user.id]
                self.stdout.write(f"  - 대상 사용자: {target_user.username} (ID: {target_user.id})")
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"  ❌ 사용자 '{username}'를 찾을 수 없습니다."))
                return
        else:
            devices = FCMDevice.objects.all()
            user_ids = list(devices.filter(is_active=True).values_list('user_id', flat=True).distinct())
            self.stdout.write("  - 대상 사용자: 전체 등록 기기 대상")

        total_devices = devices.count()
        active_devices = devices.filter(is_active=True).count()
        self.stdout.write(f"  - 총 등록 기기 수: {total_devices}대 (활성 기기: {active_devices}대)")

        for dev in devices:
            status_str = "✅ 활성" if dev.is_active else "❌ 비활성"
            token_preview = f"{dev.registration_id[:15]}...{dev.registration_id[-10:]}" if len(dev.registration_id) > 25 else dev.registration_id
            self.stdout.write(f"    • [{dev.platform}] {dev.user.username} | {token_preview} | {status_str} (수정: {dev.updated_at.strftime('%Y-%m-%d %H:%M')})")

        if check_only:
            self.stdout.write(self.style.SUCCESS("\n✨ 점검 완료 (--check-only 모드)"))
            return

        if not user_ids or active_devices == 0:
            self.stdout.write(self.style.WARNING("\n⚠️ 발송 가능한 활성 기기 토큰이 없습니다. 모바일 앱에서 먼저 로그인하여 토큰을 등록해 주세요."))
            return

        self.stdout.write(self.style.NOTICE(f"\n🚀 [3/3] 테스트 푸시 발송 실행..."))
        self.stdout.write(f"  - 제목: {title}")
        self.stdout.write(f"  - 내용: {body}")

        created_count = send_push_notification(
            user_ids=user_ids,
            title=title,
            body=body,
            category='approval',
            target_type='test',
            target_id='0',
            extra_data={'test': 'true', 'badge': '1'},
        )

        self.stdout.write(self.style.SUCCESS(f"\n🎉 푸시 발송 처리가 완료되었습니다! (생성된 알림 수: {created_count})"))
        self.stdout.write("모바일 기기의 상단 알림 바 및 앱 아이콘 배지를 확인해 주세요.\n")
