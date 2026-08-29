import 'dart:io';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
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

  /// 3. 대화방 이전 메시지 내역 조회 (REST API)
  Future<List<ChatMessageModel>> fetchMessages(int roomId) async {
    final response = await _dio.get(
      '/api/v1/chat-message/',
      queryParameters: {'room': roomId},
    );
    final dynamic data = response.data;

    List<dynamic> list = [];
    if (data is List) {
      list = data;
    } else if (data is Map<String, dynamic> && data['results'] is List) {
      list = data['results'] as List<dynamic>;
    }

    return list.map((json) => ChatMessageModel.fromJson(json as Map<String, dynamic>)).toList();
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

  /// 6. 사진/파일 첨부 전송 (REST API 멀티파트)
  Future<ChatMessageModel> sendFileMessage({
    required int roomId,
    required File file,
    required String messageType,
    String? content,
  }) async {
    final fileName = file.path.split('/').last;
    final formData = FormData.fromMap({
      'room': roomId,
      'message_type': messageType,
      'content': content ?? '',
      'file': await MultipartFile.fromFile(file.path, filename: fileName),
      'file_name': fileName,
      'file_size': await file.length(),
    });

    final response = await _dio.post('/api/v1/chat-message/', data: formData);
    return ChatMessageModel.fromJson(response.data as Map<String, dynamic>);
  }

  /// 7. 대화방 나가기 / 목록에서 숨기기
  Future<void> leaveRoom(int roomId) async {
    await _dio.post('/api/v1/chat-room/$roomId/leave/');
  }
}
