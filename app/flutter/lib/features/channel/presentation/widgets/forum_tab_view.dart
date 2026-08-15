import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_text_styles.dart';

/// 게시판 탭 뷰 (추후 게시판 목록 / 카테고리 / 포스트 연동 기반 뷰)
class ForumTabView extends ConsumerWidget {
  const ForumTabView({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // 안내 헤더 카드
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.bgCard,
              borderRadius: BorderRadius.zero,
              border: Border.all(color: AppColors.border, width: 0.8),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: const Color(0xFF00695C).withAlpha(25),
                        borderRadius: BorderRadius.zero,
                      ),
                      child: const Icon(
                        Icons.forum_rounded,
                        color: Color(0xFF00695C),
                        size: 22,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('워크스페이스 사내 게시판',
                              style: AppTextStyles.titleSm),
                          const SizedBox(height: 2),
                          Text(
                            '팀별 자유 토론 및 소통 채널입니다.',
                            style: AppTextStyles.bodyMuted,
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 14),
                const Divider(color: AppColors.border, height: 1),
                const SizedBox(height: 14),
                Text(
                  '💡 안내: 게시판 목록 및 카테고리별 게시글 작성/조회 기능이 곧 연결될 예정입니다.',
                  style: AppTextStyles.caption.copyWith(
                    color: AppColors.textSecond,
                    height: 1.4,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
