import 'package:freezed_annotation/freezed_annotation.dart';
import '../../../../core/models/common_models.dart';

part 'meeting_model.freezed.dart';
part 'meeting_model.g.dart';

// ── 카테고리 ───────────────────────────────────────────────────────────────────

@freezed
class MeetingCategoryModel with _$MeetingCategoryModel {
  const factory MeetingCategoryModel({
    required int pk,
    required String name,
    @Default('#6366F1') String color,
    @Default(0) int order,
  }) = _MeetingCategoryModel;
  factory MeetingCategoryModel.fromJson(Map<String, dynamic> json) =>
      _$MeetingCategoryModelFromJson(json);
}

// ── 파일 / 링크 ────────────────────────────────────────────────────────────────

@freezed
class MeetingFileModel with _$MeetingFileModel {
  const factory MeetingFileModel({
    required int pk,
    required String file,
    required String fileName,
    @Default('') String fileType,
    int? fileSize,
    @Default('') String description,
    required String created,
    SimpleUserModel? creator,
  }) = _MeetingFileModel;
  factory MeetingFileModel.fromJson(Map<String, dynamic> json) =>
      _$MeetingFileModelFromJson(json);
}

@freezed
class MeetingLinkModel with _$MeetingLinkModel {
  const factory MeetingLinkModel({
    required int pk,
    required String link,
    required String name,
    @Default(0) int hit,
    required String created,
    SimpleUserModel? creator,
  }) = _MeetingLinkModel;
  factory MeetingLinkModel.fromJson(Map<String, dynamic> json) =>
      _$MeetingLinkModelFromJson(json);
}

// ── 회의 내 연결된 업무 (경량) ──────────────────────────────────────────────────

@freezed
class IssueInMeetingModel with _$IssueInMeetingModel {
  const factory IssueInMeetingModel({
    required int pk,
    required String project, // slug
    required String subject,
    required String status,
    SimpleUserModel? assignedTo,
    String? closed,
  }) = _IssueInMeetingModel;
  factory IssueInMeetingModel.fromJson(Map<String, dynamic> json) =>
      _$IssueInMeetingModelFromJson(json);
}

// ── 메인 Meeting 모델 ──────────────────────────────────────────────────────────

@freezed
class MeetingModel with _$MeetingModel {
  const factory MeetingModel({
    required int pk,
    required int project,
    required SimpleProjectModel projectDesc,
    required String title,
    int? category,
    MeetingCategoryModel? categoryDesc,
    @Default('1') String status,
    @Default('예정') String statusDisplay,
    @Default(false) bool isConfirmed,
    @Default('') String agenda,
    @Default('') String content,
    @Default('') String decisions,
    @Default('') String actionItems,
    required String meetingDate,
    @Default([]) List<int> attendees,
    @Default([]) List<SimpleUserModel> attendeesDesc,
    @Default('') String otherAttendees,
    @Default([]) List<MeetingFileModel> files,
    @Default([]) List<MeetingLinkModel> links,
    @Default([]) List<IssueInMeetingModel> issues,
    SimpleUserModel? creator,
    SimpleUserModel? updater,
    required String created,
    required String updated,
  }) = _MeetingModel;
  factory MeetingModel.fromJson(Map<String, dynamic> json) =>
      _$MeetingModelFromJson(json);
}

// ── 목록 응답 ──────────────────────────────────────────────────────────────────

@freezed
class MeetingListResponse with _$MeetingListResponse {
  const factory MeetingListResponse({
    required int count,
    String? next,
    String? previous,
    required List<MeetingModel> results,
  }) = _MeetingListResponse;
  factory MeetingListResponse.fromJson(Map<String, dynamic> json) =>
      _$MeetingListResponseFromJson(json);
}

// ── 필터 모델 ──────────────────────────────────────────────────────────────────

class MeetingFilterModel {
  final String? projectSlug;
  final String? status;
  final String ordering;
  final int page;

  const MeetingFilterModel({
    this.projectSlug,
    this.status,
    this.ordering = '-meeting_date',
    this.page = 1,
  });

  Map<String, dynamic> toQueryParams() {
    final params = <String, dynamic>{
      'ordering': ordering,
      'page': page,
    };
    if (projectSlug != null) params['project__search'] = projectSlug;
    if (status != null) params['status'] = status;
    return params;
  }

  MeetingFilterModel copyWith({
    String? projectSlug,
    String? status,
    String? ordering,
    int? page,
    bool clearProjectSlug = false,
    bool clearStatus = false,
  }) {
    return MeetingFilterModel(
      projectSlug: clearProjectSlug ? null : projectSlug ?? this.projectSlug,
      status: clearStatus ? null : status ?? this.status,
      ordering: ordering ?? this.ordering,
      page: page ?? this.page,
    );
  }
}
