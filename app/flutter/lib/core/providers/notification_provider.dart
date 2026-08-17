import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/notification_model.dart';
import 'dio_provider.dart';

/// 사용자 알림 목록 노티파이어
class NotificationListNotifier
    extends StateNotifier<AsyncValue<List<NotificationModel>>> {
  final Dio _dio;

  NotificationListNotifier(this._dio) : super(const AsyncValue.loading()) {
    fetchNotifications();
  }

  Future<void> fetchNotifications() async {
    try {
      state = const AsyncValue.loading();
      final response = await _dio.get('/api/v1/notification/');
      final data = response.data;
      List<dynamic> rawList = [];
      if (data is List) {
        rawList = data;
      } else if (data is Map && data['results'] is List) {
        rawList = data['results'] as List;
      }
      final items = rawList
          .map((e) => NotificationModel.fromJson(e as Map<String, dynamic>))
          .toList();
      state = AsyncValue.data(items);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> markAsRead(int notificationId) async {
    try {
      await _dio.post('/api/v1/notification/$notificationId/read/');
      state.whenData((list) {
        state = AsyncValue.data(
          list.map((n) {
            if (n.pk == notificationId) {
              return n.copyWith(isRead: true);
            }
            return n;
          }).toList(),
        );
      });
    } catch (_) {}
  }

  Future<void> markAllAsRead() async {
    try {
      await _dio.post('/api/v1/notification/read-all/');
      state.whenData((list) {
        state = AsyncValue.data(
          list.map((n) => n.copyWith(isRead: true)).toList(),
        );
      });
    } catch (_) {}
  }
}

final notificationListProvider = StateNotifierProvider.autoDispose<
    NotificationListNotifier, AsyncValue<List<NotificationModel>>>((ref) {
  final dio = ref.watch(dioProvider);
  return NotificationListNotifier(dio);
});

/// 미확인 알림 수 Provider
final unreadNotificationCountProvider =
    Provider.autoDispose<int>((ref) {
  final listAsync = ref.watch(notificationListProvider);
  return listAsync.maybeWhen(
    data: (list) => list.where((n) => !n.isRead).length,
    orElse: () => 0,
  );
});
