import 'package:flutter/foundation.dart';

@immutable
class NotificationModel {
  final int pk;
  final String title;
  final String body;
  final String category; // work, meeting, notice, approval, chat
  final String targetType; // issue, meeting, notice
  final String targetId;
  final Map<String, dynamic> data;
  final bool isRead;
  final DateTime createdAt;

  const NotificationModel({
    required this.pk,
    required this.title,
    required this.body,
    required this.category,
    required this.targetType,
    required this.targetId,
    required this.data,
    required this.isRead,
    required this.createdAt,
  });

  factory NotificationModel.fromJson(Map<String, dynamic> json) {
    return NotificationModel(
      pk: json['pk'] as int? ?? 0,
      title: json['title'] as String? ?? '',
      body: json['body'] as String? ?? '',
      category: json['category'] as String? ?? 'work',
      targetType: json['target_type'] as String? ?? '',
      targetId: json['target_id']?.toString() ?? '',
      data: json['data'] is Map<String, dynamic>
          ? json['data'] as Map<String, dynamic>
          : {},
      isRead: json['is_read'] as bool? ?? false,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'].toString())?.toLocal() ??
              DateTime.now()
          : DateTime.now(),
    );
  }

  NotificationModel copyWith({bool? isRead}) {
    return NotificationModel(
      pk: pk,
      title: title,
      body: body,
      category: category,
      targetType: targetType,
      targetId: targetId,
      data: data,
      isRead: isRead ?? this.isRead,
      createdAt: createdAt,
    );
  }
}
