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
}

/// Riverpod 프로바이더
final projectRepositoryProvider = Provider<ProjectRepository>((ref) {
  return ProjectRepository(ref.watch(dioProvider));
});
