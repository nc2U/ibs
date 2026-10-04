import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import '../../../../core/providers/dio_provider.dart';
import 'models/chat_model.dart';

final chatRepositoryProvider = Provider<ChatRepository>((ref) {
  final dio = ref.watch(dioProvider);
  return ChatRepository(dio);
});

class ChatRepository {
  final Dio _dio;

  ChatRepository(this._dio);

  /// 1. 대화방 목록 조회
  Future<List<ChatRoomModel>> fetchChatRooms() async {
    final response = await _dio.get('/api/v1/chat-room/');
    final dynamic data = response.data;

    List<dynamic> list = [];
    if (data is List) {
      list = data;
    } else if (data is Map<String, dynamic> && data['results'] is List) {
      list = data['results'] as List<dynamic>;
    }

    return list.map((json) => ChatRoomModel.fromJson(json as Map<String, dynamic>)).toList();
  }

  /// 2. 특정 사용자와의 1:1 DM 방 조회 또는 생성
  Future<ChatRoomModel> getOrCreateDm(int targetUserId) async {
    final response = await _dio.post(
      '/api/v1/chat-room/get-or-create-dm/',
      data: {'target_user_id': targetUserId},
    );
    return ChatRoomModel.fromJson(response.data as Map<String, dynamic>);
  }

  /// 2-1. 나와의 채팅(개인 메모/보관함) 방 조회 또는 생성
  Future<ChatRoomModel> getOrCreateSelf() async {
    final response = await _dio.get('/api/v1/chat-room/get-or-create-self/');
    return ChatRoomModel.fromJson(response.data as Map<String, dynamic>);
  }

  /// 3. 대화방 메시지 내역 조회 (REST API, 커서 페이지네이션)
  /// - 기본: 최신 N개 / [beforeId]: 해당 ID 이전 메시지 / [afterId]: 해당 ID 이후 메시지
  /// - 반환 메시지는 항상 오래된 순 → 최신 순 정렬
  Future<({List<ChatMessageModel> messages, bool hasMore})> fetchMessagePage(
    int roomId, {
    int? beforeId,
    int? afterId,
  }) async {
    final response = await _dio.get(
      '/api/v1/chat-message/',
      queryParameters: {
        'room': roomId,
        if (beforeId != null) 'before_id': beforeId,
        if (beforeId == null && afterId != null) 'after_id': afterId,
      },
    );
    final dynamic data = response.data;

    List<dynamic> list = [];
    bool hasMore = false;
    if (data is List) {
      list = data;
    } else if (data is Map<String, dynamic>) {
      if (data['results'] is List) list = data['results'] as List<dynamic>;
      hasMore = data['has_more'] as bool? ?? false;
    }

    final messages = list
        .map((json) => ChatMessageModel.fromJson(json as Map<String, dynamic>))
        .toList();
    return (messages: messages, hasMore: hasMore);
  }

  /// 3-1. 최신 메시지 한 페이지 조회 (기존 호환)
  Future<List<ChatMessageModel>> fetchMessages(int roomId) async {
    return (await fetchMessagePage(roomId)).messages;
  }

  /// 4. 메시지 읽음 처리
  Future<void> markAsRead(int roomId, {int? lastMessageId}) async {
    await _dio.post(
      '/api/v1/chat-room/$roomId/read/',
      data: lastMessageId != null ? {'last_message_id': lastMessageId} : {},
    );
  }

  /// 5. 전체 미확인 메시지 총합 조회 (상단 앱바 배지용)
  Future<int> fetchTotalUnread() async {
    try {
      final response = await _dio.get('/api/v1/chat-room/total-unread/');
      if (response.data is Map<String, dynamic>) {
        return response.data['total_unread'] as int? ?? 0;
      }
      return 0;
    } catch (_) {
      return 0;
    }
  }

  /// 6. 사진/파일 바이트 첨부 전송 (REST API 멀티파트 - Web 및 모바일 100% 호환)
  Future<ChatMessageModel> sendFileBytesMessage({
    required int roomId,
    required List<int> fileBytes,
    required String fileName,
    required String messageType,
    String? content,
    int? fileSize,
    int? replyToId,
  }) async {
    final size = fileSize ?? fileBytes.length;
    final formData = FormData.fromMap({
      'room': roomId,
      'message_type': messageType,
      'content': content ?? '',
      'file': MultipartFile.fromBytes(fileBytes, filename: fileName),
      'file_name': fileName,
      'file_size': size,
      if (replyToId != null) 'reply_to': replyToId,
    });

    final response = await _dio.post('/api/v1/chat-message/', data: formData);
    return ChatMessageModel.fromJson(response.data as Map<String, dynamic>);
  }

  /// 6-1. XFile 기반 사진/문서 첨부 전송 헬퍼
  Future<ChatMessageModel> sendXFileMessage({
    required int roomId,
    required XFile file,
    required String messageType,
    String? content,
    int? replyToId,
  }) async {
    final bytes = await file.readAsBytes();
    final length = await file.length();
    return sendFileBytesMessage(
      roomId: roomId,
      fileBytes: bytes,
      fileName: file.name,
      messageType: messageType,
      content: content,
      fileSize: length,
      replyToId: replyToId,
    );
  }

  /// 6-3. 기존 호환용 다목적 파일 전송 (File, XFile 등 지원)
  Future<ChatMessageModel> sendFileMessage({
    required int roomId,
    required dynamic file,
    required String messageType,
    String? content,
    int? replyToId,
  }) async {
    if (file is XFile) {
      return sendXFileMessage(
        roomId: roomId,
        file: file,
        messageType: messageType,
        content: content,
        replyToId: replyToId,
      );
    }
    // dart:io File 또는 duck-typed 파일 객체
    final bytes = await (file.readAsBytes() as Future<List<int>>);
    String fileName = 'file';
    try {
      fileName = file.name as String;
    } catch (_) {
      try {
        fileName = (file.path as String).split(RegExp(r'[/\\]')).last;
      } catch (_) {}
    }
    int? size;
    try {
      size = await (file.length() as Future<int>);
    } catch (_) {
      size = bytes.length;
    }

    return sendFileBytesMessage(
      roomId: roomId,
      fileBytes: bytes,
      fileName: fileName,
      messageType: messageType,
      content: content,
      fileSize: size,
      replyToId: replyToId,
    );
  }

  /// 6-2. 텍스트/링크 메시지 전송 (REST API 백업)
  Future<ChatMessageModel> sendTextMessage({
    required int roomId,
    required String content,
    String messageType = 'text',
    int? refId,
    String? refTitle,
    String? refSub,
    int? replyToId,
  }) async {
    final data = <String, dynamic>{
      'room': roomId,
      'message_type': messageType,
      'content': content,
    };
    if (refId != null) data['ref_id'] = refId;
    if (refTitle != null && refTitle.isNotEmpty) data['ref_title'] = refTitle;
    if (refSub != null && refSub.isNotEmpty) data['ref_sub'] = refSub;
    if (replyToId != null) {
      data['reply_to'] = replyToId;
      data['reply_to_id'] = replyToId;
    }

    final response = await _dio.post('/api/v1/chat-message/', data: data);
    return ChatMessageModel.fromJson(response.data as Map<String, dynamic>);
  }

  /// 7. 대화방 나가기 / 목록에서 숨기기
  Future<void> leaveRoom(int roomId) async {
    await _dio.post('/api/v1/chat-room/$roomId/leave/');
  }

  /// 8. 메시지/파일 삭제
  Future<void> deleteMessage(int messageId, {int? roomId}) async {
    await _dio.delete(
      '/api/v1/chat-message/$messageId/',
      queryParameters: roomId != null ? {'room': roomId} : null,
    );
  }

  /// 9. 메시지 & 파일 통합/방내 검색
  Future<Map<String, dynamic>> searchMessages({
    required String query,
    int? roomId,
    String type = 'all',
    int page = 1,
    int pageSize = 30,
  }) async {
    final response = await _dio.get(
      '/api/v1/chat-message/search/',
      queryParameters: {
        'q': query,
        if (roomId != null) 'room': roomId,
        'type': type,
        'page': page,
        'page_size': pageSize,
      },
    );
    final data = response.data as Map<String, dynamic>;
    final results = (data['results'] as List<dynamic>? ?? [])
        .map((j) => ChatMessageModel.fromJson(j as Map<String, dynamic>))
        .toList();
    return {
      'count': data['count'] as int? ?? 0,
      'page': data['page'] as int? ?? page,
      'has_more': data['has_more'] as bool? ?? false,
      'results': results,
    };
  }

  /// 10. 타깃 메시지 전후 맥락(Context) 메시지 조회
  Future<List<ChatMessageModel>> fetchMessageContext(int messageId, {int limit = 15}) async {
    final response = await _dio.get(
      '/api/v1/chat-message/context/',
      queryParameters: {
        'message_id': messageId,
        'limit': limit,
      },
    );
    final data = response.data as Map<String, dynamic>;
    final results = (data['results'] as List<dynamic>? ?? [])
        .map((j) => ChatMessageModel.fromJson(j as Map<String, dynamic>))
        .toList();
    return results;
  }

  /// 11. 대화방 영구 보존 파일/미디어/링크 모아보기 서랍
  Future<Map<String, dynamic>> fetchChatFiles({
    required int roomId,
    String tab = 'all',
    int page = 1,
    int pageSize = 30,
  }) async {
    final response = await _dio.get(
      '/api/v1/chat-message/files/',
      queryParameters: {
        'room': roomId,
        'tab': tab,
        'page': page,
        'page_size': pageSize,
      },
    );
    final data = response.data as Map<String, dynamic>;
    final results = (data['results'] as List<dynamic>? ?? [])
        .map((j) => ChatMessageModel.fromJson(j as Map<String, dynamic>))
        .toList();
    return {
      'count': data['count'] as int? ?? 0,
      'page': data['page'] as int? ?? page,
      'has_more': data['has_more'] as bool? ?? false,
      'results': results,
    };
  }
}
