import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/network_monitor.dart';
import '../constants/app_text_styles.dart';

/// 오프라인 상태일 때 화면 상단에 표시되는 전역 배너
///
/// MaterialApp.router의 `builder` 콜백에서 감싸서 사용:
/// ```dart
/// builder: (context, child) => OfflineBanner(child: child!),
/// ```
class OfflineBanner extends ConsumerWidget {
  final Widget child;

  const OfflineBanner({super.key, required this.child});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isOffline = ref.watch(isOfflineProvider);

    return Column(
      children: [
        AnimatedContainer(
          duration: const Duration(milliseconds: 300),
          height: isOffline ? 36 : 0,
          color: const Color(0xFFD32F2F), // Material Red 700
          child: isOffline
              ? Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.wifi_off_rounded,
                        color: Colors.white, size: 16),
                    const SizedBox(width: 8),
                    Text(
                      '네트워크 연결이 끊겼습니다.',
                      style: AppTextStyles.bodySm
                          .copyWith(color: Colors.white, height: 1),
                    ),
                  ],
                )
              : const SizedBox.shrink(),
        ),
        Expanded(child: child),
      ],
    );
  }
}
