import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../constants/app_text_styles.dart';
import '../models/notification_model.dart';
import '../providers/notification_provider.dart';
import '../theme/app_colors_extension.dart';
import '../../features/approval/providers/approval_providers.dart';

/// 알림 센터 바텀 시트
class NotificationSheet extends ConsumerStatefulWidget {
  const NotificationSheet({super.key});

  static void show(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => const NotificationSheet(),
    );
  }

  @override
  ConsumerState<NotificationSheet> createState() => _NotificationSheetState();
}

class _NotificationSheetState extends ConsumerState<NotificationSheet> {
  String _selectedCategory = 'all'; // all, work, meeting, notice, approval

  String _formatTimeAgo(DateTime dt) {
    final diff = DateTime.now().difference(dt);
    if (diff.inMinutes < 1) return '방금 전';
    if (diff.inMinutes < 60) return '${diff.inMinutes}분 전';
    if (diff.inHours < 24) return '${diff.inHours}시간 전';
    if (diff.inDays < 7) return '${diff.inDays}일 전';
    return '${dt.year}.${dt.month.toString().padLeft(2, '0')}.${dt.day.toString().padLeft(2, '0')}';
  }

  void _handleNotificationTap(NotificationModel n) {
    // 1. 읽음 처리
    if (!n.isRead) {
      ref.read(notificationListProvider.notifier).markAsRead(n.pk);
    }

    // 2. 바텀 시트 닫기
    Navigator.of(context).pop();

    // 3. 딥링크 라우팅
    if (n.targetType == 'issue' && n.targetId.isNotEmpty) {
      context.go('/work/issues/${n.targetId}');
    } else if (n.targetType == 'meeting' && n.targetId.isNotEmpty) {
      context.go('/work/meetings/${n.targetId}');
    } else if (n.category == 'notice') {
      context.go('/channel?section=0&tab=0');
    } else if (n.category == 'approval') {
      if (n.targetId.isNotEmpty) {
        context.go('/approval/${n.targetId}');
      } else {
        context.go('/approval');
      }
    }
  }

  Color _getCategoryColor(String category, BuildContext context) {
    switch (category) {
      case 'work':
        return context.colors.accentWork;
      case 'meeting':
        return const Color(0xFF0D9488); // Teal
      case 'notice':
        return const Color(0xFFF59E0B); // Amber
      case 'approval':
        return const Color(0xFF8B5CF6); // Purple
      default:
        return context.colors.accentCorp;
    }
  }

  IconData _getCategoryIcon(String category, String targetType) {
    switch (category) {
      case 'work':
        return Icons.task_alt_rounded;
      case 'meeting':
        return Icons.groups_rounded;
      case 'notice':
        return Icons.campaign_rounded;
      case 'approval':
        return Icons.fact_check_rounded;
      default:
        return Icons.notifications_rounded;
    }
  }

  @override
  Widget build(BuildContext context) {
    final notificationsAsync = ref.watch(notificationListProvider);
    final unreadCount = ref.watch(unreadNotificationCountProvider);

    return Container(
      height: MediaQuery.of(context).size.height * 0.75,
      decoration: BoxDecoration(
        color: context.colors.bgPrimary,
        borderRadius: const BorderRadius.only(
          topLeft: Radius.circular(16),
          topRight: Radius.circular(16),
        ),
        border: Border(
          top: BorderSide(color: context.colors.border, width: 1),
        ),
      ),
      child: Column(
        children: [
          // ── 상단 드래그 핸들 ──────────────────────────────────────────
          Center(
            child: Container(
              margin: const EdgeInsets.only(top: 10, bottom: 8),
              width: 36,
              height: 4,
              decoration: BoxDecoration(
                color: context.colors.textDisabled.withAlpha(80),
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),

          // ── 헤더: 타이틀 + 모두 읽음 액션 ──────────────────────────────
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 8),
            child: Row(
              children: [
                Text(
                  '알림 센터',
                  style: AppTextStyles.titleMd.copyWith(
                    fontWeight: FontWeight.bold,
                    color: context.colors.textPrimary,
                  ),
                ),
                if (unreadCount > 0) ...[
                  const SizedBox(width: 8),
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: context.colors.accentWork,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Text(
                      '$unreadCount',
                      style: const TextStyle(
                        fontSize: 10.5,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                  ),
                ],
                const Spacer(),
                if (unreadCount > 0)
                  TextButton(
                    onPressed: () {
                      ref
                          .read(notificationListProvider.notifier)
                          .markAllAsRead();
                    },
                    style: TextButton.styleFrom(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 4),
                      minimumSize: Size.zero,
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                    child: Text(
                      '모두 읽음',
                      style: TextStyle(
                        fontSize: 12,
                        color: context.colors.accentCorp,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
              ],
            ),
          ),

          // ── 결재 대기 바로가기 배너 (대기 문서가 있을 때) ───────────────
          if (ref.watch(pendingApprovalCountProvider) > 0)
            Container(
              margin: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: context.colors.accentApproval.withAlpha(20),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                  color: context.colors.accentApproval.withAlpha(80),
                  width: 0.8,
                ),
              ),
              child: InkWell(
                onTap: () {
                  Navigator.of(context).pop();
                  context.go('/approval');
                },
                child: Row(
                  children: [
                    Icon(
                      Icons.draw_rounded,
                      size: 18,
                      color: context.colors.accentApproval,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        '결재 대기 중인 문서가 ${ref.watch(pendingApprovalCountProvider)}건 있습니다.',
                        style: TextStyle(
                          fontSize: 12.5,
                          fontWeight: FontWeight.w600,
                          color: context.colors.accentApproval,
                        ),
                      ),
                    ),
                    Icon(
                      Icons.arrow_forward_ios_rounded,
                      size: 12,
                      color: context.colors.accentApproval,
                    ),
                  ],
                ),
              ),
            ),

          // ── 카테고리 필터 칩 ──────────────────────────────────────────
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
            child: Row(
              children: [
                _buildFilterChip('all', '전체'),
                const SizedBox(width: 6),
                _buildFilterChip('work', '업무'),
                const SizedBox(width: 6),
                _buildFilterChip('meeting', '회의'),
                const SizedBox(width: 6),
                _buildFilterChip('notice', '공지'),
              ],
            ),
          ),
          Divider(color: context.colors.border, height: 1),

          // ── 알림 목록 본문 ──────────────────────────────────────────
          Expanded(
            child: notificationsAsync.when(
              loading: () => const Center(
                child: CircularProgressIndicator(strokeWidth: 2),
              ),
              error: (err, _) => Center(
                child: Text(
                  '알림을 불러오지 못했습니다.',
                  style: TextStyle(color: context.colors.textMuted),
                ),
              ),
              data: (list) {
                final filtered = _selectedCategory == 'all'
                    ? list
                    : list.where((n) => n.category == _selectedCategory).toList();

                if (filtered.isEmpty) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          Icons.notifications_off_outlined,
                          size: 40,
                          color: context.colors.textDisabled,
                        ),
                        const SizedBox(height: 12),
                        Text(
                          '새로운 알림이 없습니다.',
                          style: TextStyle(
                            fontSize: 13,
                            color: context.colors.textMuted,
                          ),
                        ),
                      ],
                    ),
                  );
                }

                return ListView.separated(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  itemCount: filtered.length,
                  separatorBuilder: (ctx, idx) => Divider(
                    color: context.colors.border.withAlpha(60),
                    height: 1,
                  ),
                  itemBuilder: (ctx, idx) {
                    final n = filtered[idx];
                    final catColor = _getCategoryColor(n.category, context);
                    final catIcon = _getCategoryIcon(n.category, n.targetType);

                    return InkWell(
                      onTap: () => _handleNotificationTap(n),
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 18, vertical: 14),
                        color: n.isRead
                            ? Colors.transparent
                            : catColor.withAlpha(12),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            // 카테고리 아이콘 배지
                            Container(
                              padding: const EdgeInsets.all(8),
                              decoration: BoxDecoration(
                                color: catColor.withAlpha(25),
                                borderRadius: BorderRadius.circular(8),
                                border: Border.all(
                                  color: catColor.withAlpha(60),
                                  width: 0.6,
                                ),
                              ),
                              child: Icon(catIcon, color: catColor, size: 18),
                            ),
                            const SizedBox(width: 12),

                            // 본문 텍스트
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    children: [
                                      Expanded(
                                        child: Text(
                                          n.title,
                                          style: TextStyle(
                                            fontSize: 13,
                                            fontWeight: n.isRead
                                                ? FontWeight.w500
                                                : FontWeight.w700,
                                            color: n.isRead
                                                ? context.colors.textSecond
                                                : context.colors.textPrimary,
                                            letterSpacing: -0.2,
                                          ),
                                          maxLines: 1,
                                          overflow: TextOverflow.ellipsis,
                                        ),
                                      ),
                                      const SizedBox(width: 6),
                                      Text(
                                        _formatTimeAgo(n.createdAt),
                                        style: TextStyle(
                                          fontSize: 10.5,
                                          color: context.colors.textMuted,
                                        ),
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 3),
                                  Text(
                                    n.body,
                                    style: TextStyle(
                                      fontSize: 12,
                                      color: n.isRead
                                          ? context.colors.textMuted
                                          : context.colors.textSecond,
                                      height: 1.35,
                                    ),
                                    maxLines: 2,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ],
                              ),
                            ),

                            // 미확인 닷 (Dot)
                            if (!n.isRead) ...[
                              const SizedBox(width: 8),
                              Container(
                                width: 6,
                                height: 6,
                                margin: const EdgeInsets.only(top: 6),
                                decoration: BoxDecoration(
                                  color: catColor,
                                  shape: BoxShape.circle,
                                ),
                              ),
                            ],
                          ],
                        ),
                      ),
                    );
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterChip(String key, String label) {
    final isSelected = _selectedCategory == key;
    return InkWell(
      onTap: () => setState(() => _selectedCategory = key),
      borderRadius: BorderRadius.circular(14),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
        decoration: BoxDecoration(
          color: isSelected
              ? context.colors.accentWork
              : context.colors.bgSurface,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: isSelected
                ? context.colors.accentWork
                : context.colors.border,
            width: 0.8,
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 11.5,
            fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
            color: isSelected ? Colors.white : context.colors.textSecond,
          ),
        ),
      ),
    );
  }
}
