import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/providers/project_provider.dart';
import '../data/models/search_model.dart';
import '../data/search_repository.dart';

/// 현재 검색어
final searchQueryProvider = StateProvider<String>((ref) => '');

/// 검색 범위 ('all' | 'project')
final searchScopeProvider = StateProvider<String>((ref) => 'all');

/// 검색 대상 탭 ('all' | 'issues' | 'meetings' | 'documents' | 'news' | 'posts')
final searchTargetTabProvider = StateProvider<String>((ref) => 'all');

/// 통합 검색 결과 비동기 프로바이더
final searchResultsProvider = FutureProvider<UnifiedSearchResponse?>((ref) async {
  final query = ref.watch(searchQueryProvider).trim();
  if (query.length < 2) return null;

  final scope = ref.watch(searchScopeProvider);
  final selectedProj = ref.watch(selectedProjectProvider);

  return ref.watch(searchRepositoryProvider).runSearch(
        query: query,
        scope: scope,
        slug: scope == 'project' ? selectedProj?.slug : null,
      );
});
