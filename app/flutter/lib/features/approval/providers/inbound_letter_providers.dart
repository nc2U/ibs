import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/inbound_letter_repository.dart';
import '../data/models/inbound_letter_model.dart';

/// 수신 공문 목록 필터 상태 (상태: 전체, 접수, 처리중, 회신완료, 종결)
final inboundLetterFilterStatusProvider = StateProvider<String?>((ref) => null);

/// 수신 공문 검색어 상태
final inboundLetterSearchQueryProvider = StateProvider<String>((ref) => '');

/// 수신 공문 목록 프로바이더
final inboundLettersProvider = FutureProvider.autoDispose<InboundLetterListResponseModel>((ref) async {
  final repo = ref.watch(inboundLetterRepositoryProvider);
  final status = ref.watch(inboundLetterFilterStatusProvider);
  final search = ref.watch(inboundLetterSearchQueryProvider);

  return repo.fetchInboundLetters(
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
