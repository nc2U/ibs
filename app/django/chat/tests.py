from django.contrib.auth import get_user_model
from django.db import IntegrityError
from rest_framework import status
from rest_framework.test import APITestCase

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


