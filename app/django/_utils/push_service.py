import logging
from django.conf import settings
from accounts.models import Notification, FCMDevice

logger = logging.getLogger(__name__)

# Firebase Admin SDK 초기화 (서비스 계정 설정이 있을 때만 로드)
_firebase_initialized = False


def _get_firebase_app():
    global _firebase_initialized
    if _firebase_initialized:
        return True

    try:
        import firebase_admin
        from firebase_admin import credentials

        cred_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', None)
        if cred_path:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            _firebase_initialized = True
            return True
        elif len(firebase_admin._apps) > 0:
            _firebase_initialized = True
            return True
    except Exception as e:
        logger.debug(f"Firebase admin SDK not configured: {e}")

    return False


def send_push_notification(
    user_ids,
    title,
    body,
    category='work',
    target_type='',
    target_id='',
    extra_data=None,
):
    """
    1. 대상 사용자들의 DB Notification 레코드 생성
    2. 활성화된 모바일 기기(FCMDevice)로 FCM 푸시 발송
    """
    if not user_ids:
        return 0

    if extra_data is None:
        extra_data = {}

    # 1. DB 알림 레코드 벌크 생성
    notifications_to_create = [
        Notification(
            user_id=uid,
            title=title,
            body=body,
            category=category,
            target_type=target_type,
            target_id=str(target_id) if target_id else '',
            data=extra_data,
        )
        for uid in user_ids
    ]
    try:
        Notification.objects.bulk_create(notifications_to_create)
    except Exception as e:
        logger.error(f"Failed to create Notification records: {e}")

    # 2. 활성 FCM 기기 토큰 조회
    devices = FCMDevice.objects.filter(user_id__in=user_ids, is_active=True)
    tokens = list(devices.values_list('registration_id', flat=True))

    if not tokens:
        return len(notifications_to_create)

    # 3. Firebase Admin SDK를 통한 푸시 발송
    if _get_firebase_app():
        try:
            from firebase_admin import messaging

            # 문자열 데이터 페이로드 구성 (FCM data는 문자열만 허용)
            fcm_data = {
                'category': str(category),
                'target_type': str(target_type),
                'target_id': str(target_id),
                'title': str(title),
                'body': str(body),
            }
            for k, v in extra_data.items():
                fcm_data[str(k)] = str(v)

            multicast_msg = messaging.MulticastMessage(
                tokens=tokens,
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=fcm_data,
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='default',
                            badge=1,
                        )
                    )
                ),
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound='default',
                        channel_id='ibs_high_importance_channel',
                    ),
                ),
            )

            response = messaging.send_each_for_multicast(multicast_msg)
            logger.info(
                f"FCM Push sent: {response.success_count} success, {response.failure_count} failure out of {len(tokens)} tokens"
            )

            # 만료/실패한 토큰 비활성화 처리
            if response.failure_count > 0:
                for idx, resp in enumerate(response.responses):
                    if not resp.success:
                        err_code = getattr(resp.exception, 'code', '')
                        if err_code in ('NOT_FOUND', 'UNREGISTERED', 'INVALID_ARGUMENT'):
                            FCMDevice.objects.filter(registration_id=tokens[idx]).update(is_active=False)

        except Exception as e:
            logger.error(f"FCM Push dispatch error: {e}")
    else:
        logger.debug(f"FCM simulation: Push would be sent to {len(tokens)} tokens -> {title}: {body}")

    return len(notifications_to_create)
