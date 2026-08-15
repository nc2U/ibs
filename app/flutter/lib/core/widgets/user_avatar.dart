import 'package:flutter/material.dart';
import '../api/api_client.dart';
import '../constants/app_colors.dart';
import '../constants/app_text_styles.dart';
import '../models/user_model.dart';

/// 공용 사용자 아바타 위젯 (이미지 URL 지원 + fallback 이니셜)
class UserAvatar extends StatelessWidget {
  final UserModel? user;
  final String? imageUrl;
  final String? fallbackText;
  final double radius;
  final Color? backgroundColor;
  final Color? textColor;

  const UserAvatar({
    super.key,
    this.user,
    this.imageUrl,
    this.fallbackText,
    this.radius = 16,
    this.backgroundColor,
    this.textColor,
  });

  String? _resolveFullUrl(String? rawUrl) {
    if (rawUrl == null || rawUrl.trim().isEmpty) return null;
    final trimmed = rawUrl.trim();
    if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
      return trimmed;
    }
    final base = appBaseUrl;
    if (trimmed.startsWith('/')) {
      return '$base$trimmed';
    }
    return '$base/$trimmed';
  }

  @override
  Widget build(BuildContext context) {
    final rawUrl = imageUrl ?? user?.avatarUrl;
    final fullUrl = _resolveFullUrl(rawUrl);
    final initial = fallbackText ?? user?.initial ?? 'U';

    final bgColor = backgroundColor ?? AppColors.accentWork.withAlpha(45);
    final fgColor = textColor ?? AppColors.accentWork;

    if (fullUrl != null) {
      return CircleAvatar(
        radius: radius,
        backgroundColor: bgColor,
        child: ClipOval(
          child: Image.network(
            fullUrl,
            width: radius * 2,
            height: radius * 2,
            fit: BoxFit.cover,
            errorBuilder: (_, __, ___) => Center(
              child: Text(
                initial,
                style: AppTextStyles.label.copyWith(
                  color: fgColor,
                  fontSize: radius * 0.9,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
            loadingBuilder: (ctx, child, progress) {
              if (progress == null) return child;
              return Center(
                child: SizedBox(
                  width: radius,
                  height: radius,
                  child: CircularProgressIndicator(
                    strokeWidth: 1.5,
                    value: progress.expectedTotalBytes != null
                        ? progress.cumulativeBytesLoaded /
                            progress.expectedTotalBytes!
                        : null,
                    color: fgColor,
                  ),
                ),
              );
            },
          ),
        ),
      );
    }

    return CircleAvatar(
      radius: radius,
      backgroundColor: bgColor,
      child: Text(
        initial,
        style: AppTextStyles.label.copyWith(
          color: fgColor,
          fontSize: radius * 0.9,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }
}
