import 'dart:async';
import 'dart:convert';
import 'dart:math';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../../../../core/api/api_client.dart';
import '../../../../core/models/user_model.dart';
import '../../../../core/providers/auth_provider.dart';
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

/// 2-1. 1:1 DM 가능 대상자 목록 프로바이더 (본사 재직 스태프 + 활성 워크스페이스 멤버 전체)
final allMembersProvider = FutureProvider.autoDispose<List<UserModel>>((ref) async {
  final dio = ref.watch(dioProvider);
  final res = await dio.get('/api/v1/chat-room/available-users/');
  final dynamic data = res.data;

  List<dynamic> list = [];
  if (data is List) {
    list = data;
  } else if (data is Map<String, dynamic> && data['results'] is List) {
    list = data['results'] as List<dynamic>;
  }

  return list
      .map((json) => UserModel.fromJson(json as Map<String, dynamic>))
      .toList();
});

/// 2-2. 대화방별 상대방 타이핑 상태 프로바이더
final chatTypingUserProvider = StateProvider.autoDispose.family<String?, int>((ref, roomId) => null);

/// 3. 특정 대화방의 실시간 WebSocket & 메시지 목록 StateNotifier
class ChatRoomNotifier extends StateNotifier<AsyncValue<List<ChatMessageModel>>> {
  final int roomId;
  final ChatRepository _repo;
  final Ref _ref;
  WebSocketChannel? _channel;
  StreamSubscription? _sub;
  Timer? _reconnectTimer;
  Timer? _typingDismissTimer;
  int _reconnectAttempts = 0;
  bool _isConnected = false;
  bool _isDisposed = false;
  bool _hasConnectedOnce = false;

  // 📜 커서 페이지네이션 상태
  bool _hasMoreOlder = false;
  bool _isLoadingOlder = false;
  bool _isLoadingNewer = false;

  /// 현재 목록이 최신 메시지까지 이어져 있는지 여부
  /// (검색/보관함 점프로 과거 구간(window)을 보고 있으면 false)
  bool _atLatest = true;

  int _myUserId = 0;
  String _myUsername = '';

  late final Future<void> _initFuture;

  ChatRoomNotifier(this.roomId, this._repo, this._ref) : super(const AsyncValue.loading()) {
    _initFuture = _init();
  }

  bool get isConnected => _isConnected;
  bool get hasMoreOlder => _hasMoreOlder;
  bool get isLoadingOlder => _isLoadingOlder;
  bool get atLatest => _atLatest;

  List<ChatMessageModel> get _current => state.valueOrNull ?? const [];

  Future<void> _init() async {
    try {
      try {
        final myUser = _ref.read(currentUserProvider).valueOrNull ??
            await _ref.read(currentUserProvider.future);
        _myUserId = myUser?.pk ?? 0;
        _myUsername = myUser?.username ?? '';
      } catch (_) {
        final tokenStorage = _ref.read(tokenStorageProvider);
        final cached = await tokenStorage.getUserData();
        if (cached != null && cached.isNotEmpty) {
          try {
            final json = jsonDecode(cached) as Map<String, dynamic>;
            _myUserId = json['pk'] as int? ?? 0;
            _myUsername = json['username'] as String? ?? '';
          } catch (_) {}
        }
      }

      // 1) 기존 메시지 내역 불러오기 (최신 페이지)
      final page = await _repo.fetchMessagePage(roomId);
      if (_isDisposed) return;
      _hasMoreOlder = page.hasMore;
      _atLatest = true;
      state = AsyncValue.data(page.messages);

      // 2) 읽음 처리 - 실패해도 이미 불러온 메시지/WebSocket 연결에는 영향 없도록 분리
      await _markLatestAsRead(page.messages);

      // 3) WebSocket 연결
      await _connectWebSocket();
    } catch (e, st) {
      if (!_isDisposed) {
        state = AsyncValue.error(e, st);
      }
    }
  }

  Future<void> _markLatestAsRead(List<ChatMessageModel> messages) async {
    if (messages.isEmpty || _isDisposed) return;
    try {
      await _repo.markAsRead(roomId, lastMessageId: messages.last.id);
      if (_isDisposed) return;
      _ref.invalidate(totalUnreadChatCountProvider);
      _ref.invalidate(chatRoomsProvider);
    } catch (_) {}
  }

  /// 최신 페이지를 다시 받아 목록 꼬리(tail)를 교체한다.
  /// 이미 불러온 과거 메시지(페이지네이션 결과)는 유지하고,
  /// 삭제/소프트 삭제 등 최신 구간의 변경 사항은 반영한다.
  /// 과거 구간(window)을 보는 중에는 목록을 건드리지 않는다.
  Future<void> refreshMessages() async {
    await _initFuture;
    if (_isDisposed || !_atLatest) return;
    try {
      final page = await _repo.fetchMessagePage(roomId);
      if (_isDisposed || !_atLatest) return;
      final fetched = page.messages;
      if (fetched.isEmpty) {
        state = const AsyncValue.data([]);
        return;
      }
      final firstId = fetched.first.id;
      final kept = _current.where((m) => m.id < firstId).toList();
      if (kept.isEmpty) _hasMoreOlder = page.hasMore;
      state = AsyncValue.data([...kept, ...fetched]);
      await _markLatestAsRead(fetched);
    } catch (_) {}
  }

  /// ⬆️ 더 오래된 메시지 불러오기 (위로 스크롤 시)
  Future<bool> loadOlder() async {
    await _initFuture;
    final msgs = _current;
    if (_isDisposed || _isLoadingOlder || !_hasMoreOlder || msgs.isEmpty) return false;
    _isLoadingOlder = true;
    try {
      final page = await _repo.fetchMessagePage(roomId, beforeId: msgs.first.id);
      if (_isDisposed) return false;
      _hasMoreOlder = page.hasMore;
      final existing = _current.map((m) => m.id).toSet();
      final older = page.messages.where((m) => !existing.contains(m.id)).toList();
      if (older.isNotEmpty) {
        state = AsyncValue.data([...older, ..._current]);
      }
      return older.isNotEmpty;
    } catch (_) {
      return false;
    } finally {
      _isLoadingOlder = false;
    }
  }

  /// ⬇️ 과거 구간(window)을 보는 중 아래로 스크롤 시 더 최근 메시지 불러오기
  Future<bool> loadNewer() async {
    await _initFuture;
    final msgs = _current;
    if (_isDisposed || _isLoadingNewer || _atLatest || msgs.isEmpty) return false;
    _isLoadingNewer = true;
    try {
      final page = await _repo.fetchMessagePage(roomId, afterId: msgs.last.id);
      if (_isDisposed) return false;
      final existing = _current.map((m) => m.id).toSet();
      final newer = page.messages.where((m) => !existing.contains(m.id)).toList();
      if (!page.hasMore) _atLatest = true;
      if (newer.isNotEmpty || _atLatest) {
        state = AsyncValue.data([..._current, ...newer]);
      }
      if (_atLatest) await _markLatestAsRead(_current);
      return newer.isNotEmpty;
    } catch (_) {
      return false;
    } finally {
      _isLoadingNewer = false;
    }
  }

  /// 🎯 특정 메시지 전후 맥락을 불러와 목록을 해당 구간(window)으로 교체한다.
  /// 이미 로드된 메시지면 아무것도 하지 않고 true 를 반환한다.
  Future<bool> loadAround(int messageId) async {
    await _initFuture;
    if (_isDisposed) return false;
    if (_current.any((m) => m.id == messageId)) return true;
    try {
      final context = await _repo.fetchMessageContext(messageId, limit: 20);
      if (_isDisposed || context.isEmpty) return false;
      _hasMoreOlder = true;
      _atLatest = false;
      state = AsyncValue.data(context);
      return context.any((m) => m.id == messageId);
    } catch (_) {
      return false;
    }
  }

  /// 🔽 최신 대화로 복귀 (과거 구간을 보고 있을 때)
  Future<void> jumpToLatest() async {
    await _initFuture;
    if (_isDisposed) return;
    try {
      final page = await _repo.fetchMessagePage(roomId);
      if (_isDisposed) return;
      _hasMoreOlder = page.hasMore;
      _atLatest = true;
      state = AsyncValue.data(page.messages);
      await _markLatestAsRead(page.messages);
    } catch (_) {}
  }

  /// 재연결 직후 끊겨 있던 동안 놓친 메시지를 보충한다.
  Future<void> _syncMissedMessages() async {
    if (_isDisposed || !_atLatest) return;
    final msgs = _current;
    if (msgs.isEmpty) return;
    try {
      var lastId = msgs.last.id;
      // 최대 5페이지까지 순차 보충
      for (var i = 0; i < 5; i++) {
        final page = await _repo.fetchMessagePage(roomId, afterId: lastId);
        if (_isDisposed || !_atLatest) return;
        final existing = _current.map((m) => m.id).toSet();
        final newer = page.messages.where((m) => !existing.contains(m.id)).toList();
        if (newer.isNotEmpty) {
          state = AsyncValue.data([..._current, ...newer]);
          lastId = newer.last.id;
        }
        if (!page.hasMore || newer.isEmpty) break;
      }
      await _markLatestAsRead(_current);
    } catch (_) {}
  }

  Future<void> _connectWebSocket() async {
    if (_isDisposed) return;

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
      _sub?.cancel();
      _channel?.sink.close();

      final channel = WebSocketChannel.connect(wsUri);
      _channel = channel;

      _sub = channel.stream.listen(
        (data) {
          _handleWsMessage(data);
        },
        onError: (err) {
          if (!identical(_channel, channel)) return;
          _isConnected = false;
          _scheduleReconnect();
        },
        onDone: () {
          if (!identical(_channel, channel)) return;
          _isConnected = false;
          _scheduleReconnect();
        },
        cancelOnError: false,
      );

      // 핸드셰이크가 실제로 성공한 뒤에만 연결 상태/백오프를 초기화한다.
      // (인증 실패 등으로 거부되면 지수 백오프가 정상적으로 증가)
      await channel.ready;
      if (_isDisposed || !identical(_channel, channel)) return;
      _isConnected = true;
      _reconnectAttempts = 0;

      if (_hasConnectedOnce) {
        unawaited(_syncMissedMessages());
      }
      _hasConnectedOnce = true;
    } catch (_) {
      _isConnected = false;
      _scheduleReconnect();
    }
  }

  void _scheduleReconnect() {
    if (_isDisposed || _isConnected) return;
    // 이미 재연결이 예약되어 있으면 중복 예약(백오프 이중 증가) 방지
    if (_reconnectTimer?.isActive ?? false) return;

    // 지수 백오프: 2, 4, 8, 최대 20초 후 재연결
    final delaySeconds = min(20, max(2, pow(2, _reconnectAttempts).toInt()));
    _reconnectAttempts++;

    _reconnectTimer = Timer(Duration(seconds: delaySeconds), () {
      if (!_isDisposed && !_isConnected) {
        _connectWebSocket();
      }
    });
  }

  void _handleWsMessage(dynamic rawData) {
    try {
      final json = jsonDecode(rawData as String) as Map<String, dynamic>;
      final type = json['type'] as String?;

      if (_myUserId == 0) {
        final myUser = _ref.read(currentUserProvider).valueOrNull;
        if (myUser != null) {
          _myUserId = myUser.pk;
          _myUsername = myUser.username;
        }
      }

      if (type == 'chat_message') {
        final newMsg = ChatMessageModel.fromJson(json['data'] as Map<String, dynamic>);
        // 과거 구간(window)을 보는 중에는 목록 연속성이 깨지므로 추가하지 않는다.
        // (최신으로 돌아오거나 loadNewer 시 자동으로 불러옴)
        if (_atLatest) {
          state = state.whenData((msgs) {
            if (msgs.any((m) => m.id == newMsg.id)) return msgs;
            return [...msgs, newMsg];
          });
        }

        final isMe = (newMsg.sender != null && _myUserId > 0 && newMsg.sender!.pk == _myUserId) ||
                     (newMsg.sender != null && _myUsername.isNotEmpty && newMsg.sender!.username == _myUsername);

        // 상대방이 보낸 메시지인 경우에만 수신 즉시 읽음 처리 전송
        if (!isMe) {
          _repo.markAsRead(roomId, lastMessageId: newMsg.id).then((_) {
            _ref.invalidate(totalUnreadChatCountProvider);
            _ref.invalidate(chatRoomsProvider);
          });
          if (_channel != null && _isConnected) {
            try {
              _channel!.sink.add(jsonEncode({
                'type': 'read',
                'last_message_id': newMsg.id,
              }));
            } catch (_) {}
          }
        }
      } else if (type == 'delete_message') {
        final deletedId = json['message_id'] as int?;
        final isSoft = json['is_soft'] as bool? ?? false;
        if (deletedId != null) {
          state = state.whenData((msgs) {
            if (isSoft) {
              return msgs.map((m) {
                if (m.id == deletedId) {
                  return m.copyWith(
                    isDeleted: true,
                    content: '삭제된 메시지입니다.',
                    file: null,
                    fileName: '',
                    fileSize: 0,
                  );
                }
                return m;
              }).toList();
            } else {
              return msgs.where((m) => m.id != deletedId).toList();
            }
          });
        }
      } else if (type == 'read') {
        final readUserId = json['user_id'] as int?;
        final lastReadId = json['last_message_id'] as int?;

        // 다른 사용자가 읽은 경우에만 내가 보낸 메시지의 unreadCount를 차감
        if (readUserId != null && _myUserId > 0 && readUserId != _myUserId && lastReadId != null) {
          state = state.whenData((msgs) {
            return msgs.map((m) {
              if (m.id <= lastReadId && m.unreadCount > 0) {
                return m.copyWith(unreadCount: (m.unreadCount - 1).clamp(0, 999));
              }
              return m;
            }).toList();
          });
        }
      } else if (type == 'typing') {
        final isTyping = json['is_typing'] as bool? ?? false;
        final senderName = json['sender_name']?.toString() ?? json['username']?.toString() ?? '상대방';
        final senderId = json['user_id'] as int? ?? json['sender_id'] as int?;

        if (senderId != null && senderId != _myUserId) {
          _typingDismissTimer?.cancel();
          if (isTyping) {
            _ref.read(chatTypingUserProvider(roomId).notifier).state = senderName;
            _typingDismissTimer = Timer(const Duration(seconds: 3), () {
              if (!_isDisposed) {
                _ref.read(chatTypingUserProvider(roomId).notifier).state = null;
              }
            });
          } else {
            _ref.read(chatTypingUserProvider(roomId).notifier).state = null;
          }
        }
      }
    } catch (_) {}
  }

  /// 💬 메시지 전송 (웹소켓 전송 시도 + 단절 시 REST API 자동 폴백으로 무음 유실 100% 방지)
  Future<void> sendMessage({
    required String content,
    ChatMessageType type = ChatMessageType.text,
    int? refId,
    String? refTitle,
    String? refSub,
    int? replyToId,
  }) async {
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
      'reply_to': replyToId,
      'reply_to_id': replyToId,
    };

    if (!_atLatest) await jumpToLatest();

    bool sentViaWs = false;
    if (_channel != null && _isConnected) {
      try {
        _channel!.sink.add(jsonEncode(payload));
        sentViaWs = true;
      } catch (_) {
        sentViaWs = false;
      }
    }

    // 웹소켓 연결이 없거나 전송 실패 시 즉시 REST API로 자동 폴백
    if (!sentViaWs) {
      try {
        final newMsg = await _repo.sendTextMessage(
          roomId: roomId,
          content: content,
          messageType: parseTypeStr(type),
          refId: refId,
          refTitle: refTitle,
          refSub: refSub,
          replyToId: replyToId,
        );
        state = state.whenData((msgs) {
          if (msgs.any((m) => m.id == newMsg.id)) return msgs;
          return [...msgs, newMsg];
        });
        _ref.invalidate(chatRoomsProvider);
      } catch (e) {
        rethrow;
      }
    }
  }

  /// 📎 사진 / 파일 전송 후 로컬 상태 즉시 추가 (XFile 기반 크로스 플랫폼 지원)
  Future<void> sendFile({
    required XFile file,
    required String messageType,
    String? content,
    int? replyToId,
  }) async {
    try {
      if (!_atLatest) await jumpToLatest();
      final newMsg = await _repo.sendXFileMessage(
        roomId: roomId,
        file: file,
        messageType: messageType,
        content: content,
        replyToId: replyToId,
      );
      state = state.whenData((msgs) {
        if (msgs.any((m) => m.id == newMsg.id)) return msgs;
        return [...msgs, newMsg];
      });
      _ref.invalidate(chatRoomsProvider);
    } catch (e) {
      rethrow;
    }
  }

  /// ✍️ 타이핑 인디케이터 전송
  void sendTyping(bool isTyping) {
    if (_channel == null || !_isConnected) return;
    try {
      _channel!.sink.add(jsonEncode({
        'type': 'typing',
        'is_typing': isTyping,
      }));
    } catch (_) {}
  }

  /// 🗑️ 메시지 / 첨부파일 삭제
  Future<void> deleteMessage(int messageId) async {
    try {
      await _repo.deleteMessage(messageId, roomId: roomId);
      _ref.invalidate(chatRoomsProvider);
      // WebSocket 이 끊겨 있으면 delete_message 이벤트를 받지 못하므로
      // 서버 기준(완전/소프트 삭제)으로 최신 구간을 다시 동기화한다.
      if (!_isConnected) {
        await refreshMessages();
      }
    } catch (e) {
      rethrow;
    }
  }

  @override
  void dispose() {
    _isDisposed = true;
    _reconnectTimer?.cancel();
    _typingDismissTimer?.cancel();
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
