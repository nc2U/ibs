from django.contrib.auth import get_user_model
from django.db import IntegrityError
from rest_framework import status
from rest_framework.test import APITestCase, APITransactionTestCase

from company.models import Company
from chat.models import ChatRoom
from work.models.project import IssueProject, Member

User = get_user_model()


class ChatRoomAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='chat_user', password='password123')
        self.company = Company.objects.create(name='(주)대영아이비에스')
        self.project = IssueProject.objects.create(
            company=self.company,
            name='채팅 테스트 워크스페이스',
            slug='chat-ws',
            status='1',
            chat_channel_enabled=True,
            creator=self.user
        )
        Member.objects.create(project=self.project, user=self.user)

    def test_list_and_total_unread_chat_rooms(self):
        self.client.force_authenticate(user=self.user)

        # 1) 최초 조회 시 공용 채널 자동 생성 검증
        res_list = self.client.get('/api/v1/chat-room/')
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)

        # 2) total-unread 호출 시 정상 200 반환 검증 (500 에러 재발 방지)
        res_unread = self.client.get('/api/v1/chat-room/total-unread/')
        self.assertEqual(res_unread.status_code, status.HTTP_200_OK)
        self.assertIn('total_unread', res_unread.data)

        # 3) 연속 호출 시에도 안전하게 단일 채널 유지 및 200 반환
        res_list_again = self.client.get('/api/v1/chat-room/')
        self.assertEqual(res_list_again.status_code, status.HTTP_200_OK)
        self.assertEqual(
            ChatRoom.objects.filter(project=self.project, room_type='channel').count(),
            1
        )

    def test_unique_project_channel_constraint(self):
        # 동일 프로젝트에 room_type='channel' 중복 생성 시 IntegrityError 발생 검증
        ChatRoom.objects.create(
            project=self.project,
            room_type='channel',
            title='채널 1'
        )
        with self.assertRaises(IntegrityError):
            ChatRoom.objects.create(
                project=self.project,
                room_type='channel',
                title='채널 2'
            )

    def test_get_or_create_self_chat(self):
        self.client.force_authenticate(user=self.user)

        # 1) 최초 조회 시 '나와의 채팅' 생성 (201 Created)
        res = self.client.get('/api/v1/chat-room/get-or-create-self/')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['room_type'], 'self')
        self.assertEqual(res.data['title'], '나와의 채팅')
        self.assertTrue(res.data['is_pinned'])

        room_id = res.data['id']

        # 2) 재호출 시 동일 방 반환 (200 OK)
        res_again = self.client.post('/api/v1/chat-room/get-or-create-self/')
        self.assertEqual(res_again.status_code, status.HTTP_200_OK)
        self.assertEqual(res_again.data['id'], room_id)

        # 3) 자기 자신을 대상으로 DM 생성 시 나와의 채팅으로 연결
        res_dm = self.client.post('/api/v1/chat-room/get-or-create-dm/', {'target_user_id': self.user.pk})
        self.assertEqual(res_dm.status_code, status.HTTP_200_OK)
        self.assertEqual(res_dm.data['id'], room_id)

        # 4) 나와의 채팅방은 나가기(leave) 불가 검증
        res_leave = self.client.post(f'/api/v1/chat-room/{room_id}/leave/')
        self.assertEqual(res_leave.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unique_user_self_chat_constraint(self):
        ChatRoom.objects.create(
            created_by=self.user,
            room_type='self',
            title='나와의 채팅 1'
        )
        with self.assertRaises(IntegrityError):
            ChatRoom.objects.create(
                created_by=self.user,
                room_type='self',
                title='나와의 채팅 2'
            )


class ChatMessageAPITests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', email='user1@test.com', password='password123')
        self.user2 = User.objects.create_user(username='user2', email='user2@test.com', password='password123')
        self.superuser = User.objects.create_superuser(username='super', email='super@test.com', password='password123')

        self.company = Company.objects.create(name='(주)대영아이비에스')
        self.project = IssueProject.objects.create(
            company=self.company,
            name='채팅 워크스페이스',
            slug='chat-ws-2',
            status='1',
            chat_channel_enabled=True,
            creator=self.user1
        )
        Member.objects.create(project=self.project, user=self.user1)
        Member.objects.create(project=self.project, user=self.user2)

        from chat.models import ChatRoomMember, ChatMessage
        self.room = ChatRoom.objects.create(
            project=self.project,
            room_type='group',
            title='테스트 대화방',
            created_by=self.user1
        )
        ChatRoomMember.objects.create(room=self.room, user=self.user1, is_admin=True)
        ChatRoomMember.objects.create(room=self.room, user=self.user2, is_admin=False)

        self.msg1 = ChatMessage.objects.create(
            room=self.room,
            sender=self.user1,
            content='user1이 보낸 메시지'
        )
        self.msg2 = ChatMessage.objects.create(
            room=self.room,
            sender=self.user2,
            content='user2가 보낸 메시지'
        )

    def test_delete_own_message(self):
        """자신이 작성한 메시지 삭제 성공 검증"""
        self.client.force_authenticate(user=self.user1)
        res = self.client.delete(f'/api/v1/chat-message/{self.msg1.id}/')
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        from chat.models import ChatMessage
        self.assertFalse(ChatMessage.objects.filter(id=self.msg1.id).exists())

    def test_delete_other_user_message_forbidden(self):
        """타인이 작성한 메시지를 일반 멤버가 삭제 시도 시 403 차단 검증"""
        self.client.force_authenticate(user=self.user2)
        res = self.client.delete(f'/api/v1/chat-message/{self.msg1.id}/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        from chat.models import ChatMessage
        self.assertTrue(ChatMessage.objects.filter(id=self.msg1.id).exists())

    def test_non_author_cannot_delete_even_if_admin(self):
        """방 관리자라도 타인이 작성한 메시지는 삭제할 수 없음(403 차단) 검증"""
        # 방 관리자(user1)가 user2의 메시지 삭제 시도 -> 403 차단
        self.client.force_authenticate(user=self.user1)
        res = self.client.delete(f'/api/v1/chat-message/{self.msg2.id}/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        from chat.models import ChatMessage
        self.assertTrue(ChatMessage.objects.filter(id=self.msg2.id).exists())

    def test_direct_chat_smart_delete(self):
        """1:1 대화방: 상대방이 안 읽었으면 완전 삭제, 이미 읽었으면 소프트 삭제 검증"""
        from chat.models import ChatRoom, ChatRoomMember, ChatMessage
        direct_room = ChatRoom.objects.create(room_type='direct', created_by=self.user1)
        m1 = ChatRoomMember.objects.create(room=direct_room, user=self.user1, last_read_message_id=0)
        m2 = ChatRoomMember.objects.create(room=direct_room, user=self.user2, last_read_message_id=0)

        # 1) 상대방이 아직 안 읽은 메시지 -> 완전 삭제
        msg_unread = ChatMessage.objects.create(room=direct_room, sender=self.user1, content='안 읽은 메시지')
        self.client.force_authenticate(user=self.user1)
        res1 = self.client.delete(f'/api/v1/chat-message/{msg_unread.id}/')
        self.assertEqual(res1.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ChatMessage.objects.filter(id=msg_unread.id).exists())

        # 2) 상대방이 이미 읽은 메시지 -> 소프트 삭제
        msg_read = ChatMessage.objects.create(room=direct_room, sender=self.user1, content='이미 읽은 메시지')
        m2.last_read_message_id = msg_read.id
        m2.save()

        res2 = self.client.delete(f'/api/v1/chat-message/{msg_read.id}/')
        self.assertEqual(res2.status_code, status.HTTP_204_NO_CONTENT)
        msg_after = ChatMessage.objects.get(id=msg_read.id)
        self.assertTrue(msg_after.is_deleted)
        self.assertEqual(msg_after.content, '삭제된 메시지입니다.')

        # 3) 조회 시 serializer도 정상 처리 검증
        res_list = self.client.get(f'/api/v1/chat-message/?room={direct_room.id}')
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        found = [m for m in res_list.data['results'] if m['id'] == msg_read.id]
        self.assertEqual(len(found), 1)
        self.assertTrue(found[0]['is_deleted'])
        self.assertEqual(found[0]['content'], '삭제된 메시지입니다.')

    def test_post_message_to_unauthorized_room_forbidden(self):
        """참여하지 않은 비공개 대화방에 메시지 등록 시도 시 403 차단 (IDOR 방어) 검증"""
        # user3 생성 (어떤 방에도 속하지 않음)
        user3 = User.objects.create_user(username='user3', email='user3@test.com', password='password123')
        self.client.force_authenticate(user=user3)

        payload = {
            'room': self.room.id,
            'content': '허가되지 않은 접근 시도',
            'message_type': 'text',
        }
        res = self.client.post('/api/v1/chat-message/', payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_cross_room_reply_to_prevention(self):
        """다른 대화방의 메시지 ID를 reply_to로 지정 시 타 방 메시지가 노출되지 않도록 방어 검증"""
        from chat.models import ChatRoom, ChatRoomMember, ChatMessage

        # 별도의 비밀 대화방 및 비밀 메시지 생성
        secret_room = ChatRoom.objects.create(room_type='group', title='기밀 회의방', created_by=self.user2)
        ChatRoomMember.objects.create(room=secret_room, user=self.user2, is_admin=True)
        secret_msg = ChatMessage.objects.create(
            room=secret_room,
            sender=self.user2,
            content='비밀 기밀 메시지 내용'
        )

        # user1이 자신이 속한 self.room에 메시지를 작성하면서 비밀 메시지를 reply_to로 전송
        self.client.force_authenticate(user=self.user1)
        payload = {
            'room': self.room.id,
            'content': '일반 메시지',
            'message_type': 'text',
            'reply_to': secret_msg.id,
        }
        res = self.client.post('/api/v1/chat-message/', payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # 저장된 메시지는 reply_to가 없어야 함 (또는 serializer에서 reply_to_detail이 None)
        msg_id = res.data['id']
        msg_created = ChatMessage.objects.get(id=msg_id)
        self.assertIsNone(msg_created.reply_to)
        self.assertIsNone(res.data['reply_to_detail'])



    def test_chat_message_file_cleanup_on_delete(self):
        """ChatMessage 삭제 시 첨부파일이 스토리지에서 자동 삭제되는지 검증"""
        from django.core.files.base import ContentFile
        from django.core.files.storage import default_storage
        from chat.models import ChatMessage

        msg = ChatMessage.objects.create(
            room=self.room,
            sender=self.user1,
            message_type='file',
            content='파일 메시지',
            file_name='test_file.txt',
        )
        msg.file.save('test_chat_file.txt', ContentFile(b'chat attachment data'))
        msg.save()

        file_path = msg.file.name
        self.assertTrue(default_storage.exists(file_path))

        # 메시지 삭제 (on_commit 콜백 실행 트리거)
        with self.captureOnCommitCallbacks(execute=True):
            msg.delete()

        # 스토리지 파일 삭제 검증
        self.assertFalse(default_storage.exists(file_path))

    def test_chat_room_cascade_file_cleanup(self):
        """ChatRoom 삭제(CASCADE) 시 포함된 메시지의 첨부파일도 스토리지에서 자동 삭제되는지 검증"""
        from django.core.files.base import ContentFile
        from django.core.files.storage import default_storage
        from chat.models import ChatMessage

        msg = ChatMessage.objects.create(
            room=self.room,
            sender=self.user1,
            message_type='file',
            content='대화방 파일 메시지',
            file_name='room_file.txt',
        )
        msg.file.save('room_file.txt', ContentFile(b'room cascade test data'))
        msg.save()

        file_path = msg.file.name
        self.assertTrue(default_storage.exists(file_path))

        # 방 삭제 시 CASCADE로 메시지 및 파일 자동 정리 (on_commit 콜백 실행 트리거)
        with self.captureOnCommitCallbacks(execute=True):
            self.room.delete()

        self.assertFalse(default_storage.exists(file_path))

    def test_cursor_pagination_invalid_param_safe(self):
        """커서 페이지네이션에 비정상 문자열 before_id/after_id 전달 시 500 에러 없이 200 반환 검증"""
        self.client.force_authenticate(user=self.user1)

        # 1. before_id가 숫자가 아닌 경우
        res1 = self.client.get(f'/api/v1/chat-message/?room={self.room.id}&before_id=abc')
        self.assertEqual(res1.status_code, status.HTTP_200_OK)

        # 2. after_id가 숫자가 아닌 경우
        res2 = self.client.get(f'/api/v1/chat-message/?room={self.room.id}&after_id=xyz')
        self.assertEqual(res2.status_code, status.HTTP_200_OK)

    def test_message_update_blocked_method_not_allowed(self):
        """[T-MSG-NO-EDIT] 메신저 메시지는 PUT / PATCH 임의 수정 불가(405 차단) 검증"""
        self.client.force_authenticate(user=self.user1)
        res_put = self.client.put(f'/api/v1/chat-message/{self.msg1.id}/', {'content': '변조된 내용'})
        self.assertEqual(res_put.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        res_patch = self.client.patch(f'/api/v1/chat-message/{self.msg1.id}/', {'content': '변조된 내용'})
        self.assertEqual(res_patch.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_file_upload_size_limit(self):
        """[T-FILE-LIMIT] 50MB 초과 첨부파일 업로드 시 400 ValidationError 차단 검증"""
        from unittest.mock import patch, PropertyMock
        from django.core.files.uploadedfile import UploadedFile, SimpleUploadedFile
        self.client.force_authenticate(user=self.user1)
        big_file = SimpleUploadedFile('huge.bin', b'mock content')

        with patch.object(UploadedFile, 'size', new_callable=PropertyMock) as mock_size:
            mock_size.return_value = 51 * 1024 * 1024
            res = self.client.post('/api/v1/chat-message/', {
                'room': self.room.id,
                'message_type': 'file',
                'file': big_file,
                'file_name': 'huge.bin',
            }, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('file', res.data)

    def test_superuser_privacy_isolation_in_message_endpoints(self):
        """슈퍼유저라도 비참여 1:1 DM, 나와의 채팅, 비공개 그룹방 메시지 열람·검색·맥락·파일·전송 차단 검증"""
        from chat.models import ChatRoom, ChatRoomMember, ChatMessage

        dm_room = ChatRoom.objects.create(room_type='direct', created_by=self.user1)
        ChatRoomMember.objects.create(room=dm_room, user=self.user1)
        ChatRoomMember.objects.create(room=dm_room, user=self.user2)
        secret_dm_msg = ChatMessage.objects.create(
            room=dm_room,
            sender=self.user1,
            content='절대 노출되면 안 되는 1:1 기밀 대화',
        )

        self.client.force_authenticate(user=self.superuser)

        # 1) 목록 조회 (?room=dm_room.id) -> 빈 결과
        res_list = self.client.get(f'/api/v1/chat-message/?room={dm_room.id}')
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_list.data['results']), 0)

        # 2) 단건 상세 조회 -> 404
        res_detail = self.client.get(f'/api/v1/chat-message/{secret_dm_msg.id}/')
        self.assertEqual(res_detail.status_code, status.HTTP_404_NOT_FOUND)

        # 3) 통합 검색 -> 검색 결과 0건
        res_search = self.client.get('/api/v1/chat-message/search/?q=기밀')
        self.assertEqual(res_search.status_code, status.HTTP_200_OK)
        self.assertEqual(res_search.data['count'], 0)

        # 4) 전후 맥락(context) 조회 -> 403
        res_ctx = self.client.get(f'/api/v1/chat-message/context/?message_id={secret_dm_msg.id}')
        self.assertEqual(res_ctx.status_code, status.HTTP_403_FORBIDDEN)

        # 5) 파일 서랍(files) 조회 -> 403
        res_files = self.client.get(f'/api/v1/chat-message/files/?room={dm_room.id}')
        self.assertEqual(res_files.status_code, status.HTTP_403_FORBIDDEN)

        # 6) 비참여 1:1 DM 방에 메시지 작성 시도 -> 403
        res_post = self.client.post('/api/v1/chat-message/', {
            'room': dm_room.id,
            'content': '슈퍼유저 개입 시도',
            'message_type': 'text',
        })
        self.assertEqual(res_post.status_code, status.HTTP_403_FORBIDDEN)

    def test_chat_message_admin_masked_content_hides_plaintext(self):
        """Django Admin 목록에서 1:1 DM 및 나와의 채팅 원문이 평문 노출되지 않고 마스킹되는지 검증"""
        from django.contrib.admin.sites import AdminSite
        from chat.admin import ChatMessageAdmin
        from chat.models import ChatRoom, ChatMessage

        dm_room = ChatRoom.objects.create(room_type='direct', created_by=self.user1)
        secret_msg = ChatMessage.objects.create(
            room=dm_room,
            sender=self.user1,
            content='비밀번호는 123456입니다',
        )
        admin_inst = ChatMessageAdmin(ChatMessage, AdminSite())
        rendered = str(admin_inst.masked_content(secret_msg))
        self.assertNotIn('비밀번호는 123456입니다', rendered)
        self.assertIn('사생활 보호 마스킹 처리됨', rendered)

    def test_chat_room_destroy_and_update_permissions(self):
        """공용 채널/DM 임의 삭제 차단 및 그룹방 관리자 권한 검증"""
        from chat.models import ChatRoom

        channel_room = ChatRoom.objects.create(
            project=self.project,
            room_type='channel',
            title=self.project.name,
            created_by=self.user1,
        )

        # 1) 워크스페이스 일반 멤버나 방장이라도 공용 채널(channel)은 DELETE 불가 (403)
        self.client.force_authenticate(user=self.user1)
        res_del_channel = self.client.delete(f'/api/v1/chat-room/{channel_room.id}/')
        self.assertEqual(res_del_channel.status_code, status.HTTP_403_FORBIDDEN)

        # 2) 그룹방 일반 멤버(user2)는 그룹방 수정/삭제 불가 (403)
        self.client.force_authenticate(user=self.user2)
        res_patch_non_admin = self.client.patch(f'/api/v1/chat-room/{self.room.id}/', {'title': '임의 변경'})
        self.assertEqual(res_patch_non_admin.status_code, status.HTTP_403_FORBIDDEN)
        res_del_non_admin = self.client.delete(f'/api/v1/chat-room/{self.room.id}/')
        self.assertEqual(res_del_non_admin.status_code, status.HTTP_403_FORBIDDEN)

        # 3) 그룹방 관리자(user1)도 room_type 변조는 불가 (400), 제목 수정 및 삭제는 가능
        self.client.force_authenticate(user=self.user1)
        res_mutate_type = self.client.patch(f'/api/v1/chat-room/{self.room.id}/', {'room_type': 'channel'})
        self.assertEqual(res_mutate_type.status_code, status.HTTP_400_BAD_REQUEST)

        res_patch_admin = self.client.patch(f'/api/v1/chat-room/{self.room.id}/', {'title': '정상 변경'})
        self.assertEqual(res_patch_admin.status_code, status.HTTP_200_OK)

        # 4) 일반 create 엔드포인트로 direct/self 방 직접 생성 시도 차단 (400)
        res_create_direct = self.client.post('/api/v1/chat-room/', {'room_type': 'direct', 'title': '불법 DM'})
        self.assertEqual(res_create_direct.status_code, status.HTTP_400_BAD_REQUEST)

    def test_soft_deleted_messages_excluded_from_unread_counts(self):
        """소프트 삭제된 메시지(is_deleted=True)가 미읽음 배지 카운트에 합산되지 않는지 검증"""
        from chat.models import ChatMessage

        # 현재 user2 기준 안 읽은 메시지는 msg1 (1개)
        self.client.force_authenticate(user=self.user2)
        res_before = self.client.get('/api/v1/chat-room/total-unread/')
        self.assertEqual(res_before.data['total_unread'], 1)

        # 소프트 삭제된 메시지 추가 생성
        ChatMessage.objects.create(
            room=self.room,
            sender=self.user1,
            content='삭제된 메시지입니다.',
            is_deleted=True,
        )

        res_after = self.client.get('/api/v1/chat-room/total-unread/')
        self.assertEqual(res_after.data['total_unread'], 1)

        res_rooms = self.client.get('/api/v1/chat-room/')
        target_room_data = next(r for r in res_rooms.data if r['id'] == self.room.id)
        self.assertEqual(target_room_data['unread_count'], 1)

    def test_system_message_spoofing_and_invalid_params_blocked(self):
        """시스템 메시지 사칭 차단, 비정상 쿼리 파라미터 방어 및 워크스페이스 이름 변경 시그널 동기화 검증"""
        from chat.models import ChatRoom

        self.client.force_authenticate(user=self.user1)

        # 1) message_type='system' 사칭 전송 차단 (400)
        res_sys = self.client.post('/api/v1/chat-message/', {
            'room': self.room.id,
            'content': '관리자 사칭 공지',
            'message_type': 'system',
        })
        self.assertEqual(res_sys.status_code, status.HTTP_400_BAD_REQUEST)

        # 2) 비정상 쿼리 파라미터 방어 (500 에러 없이 200/400 반환)
        self.assertEqual(self.client.get('/api/v1/chat-message/?room=invalid').status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get('/api/v1/chat-message/search/?q=test&room=invalid').status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get('/api/v1/chat-message/context/?message_id=invalid').status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.client.get('/api/v1/chat-message/files/?room=invalid').status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            self.client.post(f'/api/v1/chat-room/{self.room.id}/read/', {'last_message_id': 'invalid'}).status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        # 3) 워크스페이스 이름 변경 시 공용 채널 제목 자동 동기화 검증
        channel_room = ChatRoom.objects.create(
            project=self.project,
            room_type='channel',
            title=self.project.name,
            created_by=self.user1,
        )
        self.project.name = '변경된 워크스페이스명'
        self.project.save()
        channel_room.refresh_from_db()
        self.assertEqual(channel_room.title, '변경된 워크스페이스명')


class ChatWebSocketAPITests(APITransactionTestCase):
    """WebSocket Consumer 및 Middleware 비동기 스레드 통합 테스트"""

    def setUp(self):
        self.user1 = User.objects.create_user(username='ws_user1', email='ws_user1@example.com', password='password123')
        self.user2 = User.objects.create_user(username='ws_user2', email='ws_user2@example.com', password='password123')

    def test_superuser_cannot_access_private_dm_websocket(self):
        """[T-WS-PRIVACY] 최고관리자라도 비참여 1:1 비밀 대화방(direct) 웹소켓 접속 불가 검증"""
        from asgiref.sync import async_to_sync
        from chat.models import ChatRoom, ChatRoomMember
        from chat.consumers import ChatConsumer
        admin_user = User.objects.create_superuser(username='super_admin', email='super@example.com', password='password123')
        direct_room = ChatRoom.objects.create(room_type='direct', created_by=self.user1)
        ChatRoomMember.objects.create(room=direct_room, user=self.user1)
        ChatRoomMember.objects.create(room=direct_room, user=self.user2)

        consumer = ChatConsumer()
        can_access = async_to_sync(consumer.check_room_access)(direct_room.id, admin_user)
        self.assertFalse(can_access)

        # 본인이 참여한 멤버(user1)는 정상 접근 가능
        can_access_member = async_to_sync(consumer.check_room_access)(direct_room.id, self.user1)
        self.assertTrue(can_access_member)

    def test_websocket_kicked_user_cannot_send_or_rejoin(self):
        """대화방에서 퇴장/제외된 사용자가 기존 WebSocket으로 메시지 전송 시 자동 재등록되지 않고 차단되는지 검증"""
        from asgiref.sync import async_to_sync
        from chat.models import ChatRoom, ChatRoomMember
        from chat.consumers import ChatConsumer

        group_room = ChatRoom.objects.create(room_type='group', title='그룹방', created_by=self.user1)
        ChatRoomMember.objects.create(room=group_room, user=self.user1, is_admin=True)
        m2 = ChatRoomMember.objects.create(room=group_room, user=self.user2)

        # user2가 방에서 나감 (멤버십 삭제)
        m2.delete()

        consumer = ChatConsumer()
        with self.assertRaises(PermissionError):
            async_to_sync(consumer.save_message)(
                room_id=group_room.id,
                user=self.user2,
                content='퇴장 후 몰래 전송',
                message_type='text',
                ref_id=None,
                ref_title='',
                ref_sub='',
                reply_to_id=None,
            )

        self.assertFalse(ChatRoomMember.objects.filter(room=group_room, user=self.user2).exists())

    def test_websocket_header_jwt_auth(self):
        """[T-WS-HEADER-AUTH] Authorization: Bearer <token> 헤더 기반 WebSocket 인증 지원 검증"""
        from asgiref.sync import async_to_sync
        from rest_framework_simplejwt.tokens import RefreshToken
        from chat.middleware import JWTAuthMiddleware

        refresh = RefreshToken.for_user(self.user1)
        access_token = str(refresh.access_token)

        scope = {
            'type': 'websocket',
            'query_string': b'',
            'headers': [
                (b'authorization', f'Bearer {access_token}'.encode('utf-8'))
            ],
        }

        async def dummy_app(scope, receive, send):
            return scope.get('user')

        middleware = JWTAuthMiddleware(dummy_app)
        user = async_to_sync(middleware)(scope, None, None)
        self.assertEqual(user, self.user1)
