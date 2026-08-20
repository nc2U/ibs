import json
import logging
import time
from django.conf import settings
from django.http import StreamingHttpResponse, HttpResponseForbidden, HttpResponse
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

logger = logging.getLogger(__name__)


def sse_notification_stream(request):
    """
    Server-Sent Events (SSE) 실시간 알림 스트림 엔드포인트
    URL: /api/v1/notifications/stream/
    인증: Query param 'token' 또는 Authorization Bearer 헤더 지원
    """
    token_str = request.GET.get('token')
    if not token_str:
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token_str = auth_header[7:].strip()

    if not token_str:
        return HttpResponseForbidden("Authentication token required for SSE stream.")

    try:
        access_token = AccessToken(token_str)
        user_id = access_token['user_id']
    except (InvalidToken, TokenError, KeyError, Exception) as e:
        logger.debug(f"SSE Auth failed: {e}")
        return HttpResponseForbidden("Invalid or expired token.")

    try:
        import redis
        redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/1')
        r = redis.Redis.from_url(redis_url)
        pubsub = r.pubsub()
        pubsub.subscribe(f'user_notify_{user_id}')
    except Exception as e:
        logger.error(f"SSE Redis connection error: {e}")
        return HttpResponse("SSE Redis error", status=500)

    def event_stream():
        # 초기 연결 성공 이벤트
        yield f"event: connected\ndata: {json.dumps({'status': 'connected', 'user_id': user_id})}\n\n"
        last_ping = time.time()
        try:
            while True:
                message = pubsub.get_message(timeout=1.0)
                if message and message['type'] == 'message':
                    data = message['data']
                    if isinstance(data, bytes):
                        data = data.decode('utf-8')
                    yield f"event: notification\ndata: {data}\n\n"

                # 20초마다 Heartbeat Ping 패킷 전송 (프록시/브라우저 타임아웃 방지)
                now = time.time()
                if now - last_ping >= 20:
                    yield ": ping\n\n"
                    last_ping = now
        except GeneratorExit:
            logger.debug(f"SSE Client disconnected for user {user_id}")
        except Exception as e:
            logger.debug(f"SSE stream error for user {user_id}: {e}")
        finally:
            try:
                pubsub.unsubscribe(f'user_notify_{user_id}')
                pubsub.close()
            except Exception:
                pass

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache, no-transform'
    response['X-Accel-Buffering'] = 'no'
    return response
