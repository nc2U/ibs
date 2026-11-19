import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/providers/auth_provider.dart';
import '../data/inbound_letter_repository.dart';
import '../data/models/inbound_letter_model.dart';

/// 수신 공문 목록 필터 상태 (상태: 전체, 접수, 처리중, 회신완료, 종결)
final inboundLetterFilterStatusProvider = StateProvider<String?>((ref) {
  ref.watch(authSessionVersionProvider);
  return null;
});

/// 수신 공문 검색어 상태
final inboundLetterSearchQueryProvider = StateProvider<String>((ref) {
  ref.watch(authSessionVersionProvider);
  return '';
});

/// 수신 공문 페이지 번호 상태
final inboundLetterPageProvider = StateProvider.autoDispose<int>((ref) => 1);

/// 수신 공문 목록 프로바이더
final inboundLettersProvider = FutureProvider.autoDispose<InboundLetterListResponseModel>((ref) async {
  final repo = ref.watch(inboundLetterRepositoryProvider);
  final status = ref.watch(inboundLetterFilterStatusProvider);
  final search = ref.watch(inboundLetterSearchQueryProvider);
  final page = ref.watch(inboundLetterPageProvider);

  return repo.fetchInboundLetters(
    page: page,
    status: status,
    search: search,
  );
});

/// 수신 공문 상세 프로바이더
final inboundLetterDetailProvider =
    FutureProvider.autoDispose.family<InboundLetterModel, int>((ref, id) async {
  final repo = ref.watch(inboundLetterRepositoryProvider);
  return repo.fetchInboundLetterDetail(id);
});
