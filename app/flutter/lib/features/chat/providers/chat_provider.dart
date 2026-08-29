import 'dart:async';
import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../../../../core/api/api_client.dart';
import '../../../../core/providers/dio_provider.dart';
import '../data/chat_repository.dart';
import '../data/models/chat_model.dart';

/// 1. 대화방 목록 프로바이더
final chatRoomsProvider = FutureProvider.autoDispose<List<ChatRoomModel>>((ref) async {
  final repo = ref.watch(chatRepositoryProvider);
  return repo.fetchChatRooms();
});

/// 2. 전체 미확인 메시지 총합 프로바이더 (상단 앱바 💬 배지용)
final totalUnreadChatCountProvider = FutureProvider.autoDispose<int>((ref) async {
  final repo = ref.watch(chatRepositoryProvider);
  return repo.fetchTotalUnread();
});

/// 3. 특정 대화방의 실시간 WebSocket & 메시지 목록 StateNotifier
class ChatRoomNotifier extends StateNotifier<AsyncValue<List<ChatMessageModel>>> {
  final int roomId;
  final ChatRepository _repo;
  final Ref _ref;
  WebSocketChannel? _channel;
  StreamSubscription? _sub;
  bool _isTyping = false;
  String _typingUser = '';

  ChatRoomNotifier(this.roomId, this._repo, this._ref) : super(const AsyncValue.loading()) {
    _init();
  }

  bool get isTyping => _isTyping;
  String get typingUser => _typingUser;

  Future<void> _init() async {
    try {
      // 1) 기존 메시지 내역 불러오기
      final initialMessages = await _repo.fetchMessages(roomId);
      state = AsyncValue.data(initialMessages);

      // 2) 읽음 처리
      if (initialMessages.isNotEmpty) {
        await _repo.markAsRead(roomId, lastMessageId: initialMessages.last.id);
        _ref.invalidate(totalUnreadChatCountProvider);
        _ref.invalidate(chatRoomsProvider);
      }

      // 3) WebSocket 연결
      await _connectWebSocket();
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> _connectWebSocket() async {
    final tokenStorage = _ref.read(tokenStorageProvider);
    final token = await tokenStorage.getAccessToken();
    if (token == null) return;

    // WebSocket URL 생성 (ws:// 또는 wss://)
    final baseHttp = appBaseUrl;
    final wsBase = baseHttp.startsWith('https://')
        ? baseHttp.replaceFirst('https://', 'wss://')
        : baseHttp.replaceFirst('http://', 'ws://');

    final wsUri = Uri.parse('$wsBase/ws/chat/$roomId/?token=$token');

    try {
      _channel = WebSocketChannel.connect(wsUri);
      _sub = _channel!.stream.listen(
        (data) {
          _handleWsMessage(data);
        },
        onError: (err) {
          // 에러 발생 시 재연결 대기
        },
        onDone: () {
          // 연결 종료 시
        },
      );
    } catch (_) {}
  }

  void _handleWsMessage(dynamic rawData) {
    try {
      final json = jsonDecode(rawData as String) as Map<String, dynamic>;
      final type = json['type'] as String?;

      if (type == 'chat_message') {
        final newMsg = ChatMessageModel.fromJson(json['data'] as Map<String, dynamic>);
        state = state.whenData((msgs) {
          if (msgs.any((m) => m.id == newMsg.id)) return msgs;
          return [...msgs, newMsg];
        });

        // 수신 즉시 읽음 처리
        _repo.markAsRead(roomId, lastMessageId: newMsg.id);
        _ref.invalidate(totalUnreadChatCountProvider);
        _ref.invalidate(chatRoomsProvider);
      }
    } catch (_) {}
  }

  /// 💬 메시지 전송
  void sendMessage({
    required String content,
    ChatMessageType type = ChatMessageType.text,
    int? refId,
    String? refTitle,
    String? refSub,
    int? replyToId,
  }) {
    if (_channel == null) return;

    String parseTypeStr(ChatMessageType t) {
      switch (t) {
        case ChatMessageType.issue:
          return 'issue';
        case ChatMessageType.meeting:
          return 'meeting';
        case ChatMessageType.approval:
          return 'approval';
        default:
          return 'text';
      }
    }

    final payload = {
      'type': 'chat_message',
      'content': content,
      'message_type': parseTypeStr(type),
      'ref_id': refId,
      'ref_title': refTitle ?? '',
      'ref_sub': refSub ?? '',
      'reply_to_id': replyToId,
    };

    _channel!.sink.add(jsonEncode(payload));
  }

  /// ✍️ 타이핑 인디케이터 전송
  void sendTyping(bool isTyping) {
    if (_channel == null) return;
    _channel!.sink.add(jsonEncode({
      'type': 'typing',
      'is_typing': isTyping,
    }));
  }

  @override
  void dispose() {
    _sub?.cancel();
    _channel?.sink.close();
    super.dispose();
  }
}

/// 4. 대화방별 실시간 StateNotifierProvider
final chatRoomNotifierProvider = StateNotifierProvider.autoDispose.family<ChatRoomNotifier, AsyncValue<List<ChatMessageModel>>, int>((ref, roomId) {
  final repo = ref.watch(chatRepositoryProvider);
  return ChatRoomNotifier(roomId, repo, ref);
});
