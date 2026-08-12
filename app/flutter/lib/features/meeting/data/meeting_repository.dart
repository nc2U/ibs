import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/constants/api_endpoints.dart';
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
}

/// Riverpod 프로바이더
final meetingRepositoryProvider = Provider<MeetingRepository>((ref) {
  return MeetingRepository(ref.watch(dioProvider));
});
