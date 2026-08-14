import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/constants/api_endpoints.dart';
import '../../../core/providers/dio_provider.dart';
import 'models/search_model.dart';

class SearchRepository {
  final Dio _dio;

  SearchRepository(this._dio);

  /// 통합 검색 실행 (/api/v1/issue-search/run/)
  /// - [query]: 검색어 (2글자 이상)
  /// - [scope]: 'all' | 'project'
  /// - [slug]: 프로젝트 slug (scope == 'project'일 때)
  /// - [targets]: 검색 대상 목록 ('issues', 'meetings', 'documents', 'news', 'posts', 'comments')
  Future<UnifiedSearchResponse> runSearch({
    required String query,
    String scope = 'all',
    String? slug,
    List<String>? targets,
  }) async {
    final queryParams = <String, dynamic>{
      'q': query,
      'scope': scope,
    };

    if (scope == 'project' && slug != null && slug.isNotEmpty) {
      queryParams['slug'] = slug;
    }

    if (targets != null && targets.isNotEmpty) {
      queryParams['t'] = targets;
    }

    final response = await _dio.get(
      ApiEndpoints.issueSearchRun,
      queryParameters: queryParams,
    );

    return UnifiedSearchResponse.fromJson(response.data as Map<String, dynamic>);
  }
}

/// SearchRepository Riverpod 프로바이더
final searchRepositoryProvider = Provider<SearchRepository>((ref) {
  return SearchRepository(ref.watch(dioProvider));
});
