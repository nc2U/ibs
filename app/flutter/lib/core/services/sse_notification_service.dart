import 'dart:async';
import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/dio_provider.dart';
import '../providers/notification_provider.dart';
import '../../features/approval/providers/approval_providers.dart';

/// Server-Sent Events (SSE) 실시간 알림 스트림 서비스
/// - 앱 실행 중 백엔드(/api/v1/notifications/stream/)와 영구 HTTP 스트림 연결 유지
/// - 결재 요청, 승인, 업무 등 이벤트 발생 즉시(0.1초 내) 알림 목록 및 결재 대기 상태 동기화
class SseNotificationService {
  final Dio _dio;
  final Ref _ref;
  CancelToken? _cancelToken;
  bool _isRunning = false;
  bool _isDisposed = false;

  SseNotificationService(this._dio, this._ref);

  void start() {
    if (_isRunning || _isDisposed) return;
    _isRunning = true;
    _listenStream();
  }

  void stop() {
    _isRunning = false;
    _cancelToken?.cancel('SSE Service stopped');
    _cancelToken = null;
  }

  void dispose() {
    _isDisposed = true;
    stop();
  }

  Future<void> _listenStream() async {
    while (_isRunning && !_isDisposed) {
      try {
        _cancelToken = CancelToken();
        debugPrint('📡 [SSE] 실시간 알림 스트림 연결 시도...');

        final response = await _dio.get<ResponseBody>(
          '/api/v1/notifications/stream/',
          cancelToken: _cancelToken,
          options: Options(
            responseType: ResponseType.stream,
            headers: {
              'Accept': 'text/event-stream',
              'Cache-Control': 'no-cache',
            },
            receiveTimeout: const Duration(minutes: 10),
          ),
        );

        if (response.data == null) {
          throw Exception('SSE response stream is null');
        }

        debugPrint('✅ [SSE] 실시간 알림 스트림 연결 성공');

        String buffer = '';
        await for (final chunk in response.data!.stream) {
          if (!_isRunning || _isDisposed) break;

          final text = utf8.decode(chunk, allowMalformed: true);
          buffer += text;

          // SSE 이벤트 블록은 더블 개행(\n\n)으로 구분됨
          while (buffer.contains('\n\n')) {
            final splitIdx = buffer.indexOf('\n\n');
            final eventBlock = buffer.substring(0, splitIdx).trim();
            buffer = buffer.substring(splitIdx + 2);

            if (eventBlock.isNotEmpty) {
              _processSseEvent(eventBlock);
            }
          }
        }
      } catch (e) {
        if (_cancelToken?.isCancelled ?? false) {
          debugPrint('📡 [SSE] 스트림이 정상적으로 취소됨');
          break;
        }
        debugPrint('⚠️ [SSE] 스트림 연결 끊김 / 오류 ($e), 3초 후 재연결...');
      }

      if (_isRunning && !_isDisposed) {
        await Future.delayed(const Duration(seconds: 3));
      }
    }
  }

  void _processSseEvent(String block) {
    try {
      final lines = block.split('\n');
      String? eventType;
      String? dataStr;

      for (final line in lines) {
        if (line.startsWith('event:')) {
          eventType = line.substring(6).trim();
        } else if (line.startsWith('data:')) {
          dataStr = line.substring(5).trim();
        }
      }

      if (eventType == 'notification' || (dataStr != null && dataStr.isNotEmpty && eventType != 'connected')) {
        debugPrint('🔔 [SSE] 실시간 알림 수신: $dataStr');

        // 채팅(chat) 관련 SSE 이벤트는 알림 센터 갱신에서 제외
        if (dataStr != null && dataStr.contains('"category":"chat"')) {
          return;
        }

        // 1. 알림 목록 및 미확인 배지 즉시 갱신
        _ref.read(notificationListProvider.notifier).fetchNotifications();

        // 2. 전자결재 결재 대기 목록 프로바이더 즉시 무효화/갱신
        _ref.invalidate(pendingApprovalsProvider);
        _ref.invalidate(draftedApprovalsProvider);
        _ref.invalidate(approvedApprovalsProvider);
        _ref.invalidate(allApprovalsProvider);
      }
    } catch (e) {
      debugPrint('⚠️ [SSE] 이벤트 처리 오류: $e');
    }
  }
}

final sseNotificationServiceProvider = Provider.autoDispose<SseNotificationService>((ref) {
  final dio = ref.watch(dioProvider);
  final service = SseNotificationService(dio, ref);
  service.start();

  ref.onDispose(() {
    service.dispose();
  });

  return service;
});
