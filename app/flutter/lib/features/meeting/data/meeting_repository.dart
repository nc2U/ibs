import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/constants/api_endpoints.dart';
import '../../../core/models/common_models.dart';
import '../../../core/providers/dio_provider.dart';
import 'models/meeting_model.dart';

class MeetingRepository {
  final Dio _dio;

  MeetingRepository(this._dio);

  /// 회의 목록 조회
  Future<MeetingListResponse> fetchMeetings(MeetingFilterModel filter) async {
    final response = await _dio.get(
      ApiEndpoints.meetings,
      queryParameters: filter.toQueryParams(),
    );
    return MeetingListResponse.fromJson(response.data as Map<String, dynamic>);
  }

  /// 회의 상세 조회
  Future<MeetingModel> fetchMeetingDetail(int id) async {
    final url = ApiEndpoints.resolve(ApiEndpoints.meetingDetail, {'id': id});
    final response = await _dio.get(url);
    return MeetingModel.fromJson(response.data as Map<String, dynamic>);
  }

  /// 회의 생성 (POST)
  Future<MeetingModel> createMeeting(Map<String, dynamic> data) async {
    final response = await _dio.post(ApiEndpoints.meetings, data: data);
    return MeetingModel.fromJson(response.data as Map<String, dynamic>);
  }

  /// 회의 수정 (PATCH)
  Future<MeetingModel> updateMeeting(int meetingId, Map<String, dynamic> data) async {
    final url = ApiEndpoints.resolve(ApiEndpoints.meetingDetail, {'id': meetingId});
    final response = await _dio.patch(url, data: data);
    return MeetingModel.fromJson(response.data as Map<String, dynamic>);
  }

  /// 회의 카테고리 목록 조회
  Future<List<MeetingCategoryModel>> fetchCategories({int? projectPk}) async {
    final params = <String, dynamic>{};
    if (projectPk != null) params['project'] = projectPk;
    final response = await _dio.get(
      ApiEndpoints.meetingCategories,
      queryParameters: params,
    );
    final data = response.data;
    final list = data is List
        ? data
        : (data['results'] as List? ?? []);
    return list
        .map((json) => MeetingCategoryModel.fromJson(json as Map<String, dynamic>))
        .toList();
  }

  /// 시스템 전체 사용자 목록 조회 (중복 제거)
  Future<List<SimpleUserModel>> fetchMembers({int? projectPk}) async {
    final response = await _dio.get(ApiEndpoints.users);
    final data = response.data;
    final list = data is List
        ? data
        : (data['results'] as List? ?? []);

    final Map<int, SimpleUserModel> uniqueUsers = {};
    for (final json in list) {
      if (json is Map<String, dynamic>) {
        final user = SimpleUserModel.fromJson(json);
        uniqueUsers[user.pk] = user;
      }
    }
    return uniqueUsers.values.toList();
  }

  /// 회의 확정/확정취소 토글 (POST /api/v1/meeting/{id}/confirm/)
  Future<bool> toggleConfirm(int meetingId) async {
    final url = '${ApiEndpoints.meetings}$meetingId/confirm/';
    final response = await _dio.post(url);
    final data = response.data as Map<String, dynamic>;
    return data['is_confirmed'] as bool? ?? false;
  }
}

/// Riverpod 프로바이더
final meetingRepositoryProvider = Provider<MeetingRepository>((ref) {
  return MeetingRepository(ref.watch(dioProvider));
});
