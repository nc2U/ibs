from django.conf import settings
from django.db import models
from work.models import IssueProject


class ChatRoom(models.Model):
    """
    메신저 대화방 모델
    - channel: 워크스페이스 공용 공개 채널 (#전체대화방, #현장소통방 등)
    - group: 특정 멤버들만의 비공개 소그룹 채팅방
    - direct: 1:1 비밀 다이렉트 메시지 (DM)
    """
    ROOM_TYPE_CHOICES = (
        ('channel', '워크스페이스 공용 채널'),
        ('group', '비공개 그룹 채팅방'),
        ('direct', '1:1 다이렉트 메시지 (DM)'),
    )

    project = models.ForeignKey(
        IssueProject,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='chat_rooms',
        verbose_name='소속 워크스페이스',
        help_text='공용 채널인 경우 소속 워크스페이스 지정'
    )
    room_type = models.CharField('대화방 유형', max_length=20, choices=ROOM_TYPE_CHOICES, default='channel')
    title = models.CharField('대화방 이름', max_length=150, blank=True, default='')
    description = models.CharField('대화방 설명/주제', max_length=255, blank=True, default='')
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='ChatRoomMember',
        related_name='chat_rooms',
        verbose_name='참여 멤버'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_chat_rooms',
        verbose_name='개설자'
    )
    created = models.DateTimeField('개설일시', auto_now_add=True)
    updated = models.DateTimeField('최근 활동일시', auto_now=True)

    class Meta:
        db_table = 'chat_room'
        verbose_name = '대화방'
        verbose_name_plural = '01. 대화방 목록'
        ordering = ['-updated']

    def __str__(self):
        if self.room_type == 'channel':
            ws_name = self.project.name if self.project else '전사'
            return f"#{self.title or '일반'} ({ws_name})"
        return self.title or f"채팅방 #{self.pk}"


class ChatRoomMember(models.Model):
    """대화방 멤버십 & 알림/고정 설정"""
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_memberships')
    is_admin = models.BooleanField('방장/관리자', default=False)
    is_pinned = models.BooleanField('상단 고정', default=False)
    is_muted = models.BooleanField('알림 끄기', default=False)
    joined_at = models.DateTimeField('참여일시', auto_now_add=True)
    last_read_message_id = models.PositiveBigIntegerField('마지막 읽은 메시지 ID', default=0)

    class Meta:
        db_table = 'chat_room_member'
        verbose_name = '대화방 멤버'
        verbose_name_plural = '02. 대화방 멤버 관리'
        unique_together = ('room', 'user')

    def __str__(self):
        return f"{self.room.title} - {self.user.username}"


class ChatMessage(models.Model):
    """
    대화 메시지 모델
    - 일반 텍스트, 이미지, 첨부파일
    - IBS 특화 리치 링크 카드 (Issue 업무, 회의록 Meeting, 전자결재 Approval)
    """
    MESSAGE_TYPE_CHOICES = (
        ('text', '일반 텍스트'),
        ('image', '사진/이미지'),
        ('file', '문서/도면 파일'),
        ('issue', '업무(Issue) 공유 카드'),
        ('meeting', '회의록(Meeting) 공유 카드'),
        ('approval', '전자결재(Approval) 공유 카드'),
        ('system', '시스템 알림 메시지'),
    )

    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages', verbose_name='대화방')
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chat_messages',
        verbose_name='발신자'
    )
    message_type = models.CharField('메시지 유형', max_length=20, choices=MESSAGE_TYPE_CHOICES, default='text')
    content = models.TextField('메시지 내용', blank=True, default='')

    # 첨부파일/이미지
    file = models.FileField('첨부파일', upload_to='chat/files/%Y/%m/', null=True, blank=True)
    file_name = models.CharField('원본 파일명', max_length=255, blank=True, default='')
    file_size = models.PositiveIntegerField('파일 크기 (Byte)', default=0)

    # IBS 엔터프라이즈 리치 링크 연동 (FK 또는 ID 매핑)
    ref_id = models.PositiveIntegerField('연계 데이터 PK (Issue/Meeting/Approval)', null=True, blank=True)
    ref_title = models.CharField('연계 데이터 요약/제목', max_length=255, blank=True, default='')
    ref_sub = models.CharField('연계 데이터 상태/부가정보', max_length=100, blank=True, default='')

    # 답장(Reply) 연동
    reply_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name='답장 대상 메시지'
    )

    created = models.DateTimeField('전송일시', auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'chat_message'
        verbose_name = '채팅 메시지'
        verbose_name_plural = '03. 채팅 메시지 내역'
        ordering = ['created']

    def __str__(self):
        sender_name = self.sender.username if self.sender else '시스템'
        return f"[{self.room.title}] {sender_name}: {self.content[:30]}"
