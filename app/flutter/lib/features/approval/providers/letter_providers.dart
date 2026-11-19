import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/providers/auth_provider.dart';
import '../data/letter_repository.dart';
import '../data/models/letter_model.dart';

/// 공문 목록 필터 상태 (상태: 전체, 결재대기, 승인완료, 발송완료)
final letterFilterStatusProvider = StateProvider<String?>((ref) {
  ref.watch(authSessionVersionProvider);
  return null;
});

/// 공문 검색어 상태
final letterSearchQueryProvider = StateProvider<String>((ref) {
  ref.watch(authSessionVersionProvider);
  return '';
});

/// 공문 페이지 번호 상태
final officialLetterPageProvider = StateProvider.autoDispose<int>((ref) => 1);

/// 공문 목록 프로바이더
final officialLettersProvider = FutureProvider.autoDispose<OfficialLetterListResponseModel>((ref) async {
  final repo = ref.watch(letterRepositoryProvider);
  final status = ref.watch(letterFilterStatusProvider);
  final search = ref.watch(letterSearchQueryProvider);
  final page = ref.watch(officialLetterPageProvider);

  return repo.fetchLetters(
    page: page,
    approvalStatus: status,
    search: search,
  );
});

/// 공문 상세 프로바이더
final officialLetterDetailProvider = FutureProvider.autoDispose.family<OfficialLetterModel, int>((ref, id) async {
  final repo = ref.watch(letterRepositoryProvider);
  return repo.fetchLetterDetail(id);
});
