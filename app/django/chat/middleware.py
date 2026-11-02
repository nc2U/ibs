from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from accounts.models import User


@database_sync_to_async
def get_user_from_jwt(token_string):
    try:
        access_token = AccessToken(token_string)
        user_id = access_token['user_id']
        user = User.objects.filter(id=user_id, is_active=True).first()
        return user or AnonymousUser()
    except Exception:
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    WebSocket 연결 시 Query Parameter(?token=<JWT>) 또는 Header로 전달된 JWT 인증
    """
    async def __call__(self, scope, receive, send):
        token = None

        # 1. Query parameter 파싱
        query_string = scope.get('query_string', b'').decode('utf-8')
        if query_string:
            query_params = parse_qs(query_string)
            token = query_params.get('token', [None])[0]

        # 2. Header 파싱 (Authorization: Bearer <token> 또는 Sec-WebSocket-Protocol)
        if not token:
            headers = dict(scope.get('headers', []))
            auth_header = headers.get(b'authorization', b'').decode('utf-8')
            if auth_header.startswith('Bearer '):
                token = auth_header.split('Bearer ', 1)[1].strip()
            elif b'sec-websocket-protocol' in headers:
                protocols = [p.strip() for p in headers[b'sec-websocket-protocol'].decode('utf-8').split(',')]
                if protocols:
                    token = protocols[0]

        if token:
            scope['user'] = await get_user_from_jwt(token)
        else:
            scope['user'] = AnonymousUser()

        return await super().__call__(scope, receive, send)
