import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/constants/api_endpoints.dart';
import '../../../core/providers/dio_provider.dart';
import 'models/project_model.dart';

class ProjectRepository {
  final Dio _dio;

  ProjectRepository(this._dio);

  /// 프로젝트 목록 조회
  Future<List<ProjectModel>> fetchProjects() async {
    final response = await _dio.get(ApiEndpoints.projects);
    final data = response.data;
    if (data is Map && data.containsKey('results')) {
      return (data['results'] as List)
          .map((e) => ProjectModel.fromJson(e as Map<String, dynamic>))
          .toList();
    }
    return (data as List)
        .map((e) => ProjectModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// 내 워크스페이스(프로젝트) 목록 조회 (/api/v1/issue-project/my_projects/)
  Future<List<ProjectModel>> fetchMyProjects() async {
    final response = await _dio.get(ApiEndpoints.projectMyProjects);
    final data = response.data;
    if (data is Map && data.containsKey('results')) {
      return (data['results'] as List)
          .map((e) => ProjectModel.fromJson(e as Map<String, dynamic>))
          .toList();
    }
    return (data as List)
        .map((e) => ProjectModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// 프로젝트 상세 조회
  Future<ProjectModel> fetchProjectDetail(String slug) async {
    final url = ApiEndpoints.resolve(ApiEndpoints.projectDetail, {'slug': slug});
    final response = await _dio.get(url);
    return ProjectModel.fromJson(response.data as Map<String, dynamic>);
  }

  /// 🏢 부동산 개발 프로젝트 상세 정보 조회 (/api/v1/project/{id}/)
  Future<RealEstateProjectDetailModel?> fetchRealEstateProjectDetail(int projectId) async {
    try {
      final response = await _dio.get('/api/v1/project/$projectId/');
      if (response.data is Map<String, dynamic>) {
        return RealEstateProjectDetailModel.fromJson(response.data as Map<String, dynamic>);
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  /// ✏️ 부동산 개발 프로젝트 기본 정보 및 개요 수정 (/api/v1/project/{id}/)
  Future<String?> updateRealEstateProject({
    required int projectId,
    required Map<String, dynamic> payload,
  }) async {
    try {
      final response = await _dio.patch('/api/v1/project/$projectId/', data: payload);
      if (response.statusCode == 200 || response.statusCode == 204) {
        return null; // 성공
      }
      return '서버 응답 오류: ${response.statusCode}';
    } on DioException catch (e) {
      if (e.response?.data is Map) {
        final map = e.response!.data as Map;
        return map.entries.map((entry) => '${entry.key}: ${entry.value}').join('\n');
      }
      return e.message ?? '프로젝트 정보 수정에 실패했습니다.';
    } catch (e) {
      return e.toString();
    }
  }
}

/// Riverpod 프로바이더
final projectRepositoryProvider = Provider<ProjectRepository>((ref) {
  return ProjectRepository(ref.watch(dioProvider));
});
