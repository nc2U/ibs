import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../features/approval/providers/approval_providers.dart';
import '../services/app_badge_service.dart';
import 'notification_provider.dart';

/// 앱 전체 미확인 알림 및 결재 대기 건수를 합산한 총 뱃지 카운트 Provider
final totalAppBadgeCountProvider = Provider.autoDispose<int>((ref) {
  final unreadNotifCount = ref.watch(unreadNotificationCountProvider);
  final pendingApprovalCount = ref.watch(pendingApprovalCountProvider);

  final total = unreadNotifCount + pendingApprovalCount;

  // 총 뱃지 카운트 변경 시 모바일 OS 앱 아이콘 뱃지 자동 갱신
  AppBadgeService.updateBadgeCount(total);

  return total;
});
