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
