import 'package:flutter/material.dart';
import '../constants/app_text_styles.dart';
import '../theme/app_colors_extension.dart';

/// 공통 에러/빈 상태 위젯
class ErrorView extends StatelessWidget {
  final String message;
  final String? subMessage;
  final VoidCallback? onRetry;
  final IconData icon;

  const ErrorView({
    super.key,
    required this.message,
    this.subMessage,
    this.onRetry,
    this.icon = Icons.error_outline_rounded,
  });

  /// 빈 목록 상태 팩토리
  const ErrorView.empty({
    super.key,
    this.message = '데이터가 없습니다.',
    this.subMessage,
    this.onRetry,
    this.icon = Icons.inbox_rounded,
  });

  /// 네트워크 오류 팩토리
  const ErrorView.network({
    super.key,
    this.message = '서버와 연결할 수 없습니다.',
    this.subMessage = '네트워크 상태를 확인해 주세요.',
    this.onRetry,
    this.icon = Icons.wifi_off_rounded,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 52, color: context.colors.textDisabled),
            const SizedBox(height: 16),
            Text(message,
                style: AppTextStyles.titleMd.copyWith(color: context.colors.textMuted),
                textAlign: TextAlign.center),
            if (subMessage != null) ...[
              const SizedBox(height: 8),
              Text(subMessage!,
                  style: AppTextStyles.bodySm.copyWith(color: context.colors.textMuted),
                  textAlign: TextAlign.center),
            ],
            if (onRetry != null) ...[
              const SizedBox(height: 24),
              OutlinedButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh_rounded, size: 18),
                label: const Text('다시 시도'),
                style: OutlinedButton.styleFrom(
                  foregroundColor: context.colors.accentWork,
                  side: BorderSide(color: context.colors.accentWork),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(6),
                  ),
                  padding:
                      const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
