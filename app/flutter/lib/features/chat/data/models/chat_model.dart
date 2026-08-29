import '../../../../core/models/common_models.dart';

/// 대화방 유형
enum ChatRoomType {
  channel, // 워크스페이스 공용 채널
  group,   // 비공개 소그룹
  direct,  // 1:1 DM
}

/// 메시지 유형
enum ChatMessageType {
  text,
  image,
  file,
  issue,
  meeting,
  approval,
  system,
}

/// 대화방 모델
class ChatRoomModel {
  final int id;
  final int? project;
  final String? projectName;
  final ChatRoomType roomType;
  final String title;
  final String description;
  final int? createdBy;
  final DateTime created;
  final DateTime updated;
  final int memberCount;
  final List<SimpleUserModel> members;
  final ChatLastMessage? lastMessage;
  final int unreadCount;
  final bool isPinned;
  final bool isMuted;

  ChatRoomModel({
    required this.id,
    this.project,
    this.projectName,
    required this.roomType,
    required this.title,
    required this.description,
    this.createdBy,
    required this.created,
    required this.updated,
    required this.memberCount,
    required this.members,
    this.lastMessage,
    required this.unreadCount,
    required this.isPinned,
    required this.isMuted,
  });

  factory ChatRoomModel.fromJson(Map<String, dynamic> json) {
    ChatRoomType parseRoomType(String? type) {
      switch (type) {
        case 'direct':
          return ChatRoomType.direct;
        case 'group':
          return ChatRoomType.group;
        default:
          return ChatRoomType.channel;
      }
    }

    return ChatRoomModel(
      id: json['id'] as int,
      project: json['project'] as int?,
      projectName: json['project_name'] as String?,
      roomType: parseRoomType(json['room_type'] as String?),
      title: json['title'] as String? ?? '',
      description: json['description'] as String? ?? '',
      createdBy: json['created_by'] as int?,
      created: DateTime.parse(json['created'] as String),
      updated: DateTime.parse(json['updated'] as String),
      memberCount: json['member_count'] as int? ?? 0,
      members: (json['members'] as List<dynamic>?)
              ?.map((m) => SimpleUserModel.fromJson(m as Map<String, dynamic>))
              .toList() ??
          [],
      lastMessage: json['last_message'] != null
          ? ChatLastMessage.fromJson(json['last_message'] as Map<String, dynamic>)
          : null,
      unreadCount: json['unread_count'] as int? ?? 0,
      isPinned: json['is_pinned'] as bool? ?? false,
      isMuted: json['is_muted'] as bool? ?? false,
    );
  }

  /// 표시할 방 이름 (1:1 DM인 경우 상대방 이름 자동 반환)
  String getDisplayName(int currentUserId) {
    if (roomType == ChatRoomType.direct) {
      final other = members.firstWhere(
        (m) => m.pk != currentUserId,
        orElse: () => members.isNotEmpty
            ? members.first
            : const SimpleUserModel(pk: 0, username: '대화 상대'),
      );
      return other.name.isNotEmpty ? '${other.name} (${other.username})' : other.username;
    }
    if (title.isNotEmpty) return title;
    if (roomType == ChatRoomType.channel) {
      return '#${projectName ?? "공용 채널"}';
    }
    return '그룹 대화방';
  }
}

/// 최근 메시지 요약
class ChatLastMessage {
  final int id;
  final String senderName;
  final String messageType;
  final String content;
  final DateTime created;

  ChatLastMessage({
    required this.id,
    required this.senderName,
    required this.messageType,
    required this.content,
    required this.created,
  });

  factory ChatLastMessage.fromJson(Map<String, dynamic> json) {
    return ChatLastMessage(
      id: json['id'] as int,
      senderName: json['sender_name'] as String? ?? '',
      messageType: json['message_type'] as String? ?? 'text',
      content: json['content'] as String? ?? '',
      created: DateTime.parse(json['created'] as String),
    );
  }
}

/// 답장 원본 요약 모델
class ChatReplyDetail {
  final int id;
  final String senderName;
  final String content;
  final String messageType;

  ChatReplyDetail({
    required this.id,
    required this.senderName,
    required this.content,
    required this.messageType,
  });

  factory ChatReplyDetail.fromJson(Map<String, dynamic> json) {
    return ChatReplyDetail(
      id: json['id'] as int,
      senderName: json['sender_name'] as String? ?? '알 수 없음',
      content: json['content'] as String? ?? '',
      messageType: json['message_type'] as String? ?? 'text',
    );
  }
}

/// 개별 채팅 메시지 모델
class ChatMessageModel {
  final int id;
  final int roomId;
  final SimpleUserModel? sender;
  final ChatMessageType messageType;
  final String content;
  final String? file;
  final String fileName;
  final int fileSize;
  final int? refId;
  final String refTitle;
  final String refSub;
  final int? replyTo;
  final ChatReplyDetail? replyToDetail;
  final DateTime created;

  ChatMessageModel({
    required this.id,
    required this.roomId,
    this.sender,
    required this.messageType,
    required this.content,
    this.file,
    required this.fileName,
    required this.fileSize,
    this.refId,
    required this.refTitle,
    required this.refSub,
    this.replyTo,
    this.replyToDetail,
    required this.created,
  });

  factory ChatMessageModel.fromJson(Map<String, dynamic> json) {
    ChatMessageType parseMsgType(String? type) {
      switch (type) {
        case 'image':
          return ChatMessageType.image;
        case 'file':
          return ChatMessageType.file;
        case 'issue':
          return ChatMessageType.issue;
        case 'meeting':
          return ChatMessageType.meeting;
        case 'approval':
          return ChatMessageType.approval;
        case 'system':
          return ChatMessageType.system;
        default:
          return ChatMessageType.text;
      }
    }

    return ChatMessageModel(
      id: json['id'] as int,
      roomId: json['room'] is int ? json['room'] as int : (json['room_id'] as int? ?? 0),
      sender: json['sender'] != null
          ? SimpleUserModel.fromJson(json['sender'] as Map<String, dynamic>)
          : null,
      messageType: parseMsgType(json['message_type'] as String?),
      content: json['content'] as String? ?? '',
      file: json['file'] as String?,
      fileName: json['file_name'] as String? ?? '',
      fileSize: json['file_size'] as int? ?? 0,
      refId: json['ref_id'] as int?,
      refTitle: json['ref_title'] as String? ?? '',
      refSub: json['ref_sub'] as String? ?? '',
      replyTo: json['reply_to'] as int?,
      replyToDetail: json['reply_to_detail'] != null
          ? ChatReplyDetail.fromJson(json['reply_to_detail'] as Map<String, dynamic>)
          : null,
      created: DateTime.parse(json['created'] as String),
    );
  }
}
