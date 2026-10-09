import 'package:flutter/foundation.dart';

@immutable
class TodoItem {
  final int pk;
  final int user;
  final String title;
  final bool completed;
  final bool softDeleted;

  const TodoItem({
    required this.pk,
    required this.user,
    required this.title,
    this.completed = false,
    this.softDeleted = false,
  });

  factory TodoItem.fromJson(Map<String, dynamic> json) {
    return TodoItem(
      pk: json['pk'] as int? ?? 0,
      user: json['user'] as int? ?? 0,
      title: json['title'] as String? ?? '',
      completed: json['completed'] as bool? ?? false,
      softDeleted: json['soft_deleted'] as bool? ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'pk': pk,
      'user': user,
      'title': title,
      'completed': completed,
      'soft_deleted': softDeleted,
    };
  }

  TodoItem copyWith({
    int? pk,
    int? user,
    String? title,
    bool? completed,
    bool? softDeleted,
  }) {
    return TodoItem(
      pk: pk ?? this.pk,
      user: user ?? this.user,
      title: title ?? this.title,
      completed: completed ?? this.completed,
      softDeleted: softDeleted ?? this.softDeleted,
    );
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is TodoItem &&
          runtimeType == other.runtimeType &&
          pk == other.pk &&
          title == other.title &&
          completed == other.completed &&
          softDeleted == other.softDeleted;

  @override
  int get hashCode =>
      pk.hashCode ^ title.hashCode ^ completed.hashCode ^ softDeleted.hashCode;
}
