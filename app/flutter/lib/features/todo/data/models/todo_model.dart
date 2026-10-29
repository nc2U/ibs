import 'package:flutter/foundation.dart';

int _parseInt(dynamic val, [int fallback = 0]) {
  if (val == null) return fallback;
  if (val is int) return val;
  if (val is num) return val.toInt();
  if (val is String) return int.tryParse(val) ?? fallback;
  return fallback;
}

int? _tryParseInt(dynamic val) {
  if (val == null) return null;
  if (val is int) return val;
  if (val is num) return val.toInt();
  if (val is String) return int.tryParse(val);
  return null;
}

/// 할일이 업무(Issue)로 전환된 경우의 요약 정보 (백엔드 TodoIssueInfoSerializer 대응)
@immutable
class TodoIssueInfo {
  final int pk;
  final int projectId;
  final String projectSlug;
  final String projectName;
  final String subject;

  const TodoIssueInfo({
    required this.pk,
    required this.projectId,
    this.projectSlug = '',
    this.projectName = '',
    this.subject = '',
  });

  factory TodoIssueInfo.fromJson(Map<String, dynamic> json) {
    return TodoIssueInfo(
      pk: _parseInt(json['pk']),
      projectId: _parseInt(json['project_id']),
      projectSlug: json['project_slug']?.toString() ?? '',
      projectName: json['project_name']?.toString() ?? '',
      subject: json['subject']?.toString() ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'pk': pk,
      'project_id': projectId,
      'project_slug': projectSlug,
      'project_name': projectName,
      'subject': subject,
    };
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is TodoIssueInfo &&
          runtimeType == other.runtimeType &&
          pk == other.pk &&
          projectId == other.projectId &&
          projectSlug == other.projectSlug &&
          projectName == other.projectName &&
          subject == other.subject;

  @override
  int get hashCode => Object.hash(
        pk,
        projectId,
        projectSlug,
        projectName,
        subject,
      );
}

@immutable
class TodoItem {
  final int pk;
  final int user;
  final String title;
  final bool completed;
  final bool softDeleted;

  /// 전환된 업무(Issue) PK. 전환되지 않은 할일은 null
  final int? issue;

  /// 전환된 업무 요약 정보 (워크스페이스/제목 등)
  final TodoIssueInfo? issueInfo;

  const TodoItem({
    required this.pk,
    required this.user,
    required this.title,
    this.completed = false,
    this.softDeleted = false,
    this.issue,
    this.issueInfo,
  });

  /// 업무로 전환된 할일인지 여부
  bool get isConverted => issue != null;

  factory TodoItem.fromJson(Map<String, dynamic> json) {
    final rawInfo = json['issue_info'];
    return TodoItem(
      pk: _parseInt(json['pk']),
      user: _parseInt(json['user']),
      title: json['title']?.toString() ?? '',
      completed: json['completed'] as bool? ?? false,
      softDeleted: json['soft_deleted'] as bool? ?? false,
      issue: _tryParseInt(json['issue']),
      issueInfo: rawInfo is Map
          ? TodoIssueInfo.fromJson(Map<String, dynamic>.from(rawInfo))
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'pk': pk,
      'user': user,
      'title': title,
      'completed': completed,
      'soft_deleted': softDeleted,
      'issue': issue,
      'issue_info': issueInfo?.toJson(),
    };
  }

  TodoItem copyWith({
    int? pk,
    int? user,
    String? title,
    bool? completed,
    bool? softDeleted,
    int? issue,
    TodoIssueInfo? issueInfo,
    bool clearIssue = false,
  }) {
    return TodoItem(
      pk: pk ?? this.pk,
      user: user ?? this.user,
      title: title ?? this.title,
      completed: completed ?? this.completed,
      softDeleted: softDeleted ?? this.softDeleted,
      issue: clearIssue ? null : (issue ?? this.issue),
      issueInfo: clearIssue ? null : (issueInfo ?? this.issueInfo),
    );
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is TodoItem &&
          runtimeType == other.runtimeType &&
          pk == other.pk &&
          user == other.user &&
          title == other.title &&
          completed == other.completed &&
          softDeleted == other.softDeleted &&
          issue == other.issue &&
          issueInfo == other.issueInfo;

  @override
  int get hashCode => Object.hash(
        pk,
        user,
        title,
        completed,
        softDeleted,
        issue,
        issueInfo,
      );
}

/// 할일 → 업무 전환 API(`convert_to_issue`) 응답
@immutable
class TodoConvertResult {
  final TodoItem todo;
  final TodoIssueInfo issue;

  const TodoConvertResult({required this.todo, required this.issue});

  factory TodoConvertResult.fromJson(Map<String, dynamic> json) {
    final todoRaw = json['todo'];
    final issueRaw = json['issue'];
    return TodoConvertResult(
      todo: TodoItem.fromJson(
        todoRaw is Map ? Map<String, dynamic>.from(todoRaw) : <String, dynamic>{},
      ),
      issue: TodoIssueInfo.fromJson(
        issueRaw is Map ? Map<String, dynamic>.from(issueRaw) : <String, dynamic>{},
      ),
    );
  }
}
