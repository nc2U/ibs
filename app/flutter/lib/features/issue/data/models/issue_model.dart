import 'package:freezed_annotation/freezed_annotation.dart';
import '../../../../core/models/common_models.dart';

part 'issue_model.freezed.dart';
part 'issue_model.g.dart';

// ── 경량 모델 ─────────────────────────────────────────────────────────────

@freezed
class IssueStatusModel with _$IssueStatusModel {
  @JsonSerializable(fieldRename: FieldRename.snake)
  const factory IssueStatusModel({
    required int pk,
    required String name,
    required bool closed,
  }) = _IssueStatusModel;
  factory IssueStatusModel.fromJson(Map<String, dynamic> json) =>
      _$IssueStatusModelFromJson(json);
}

@freezed
class IssuePriorityModel with _$IssuePriorityModel {
  @JsonSerializable(fieldRename: FieldRename.snake)
  const factory IssuePriorityModel({
    required int pk,
    required String name,
  }) = _IssuePriorityModel;
  factory IssuePriorityModel.fromJson(Map<String, dynamic> json) =>
      _$IssuePriorityModelFromJson(json);
}

@freezed
class IssueTrackerModel with _$IssueTrackerModel {
  @JsonSerializable(fieldRename: FieldRename.snake)
  const factory IssueTrackerModel({
    required int pk,
    required String name,
    @Default('') String description,
  }) = _IssueTrackerModel;
  factory IssueTrackerModel.fromJson(Map<String, dynamic> json) =>
      _$IssueTrackerModelFromJson(json);
}

@freezed
class IssueVersionModel with _$IssueVersionModel {
  @JsonSerializable(fieldRename: FieldRename.snake)
  const factory IssueVersionModel({
    required int pk,
    required String name,
    @Default('') String description,
  }) = _IssueVersionModel;
  factory IssueVersionModel.fromJson(Map<String, dynamic> json) =>
      _$IssueVersionModelFromJson(json);
}

@freezed
class MeetingDescModel with _$MeetingDescModel {
  @JsonSerializable(fieldRename: FieldRename.snake)
  const factory MeetingDescModel({
    required int pk,
    required String title,
  }) = _MeetingDescModel;
  factory MeetingDescModel.fromJson(Map<String, dynamic> json) =>
      _$MeetingDescModelFromJson(json);
}

@freezed
class ParentIssueModel with _$ParentIssueModel {
  @JsonSerializable(fieldRename: FieldRename.snake)
  const factory ParentIssueModel({
    required int pk,
    required String tracker,
    required String subject,
    @Default(false) bool isPrivate,
  }) = _ParentIssueModel;
  factory ParentIssueModel.fromJson(Map<String, dynamic> json) =>
      _$ParentIssueModelFromJson(json);
}

// ── 파일 / 링크 ────────────────────────────────────────────────────────────────

@freezed
class IssueFileModel with _$IssueFileModel {
  @JsonSerializable(fieldRename: FieldRename.snake)
  const factory IssueFileModel({
    required int pk,
    required String file,
    required String fileName,
    @Default('') String fileType,
    int? fileSize,
    @Default('') String description,
    required String created,
    SimpleUserModel? creator,
  }) = _IssueFileModel;
  factory IssueFileModel.fromJson(Map<String, dynamic> json) =>
      _$IssueFileModelFromJson(json);
}

@freezed
class IssueLinkModel with _$IssueLinkModel {
  @JsonSerializable(fieldRename: FieldRename.snake)
  const factory IssueLinkModel({
    required int pk,
    required String link,
    required String name,
    @Default(0) int hit,
    required String created,
    SimpleUserModel? creator,
  }) = _IssueLinkModel;
  factory IssueLinkModel.fromJson(Map<String, dynamic> json) =>
      _$IssueLinkModelFromJson(json);
}

// ── 하위업무 / 연결업무 ────────────────────────────────────────────────────────

@freezed
class SubIssueModel with _$SubIssueModel {
  @JsonSerializable(fieldRename: FieldRename.snake)
  const factory SubIssueModel({
    required int pk,
    required SimpleProjectModel project,
    required String subject,
    required IssueTrackerModel tracker,
    required String status,
    SimpleUserModel? assignedTo,
    @Default([]) List<SimpleUserModel> watchers,
    int? priority,
    String? startDate,
    String? dueDate,
    @Default(0) int doneRatio,
    String? closed,
  }) = _SubIssueModel;
  factory SubIssueModel.fromJson(Map<String, dynamic> json) =>
      _$SubIssueModelFromJson(json);
}

@freezed
class IssueInRelationModel with _$IssueInRelationModel {
  @JsonSerializable(fieldRename: FieldRename.snake)
  const factory IssueInRelationModel({
    required int pk,
    required SimpleProjectModel project,
    required String subject,
    required IssueTrackerModel tracker,
    required String status,
    SimpleUserModel? assignedTo,
    @Default([]) List<SimpleUserModel> watchers,
    int? priority,
    String? startDate,
    String? dueDate,
    @Default(0) int doneRatio,
    String? closed,
  }) = _IssueInRelationModel;
  factory IssueInRelationModel.fromJson(Map<String, dynamic> json) =>
      _$IssueInRelationModelFromJson(json);
}

@freezed
class IssueRelationModel with _$IssueRelationModel {
  @JsonSerializable(fieldRename: FieldRename.snake)
  const factory IssueRelationModel({
    int? pk,
    IssueInRelationModel? issue,
    int? delay,
  }) = _IssueRelationModel;
  factory IssueRelationModel.fromJson(Map<String, dynamic> json) =>
      _$IssueRelationModelFromJson(json);
}

// ── 변경 로그 (IssueLogEntry) ──────────────────────────────────────────────────

class IssueLogCommentModel {
  final int pk;
  final String content;
  final bool isPrivate;
  final bool isBlocked;
  final SimpleUserModel? creator;

  const IssueLogCommentModel({
    required this.pk,
    required this.content,
    this.isPrivate = false,
    this.isBlocked = false,
    this.creator,
  });

  factory IssueLogCommentModel.fromJson(Map<String, dynamic> json) {
    return IssueLogCommentModel(
      pk: json['pk'] as int? ?? 0,
      content: json['content']?.toString() ?? '',
      isPrivate: json['is_private'] as bool? ?? false,
      isBlocked: json['is_blocked'] as bool? ?? false,
      creator: json['creator'] != null
          ? SimpleUserModel.fromJson(json['creator'] as Map<String, dynamic>)
          : null,
    );
  }

  Map<String, dynamic> toJson() => {
        'pk': pk,
        'content': content,
        'is_private': isPrivate,
        'is_blocked': isBlocked,
        'creator': creator?.toJson(),
      };
}

class IssueLogEntryModel {
  final int pk;
  final int logId;
  final String action;
  final IssueLogCommentModel? comment;
  final String details;
  final String diff;
  final String timestamp;
  final SimpleUserModel? creator;

  const IssueLogEntryModel({
    required this.pk,
    required this.logId,
    required this.action,
    this.comment,
    this.details = '',
    this.diff = '',
    required this.timestamp,
    this.creator,
  });

  factory IssueLogEntryModel.fromJson(Map<String, dynamic> json) {
    return IssueLogEntryModel(
      pk: json['pk'] as int? ?? 0,
      logId: json['log_id'] as int? ?? 0,
      action: json['action']?.toString() ?? '',
      comment: json['comment'] != null
          ? IssueLogCommentModel.fromJson(
              json['comment'] as Map<String, dynamic>)
          : null,
      details: json['details']?.toString() ?? '',
      diff: json['diff']?.toString() ?? '',
      timestamp: json['timestamp']?.toString() ?? '',
      creator: json['creator'] != null
          ? SimpleUserModel.fromJson(json['creator'] as Map<String, dynamic>)
          : null,
    );
  }

  Map<String, dynamic> toJson() => {
        'pk': pk,
        'log_id': logId,
        'action': action,
        'comment': comment?.toJson(),
        'details': details,
        'diff': diff,
        'timestamp': timestamp,
        'creator': creator?.toJson(),
      };
}

// ── 댓글 ───────────────────────────────────────────────────────────────────────

@freezed
class IssueCommentModel with _$IssueCommentModel {
  @JsonSerializable(fieldRename: FieldRename.snake)
  const factory IssueCommentModel({
    required int pk,
    required String content,
    @Default(false) bool isPrivate,
    @Default(false) bool isBlocked,
    required String created,
    required String updated,
    required SimpleUserModel creator,
  }) = _IssueCommentModel;
  factory IssueCommentModel.fromJson(Map<String, dynamic> json) =>
      _$IssueCommentModelFromJson(json);
}

// ── 메인 Issue 모델 ────────────────────────────────────────────────────────────

@freezed
class IssueModel with _$IssueModel {
  @JsonSerializable(fieldRename: FieldRename.snake)
  const factory IssueModel({
    required int pk,
    required SimpleProjectModel project,
    required IssueTrackerModel tracker,
    required IssueStatusModel status,
    required IssuePriorityModel priority,
    required String subject,
    @Default('') String description,
    int? category,
    IssueVersionModel? fixedVersion,
    SimpleUserModel? assignedTo,
    ParentIssueModel? parent,
    @Default([]) List<SimpleUserModel> watchers,
    @Default(false) bool isPrivate,
    String? expectedDuration,
    @Default('') String expectedDurationDisplay,
    required String startDate,
    String? dueDate,
    int? meeting,
    MeetingDescModel? meetingDesc,
    @Default(0) int doneRatio,
    String? closed,
    @Default([]) List<IssueFileModel> files,
    @Default([]) List<IssueLinkModel> links,
    @Default([]) List<SubIssueModel> subIssues,
    @Default([]) List<IssueRelationModel> outgoingRelations,
    IssueRelationModel? incomingRelation,
    SimpleUserModel? creator,
    int? updater,
    required String created,
    required String updated,
  }) = _IssueModel;
  factory IssueModel.fromJson(Map<String, dynamic> json) =>
      _$IssueModelFromJson(json);
}

// ── 목록 응답 ──────────────────────────────────────────────────────────────────

@freezed
class IssueListResponse with _$IssueListResponse {
  @JsonSerializable(fieldRename: FieldRename.snake)
  const factory IssueListResponse({
    required int count,
    String? next,
    String? previous,
    required List<IssueModel> results,
  }) = _IssueListResponse;
  factory IssueListResponse.fromJson(Map<String, dynamic> json) =>
      _$IssueListResponseFromJson(json);
}

// ── 필터 모델 ──────────────────────────────────────────────────────────────────

class IssueFilterModel {
  final dynamic assignedTo; // int PK 또는 'me'
  final String? projectSlug;
  final String? statusExclude;
  final bool? statusClosed; // true: 완료됨, false: 진행 중
  final String ordering;
  final int page;

  const IssueFilterModel({
    this.assignedTo,
    this.projectSlug,
    this.statusExclude,
    this.statusClosed,
    this.ordering = '-updated',
    this.page = 1,
  });

  Map<String, dynamic> toQueryParams() {
    final params = <String, dynamic>{
      'ordering': ordering,
      'page': page,
    };
    if (assignedTo != null) params['assigned_to'] = assignedTo;
    if (projectSlug != null) params['project__search'] = projectSlug;
    if (statusExclude != null) params['status__exclude'] = statusExclude;
    if (statusClosed != null) params['status__closed'] = statusClosed;
    return params;
  }

  IssueFilterModel copyWith({
    dynamic assignedTo,
    String? projectSlug,
    String? statusExclude,
    bool? statusClosed,
    String? ordering,
    int? page,
    bool clearAssignedTo = false,
    bool clearProjectSlug = false,
    bool clearStatusExclude = false,
    bool clearStatusClosed = false,
  }) {
    return IssueFilterModel(
      assignedTo: clearAssignedTo ? null : assignedTo ?? this.assignedTo,
      projectSlug: clearProjectSlug ? null : projectSlug ?? this.projectSlug,
      statusExclude: clearStatusExclude ? null : statusExclude ?? this.statusExclude,
      statusClosed: clearStatusClosed ? null : statusClosed ?? this.statusClosed,
      ordering: ordering ?? this.ordering,
      page: page ?? this.page,
    );
  }
}
