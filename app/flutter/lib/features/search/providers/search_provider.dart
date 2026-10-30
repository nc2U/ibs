import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../../../core/providers/auth_provider.dart';
import '../../../core/providers/project_provider.dart';
import '../data/models/search_model.dart';
import '../data/search_repository.dart';

/// 현재 검색어 (계정 변경/로그아웃 시 자동 초기화)
final searchQueryProvider = StateProvider<String>((ref) {
  ref.watch(currentUserIdProvider);
  return '';
});

/// 검색 범위 ('all' | 'my' | 'project')
final searchScopeProvider = StateProvider<String>((ref) {
  ref.watch(currentUserIdProvider);
  return 'all';
});

/// 실제 유효 검색 범위 (선택된 워크스페이스가 없을 때 'project'면 'all'로 폴백)
final effectiveSearchScopeProvider = Provider<String>((ref) {
  final scope = ref.watch(searchScopeProvider);
  final selectedProj = ref.watch(selectedProjectProvider);
  if (scope == 'project' && selectedProj == null) {
    return 'all';
  }
  return scope;
});

/// 검색 대상 탭 ('all' | 'issues' | 'meetings' | 'documents' | 'news' | 'posts' | 'comments')
final searchTargetTabProvider = StateProvider<String>((ref) {
  ref.watch(currentUserIdProvider);
  return 'all';
});

/// 상세 검색 옵션: 제목에서만 검색 여부
final searchTitleOnlyProvider = StateProvider<bool>((ref) {
  ref.watch(currentUserIdProvider);
  return false;
});

/// 상세 검색 옵션: 열린 업무만 검색 여부
final searchOpenedOnlyProvider = StateProvider<bool>((ref) {
  ref.watch(currentUserIdProvider);
  return false;
});

/// 상세 검색 옵션: 첨부파일 검색 모드 ('1': 제외, '2': 본문+첨부파일명/설명, '3': 첨부파일명만)
final searchAttachModeProvider = StateProvider<String>((ref) {
  ref.watch(currentUserIdProvider);
  return '1';
});

/// 통합 검색 결과 비동기 프로바이더 (CancelToken 및 사용자 세션 격리 적용)
final searchResultsProvider = FutureProvider<UnifiedSearchResponse?>((ref) async {
  final userId = ref.watch(currentUserIdProvider);
  if (userId == null) return null;

  final query = ref.watch(searchQueryProvider).trim();
  if (query.length < 2) return null;

  final effectiveScope = ref.watch(effectiveSearchScopeProvider);
  final selectedProj = ref.watch(selectedProjectProvider);
  final effectiveSlug = effectiveScope == 'project' ? selectedProj?.slug : null;
  final titleOnly = ref.watch(searchTitleOnlyProvider);
  final openedOnly = ref.watch(searchOpenedOnlyProvider);
  final attachMode = ref.watch(searchAttachModeProvider);

  final cancelToken = CancelToken();
  ref.onDispose(() {
    if (!cancelToken.isCancelled) {
      cancelToken.cancel('Superseded by new search parameters');
    }
  });

  return ref.watch(searchRepositoryProvider).runSearch(
        query: query,
        scope: effectiveScope,
        slug: effectiveSlug,
        titleOnly: titleOnly,
        openedOnly: openedOnly,
        attachMode: attachMode,
        cancelToken: cancelToken,
      );
});

/// 최근 검색어 목록 Notifier (최대 10개 유지 + 사용자별 로컬 스토리지 영속화)
class RecentSearchesNotifier extends StateNotifier<List<String>> {
  static const _storage = FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
  );

  final int? _userId;

  RecentSearchesNotifier(this._userId) : super(const []) {
    _loadFromStorage();
  }

  String get _storageKey => 'ibs_recent_searches_${_userId ?? "guest"}';

  Future<void> _loadFromStorage() async {
    if (_userId == null) return;
    try {
      final raw = await _storage.read(key: _storageKey);
      if (!mounted || raw == null || raw.isEmpty) return;
      final decoded = jsonDecode(raw);
      if (decoded is List) {
        final loaded = decoded
            .map((e) => e.toString().trim())
            .where((e) => e.length >= 2)
            .toList();
        // 로드 중 이미 추가된 항목이 있다면 앞에 유지하며 병합
        final merged = <String>[
          ...state,
          ...loaded.where((q) => !state.contains(q)),
        ].take(10).toList();
        state = merged;
      }
    } catch (_) {}
  }

  Future<void> _saveToStorage(List<String> items) async {
    if (_userId == null) return;
    try {
      await _storage.write(key: _storageKey, value: jsonEncode(items));
    } catch (_) {}
  }

  void addSearch(String query) {
    final trimmed = query.trim();
    if (trimmed.length < 2) return;
    final updated = [trimmed, ...state.where((q) => q != trimmed)].take(10).toList();
    state = updated;
    _saveToStorage(updated);
  }

  void removeSearch(String query) {
    final updated = state.where((q) => q != query).toList();
    state = updated;
    _saveToStorage(updated);
  }

  void clearAll() {
    state = const [];
    _saveToStorage(const []);
  }
}

final recentSearchesProvider =
    StateNotifierProvider<RecentSearchesNotifier, List<String>>((ref) {
  final userId = ref.watch(currentUserIdProvider);
  return RecentSearchesNotifier(userId);
});
