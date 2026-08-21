import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/approval_repository.dart';
import '../data/models/approval_model.dart';

// ── 1. 결재 대기 목록 프로바이더 (내 결재 차례) ──────────────────────────────────
final pendingApprovalsProvider = FutureProvider.autoDispose<List<ApprovalDocumentModel>>((ref) async {
  final repo = ref.watch(approvalRepositoryProvider);
  return repo.fetchMyPending();
});

// ── 2. 결재 대기 건수 프로바이더 (사이드바 / 탭 배지용) ─────────────────────────
final pendingApprovalCountProvider = Provider.autoDispose<int>((ref) {
  final pending = ref.watch(pendingApprovalsProvider);
  return pending.when(
    data: (list) => list.length,
    loading: () => 0,
    error: (_, __) => 0,
  );
});

// ── 3. 내 기안 문서 목록 프로바이더 ──────────────────────────────────────────
final draftedApprovalsProvider = FutureProvider.autoDispose<List<ApprovalDocumentModel>>((ref) async {
  final repo = ref.watch(approvalRepositoryProvider);
  return repo.fetchMyDrafted();
});

// ── 4. 내 결재 완료 문서 목록 프로바이더 ───────────────────────────────────────
final approvedApprovalsProvider = FutureProvider.autoDispose<List<ApprovalDocumentModel>>((ref) async {
  final repo = ref.watch(approvalRepositoryProvider);
  return repo.fetchMyApproved();
});

// ── 5. 내가 참조된 문서 목록 프로바이더 ─────────────────────────────────────────
final observedApprovalsProvider = FutureProvider.autoDispose<List<ApprovalDocumentModel>>((ref) async {
  final repo = ref.watch(approvalRepositoryProvider);
  return repo.fetchMyObserved();
});

// ── 6. 전사 결재 문서 필터 상태 모델 & 프로바이더 ──────────────────────────────
class AllApprovalsFilter {
  final int page;
  final int? category;
  final int? docType;
  final String? status;
  final int? department;
  final String? startDate;
  final String? endDate;
  final String? search;

  const AllApprovalsFilter({
    this.page = 1,
    this.category,
    this.docType,
    this.status,
    this.department,
    this.startDate,
    this.endDate,
    this.search,
  });

  AllApprovalsFilter copyWith({
    int? page,
    int? category,
    int? docType,
    String? status,
    int? department,
    String? startDate,
    String? endDate,
    String? search,
    bool clearCategory = false,
    bool clearDocType = false,
    bool clearStatus = false,
    bool clearDepartment = false,
  }) {
    return AllApprovalsFilter(
      page: page ?? this.page,
      category: clearCategory ? null : (category ?? this.category),
      docType: clearDocType ? null : (docType ?? this.docType),
      status: clearStatus ? null : (status ?? this.status),
      department: clearDepartment ? null : (department ?? this.department),
      startDate: startDate ?? this.startDate,
      endDate: endDate ?? this.endDate,
      search: search ?? this.search,
    );
  }
}

final allApprovalsFilterProvider = StateProvider.autoDispose<AllApprovalsFilter>((ref) {
  return const AllApprovalsFilter();
});

final allApprovalsProvider = FutureProvider.autoDispose<ApprovalDocumentListResponse>((ref) async {
  final repo = ref.watch(approvalRepositoryProvider);
  final filter = ref.watch(allApprovalsFilterProvider);
  return repo.fetchAllDocuments(
    page: filter.page,
    category: filter.category,
    docType: filter.docType,
    status: filter.status,
    department: filter.department,
    startDate: filter.startDate,
    endDate: filter.endDate,
    search: filter.search,
  );
});

// ── 7. 문서 상세 프로바이더 ──────────────────────────────────────────────────
final approvalDetailProvider = FutureProvider.autoDispose.family<ApprovalDocumentModel, int>((ref, docId) async {
  final repo = ref.watch(approvalRepositoryProvider);
  return repo.fetchDocumentDetail(docId);
});

// ── 8. 카테고리 / 문서 유형 / 보직 프로바이더 ──────────────────────────────────
final docCategoriesProvider = FutureProvider.autoDispose<List<DocCategoryModel>>((ref) async {
  final repo = ref.watch(approvalRepositoryProvider);
  return repo.fetchDocCategories();
});

final forDraftDocTypesProvider = FutureProvider.autoDispose.family<List<DocumentTypeModel>, int?>((ref, assignmentId) async {
  final repo = ref.watch(approvalRepositoryProvider);
  return repo.fetchForDraftDocTypes(assignmentId: assignmentId);
});

final myAssignmentsProvider = FutureProvider.autoDispose<List<StaffAssignmentItemModel>>((ref) async {
  final repo = ref.watch(approvalRepositoryProvider);
  return repo.fetchMyAssignments();
});

// ── 9. 결재 액션 컨트롤러 (승인 / 반려 / 의견 / 상신 / 회수) ──────────────────
class ApprovalActionController extends StateNotifier<AsyncValue<void>> {
  final ApprovalRepository _repo;
  final Ref _ref;

  ApprovalActionController(this._repo, this._ref) : super(const AsyncValue.data(null));

  /// 결재 상신 (Draft -> Pending)
  Future<ApprovalDocumentModel?> submit(int docId) async {
    state = const AsyncValue.loading();
    try {
      final doc = await _repo.submitDocument(docId);
      _ref.invalidate(pendingApprovalsProvider);
      _ref.invalidate(draftedApprovalsProvider);
      _ref.invalidate(approvalDetailProvider(docId));
      state = const AsyncValue.data(null);
      return doc;
    } catch (e, st) {
      state = AsyncValue.error(e, st);
      rethrow;
    }
  }

  /// 결재 승인
  Future<String?> approve(int docId, {String? comment}) async {
    state = const AsyncValue.loading();
    try {
      final msg = await _repo.actDocument(docId, action: 'approved', comment: comment);
      _ref.invalidate(pendingApprovalsProvider);
      _ref.invalidate(approvedApprovalsProvider);
      _ref.invalidate(allApprovalsProvider);
      _ref.invalidate(approvalDetailProvider(docId));
      state = const AsyncValue.data(null);
      return msg;
    } catch (e, st) {
      state = AsyncValue.error(e, st);
      rethrow;
    }
  }

  /// 결재 반려
  Future<String?> reject(int docId, {required String comment}) async {
    state = const AsyncValue.loading();
    try {
      final msg = await _repo.actDocument(docId, action: 'rejected', comment: comment);
      _ref.invalidate(pendingApprovalsProvider);
      _ref.invalidate(draftedApprovalsProvider);
      _ref.invalidate(allApprovalsProvider);
      _ref.invalidate(approvalDetailProvider(docId));
      state = const AsyncValue.data(null);
      return msg;
    } catch (e, st) {
      state = AsyncValue.error(e, st);
      rethrow;
    }
  }

  /// 결재 의견 등록
  Future<String?> addComment(int docId, {required String comment}) async {
    state = const AsyncValue.loading();
    try {
      final msg = await _repo.actDocument(docId, action: 'commented', comment: comment);
      _ref.invalidate(approvalDetailProvider(docId));
      state = const AsyncValue.data(null);
      return msg;
    } catch (e, st) {
      state = AsyncValue.error(e, st);
      rethrow;
    }
  }

  /// 기안 회수/취소
  Future<String?> cancel(int docId) async {
    state = const AsyncValue.loading();
    try {
      final msg = await _repo.cancelDocument(docId);
      _ref.invalidate(pendingApprovalsProvider);
      _ref.invalidate(draftedApprovalsProvider);
      _ref.invalidate(approvalDetailProvider(docId));
      state = const AsyncValue.data(null);
      return msg;
    } catch (e, st) {
      state = AsyncValue.error(e, st);
      rethrow;
    }
  }
}

final approvalActionControllerProvider = StateNotifierProvider.autoDispose<ApprovalActionController, AsyncValue<void>>((ref) {
  final repo = ref.watch(approvalRepositoryProvider);
  return ApprovalActionController(repo, ref);
});
