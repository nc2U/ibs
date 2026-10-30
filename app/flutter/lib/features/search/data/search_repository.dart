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
  /// - [scope]: 'all' (전체 워크스페이스) | 'my' (내 워크스페이스) | 'project' (선택된 워크스페이스)
  /// - [slug]: 워크스페이스 slug (scope == 'project'일 때)
  /// - [targets]: 검색 대상 목록 ('issues', 'meetings', 'documents', 'news', 'posts', 'comments')
  /// - [titleOnly]: 제목에서만 검색 여부 ('1' | '0')
  /// - [openedOnly]: 열린 업무만 검색 여부 ('1' | '0')
  /// - [attachMode]: 첨부파일 검색 모드 ('1': 제외, '2': 본문+첨부파일명/설명, '3': 첨부파일명만)
  /// - [cancelToken]: 진행 중인 이전 요청 취소 토큰
  Future<UnifiedSearchResponse> runSearch({
    required String query,
    String scope = 'all',
    String? slug,
    List<String>? targets,
    bool titleOnly = false,
    bool openedOnly = false,
    String attachMode = '1',
    CancelToken? cancelToken,
  }) async {
    final queryParams = <String, dynamic>{
      'q': query,
      'scope': scope,
      'title_only': titleOnly ? '1' : '0',
      'opened_only': openedOnly ? '1' : '0',
      'attach_mode': attachMode,
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
      cancelToken: cancelToken,
    );

    final data = response.data;
    if (data is Map<String, dynamic>) {
      return UnifiedSearchResponse.fromJson(data);
    }
    if (data is Map) {
      return UnifiedSearchResponse.fromJson(Map<String, dynamic>.from(data));
    }
    return const UnifiedSearchResponse();
  }
}

/// SearchRepository Riverpod 프로바이더
final searchRepositoryProvider = Provider<SearchRepository>((ref) {
  return SearchRepository(ref.watch(dioProvider));
});
