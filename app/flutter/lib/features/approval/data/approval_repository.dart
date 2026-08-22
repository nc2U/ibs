import 'dart:io';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:path_provider/path_provider.dart';
import '../../../core/constants/api_endpoints.dart';
import '../../../core/providers/dio_provider.dart';
import 'models/approval_model.dart';

class ApprovalRepository {
  final Dio _dio;

  ApprovalRepository(this._dio);

  /// 1. 카테고리 목록 조회
  Future<List<DocCategoryModel>> fetchDocCategories() async {
    final res = await _dio.get(ApiEndpoints.approvalDocCategories);
    final list = (res.data is List) ? res.data as List : ((res.data as Map<String, dynamic>)['results'] as List? ?? []);
    return list.map((e) => DocCategoryModel.fromJson(e as Map<String, dynamic>)).toList();
  }

  /// 2. 문서 유형 목록 조회
  Future<List<DocumentTypeModel>> fetchDocTypes({int? categoryId}) async {
    final query = <String, dynamic>{};
    if (categoryId != null) query['category_id'] = categoryId;
    final res = await _dio.get(ApiEndpoints.approvalDocTypes, queryParameters: query);
    final list = (res.data is List) ? res.data as List : ((res.data as Map<String, dynamic>)['results'] as List? ?? []);
    return list.map((e) => DocumentTypeModel.fromJson(e as Map<String, dynamic>)).toList();
  }

  /// 3. 기안용 허용 문서 유형 목록 조회
  Future<List<DocumentTypeModel>> fetchForDraftDocTypes({int? assignmentId}) async {
    final query = <String, dynamic>{};
    if (assignmentId != null) query['assignment'] = assignmentId;
    final res = await _dio.get(ApiEndpoints.approvalDocTypesForDraft, queryParameters: query);
    final list = (res.data is List) ? res.data as List : ((res.data as Map<String, dynamic>)['results'] as List? ?? []);
    return list.map((e) => DocumentTypeModel.fromJson(e as Map<String, dynamic>)).toList();
  }

  /// 4. 기안자 보직/겸직 목록 조회
  Future<List<StaffAssignmentItemModel>> fetchMyAssignments() async {
    final res = await _dio.get(ApiEndpoints.approvalMyAssignments);
    final list = (res.data is List) ? res.data as List : ((res.data as Map<String, dynamic>)['results'] as List? ?? []);
    return list.map((e) => StaffAssignmentItemModel.fromJson(e as Map<String, dynamic>)).toList();
  }

  /// 5. 동적 결재선 미리보기 조회
  Future<List<RoutePreviewStepModel>> fetchRoutePreview({
    required int docTypeId,
    int? assignmentId,
    dynamic amount,
  }) async {
    final query = <String, dynamic>{'doc_type': docTypeId};
    if (assignmentId != null) query['assignment'] = assignmentId;
    if (amount != null && amount.toString().isNotEmpty) query['amount'] = amount;

    final res = await _dio.get(ApiEndpoints.approvalPreviewRoute, queryParameters: query);
    final list = (res.data is List) ? res.data as List : ((res.data as Map<String, dynamic>)['results'] as List? ?? []);
    return list.map((e) => RoutePreviewStepModel.fromJson(e as Map<String, dynamic>)).toList();
  }

  /// 6. 결재 대기 문서 목록 조회 (내 결재 차례)
  Future<List<ApprovalDocumentModel>> fetchMyPending() async {
    final res = await _dio.get(ApiEndpoints.approvalMyPending);
    final list = (res.data is List) ? res.data as List : ((res.data as Map<String, dynamic>)['results'] as List? ?? []);
    return list.map((e) => ApprovalDocumentModel.fromJson(e as Map<String, dynamic>)).toList();
  }

  /// 7. 내 기안 문서 목록 조회
  Future<List<ApprovalDocumentModel>> fetchMyDrafted() async {
    final res = await _dio.get(ApiEndpoints.approvalMyDrafted);
    final list = (res.data is List) ? res.data as List : ((res.data as Map<String, dynamic>)['results'] as List? ?? []);
    return list.map((e) => ApprovalDocumentModel.fromJson(e as Map<String, dynamic>)).toList();
  }

  /// 8. 내 결재 완료 문서 목록 조회
  Future<List<ApprovalDocumentModel>> fetchMyApproved() async {
    final res = await _dio.get(ApiEndpoints.approvalMyApproved);
    final list = (res.data is List) ? res.data as List : ((res.data as Map<String, dynamic>)['results'] as List? ?? []);
    return list.map((e) => ApprovalDocumentModel.fromJson(e as Map<String, dynamic>)).toList();
  }

  /// 9. 내가 참조된 문서 목록 조회
  Future<List<ApprovalDocumentModel>> fetchMyObserved() async {
    final res = await _dio.get(ApiEndpoints.approvalMyObserved);
    final list = (res.data is List) ? res.data as List : ((res.data as Map<String, dynamic>)['results'] as List? ?? []);
    return list.map((e) => ApprovalDocumentModel.fromJson(e as Map<String, dynamic>)).toList();
  }

  /// 10. 전사 결재 문서 목록 조회 (관리자용)
  Future<ApprovalDocumentListResponse> fetchAllDocuments({
    int page = 1,
    int? category,
    int? docType,
    String? status,
    int? department,
    String? startDate,
    String? endDate,
    String? search,
  }) async {
    final query = <String, dynamic>{'page': page};
    if (category != null) query['category'] = category;
    if (docType != null) query['doc_type'] = docType;
    if (status != null && status.isNotEmpty) query['status'] = status;
    if (department != null) query['department'] = department;
    if (startDate != null && startDate.isNotEmpty) query['start_date'] = startDate;
    if (endDate != null && endDate.isNotEmpty) query['end_date'] = endDate;
    if (search != null && search.isNotEmpty) query['search'] = search;

    final res = await _dio.get(ApiEndpoints.approvalAllDocuments, queryParameters: query);
    return ApprovalDocumentListResponse.fromJson(res.data as Map<String, dynamic>);
  }

  /// 11. 문서 상세 조회
  Future<ApprovalDocumentModel> fetchDocumentDetail(int id) async {
    final url = ApiEndpoints.resolve(ApiEndpoints.approvalDocumentDetail, {'id': id});
    final res = await _dio.get(url);
    return ApprovalDocumentModel.fromJson(res.data as Map<String, dynamic>);
  }

  /// 12. 문서 기안 생성 (Multipart 또는 JSON)
  Future<ApprovalDocumentModel> createDocument(
    Map<String, dynamic> data, {
    List<String>? filePaths,
  }) async {
    if (filePaths != null && filePaths.isNotEmpty) {
      final formData = FormData();
      data.forEach((key, value) {
        if (value != null) {
          if (value is Map) {
            formData.fields.add(MapEntry(key, value.toString()));
          } else {
            formData.fields.add(MapEntry(key, value.toString()));
          }
        }
      });
      for (final path in filePaths) {
        formData.files.add(
          MapEntry(
            'files',
            await MultipartFile.fromFile(
              path,
              filename: path.split(Platform.pathSeparator).last,
            ),
          ),
        );
      }
      final res = await _dio.post(ApiEndpoints.approvalDocuments, data: formData);
      return ApprovalDocumentModel.fromJson(res.data as Map<String, dynamic>);
    } else {
      final res = await _dio.post(ApiEndpoints.approvalDocuments, data: data);
      return ApprovalDocumentModel.fromJson(res.data as Map<String, dynamic>);
    }
  }

  /// 13. 문서 수정
  Future<ApprovalDocumentModel> updateDocument(int id, Map<String, dynamic> data) async {
    final url = ApiEndpoints.resolve(ApiEndpoints.approvalDocumentDetail, {'id': id});
    final res = await _dio.patch(url, data: data);
    return ApprovalDocumentModel.fromJson(res.data as Map<String, dynamic>);
  }

  /// 14. 문서 삭제 (임시저장 문서)
  Future<void> deleteDocument(int id) async {
    final url = ApiEndpoints.resolve(ApiEndpoints.approvalDocumentDetail, {'id': id});
    await _dio.delete(url);
  }

  /// 15. 문서 상신 (Draft -> Pending)
  Future<ApprovalDocumentModel> submitDocument(int id) async {
    final url = ApiEndpoints.resolve(ApiEndpoints.approvalSubmit, {'id': id});
    final res = await _dio.post(url);
    return ApprovalDocumentModel.fromJson(res.data as Map<String, dynamic>);
  }

  /// 16. 결재 행동 수행 (승인 / 반려 / 의견)
  Future<String> actDocument(
    int id, {
    required String action, // approved, rejected, commented
    String? comment,
  }) async {
    final url = ApiEndpoints.resolve(ApiEndpoints.approvalAct, {'id': id});
    final res = await _dio.post(url, data: {
      'action': action,
      if (comment != null && comment.isNotEmpty) 'comment': comment,
    });
    if (res.data is Map && res.data['detail'] != null) {
      return res.data['detail'].toString();
    }
    return '처리되었습니다.';
  }

  /// 17. 기안 회수/취소
  Future<String> cancelDocument(int id) async {
    final url = ApiEndpoints.resolve(ApiEndpoints.approvalCancel, {'id': id});
    final res = await _dio.post(url);
    if (res.data is Map && res.data['detail'] != null) {
      return res.data['detail'].toString();
    }
    return '취소되었습니다.';
  }

  /// 18. 결재 문서 인쇄용 PDF 다운로드
  Future<String> downloadDocumentPdf(int docId, String title, {String? pdfUrl}) async {
    final downloadUrl = (pdfUrl != null && pdfUrl.isNotEmpty)
        ? pdfUrl
        : '/pdf/approval/document/$docId/';

    final res = await _dio.get(
      downloadUrl,
      options: Options(
        responseType: ResponseType.bytes,
        headers: {'Accept': 'application/pdf, */*'},
      ),
    );

    final tempDir = await getTemporaryDirectory();
    final sanitizedTitle = title.replaceAll(RegExp(r'[\\/:*?"<>|]'), '_');
    final filePath = '${tempDir.path}/전자결재_${sanitizedTitle}_#$docId.pdf';
    final file = File(filePath);
    await file.writeAsBytes(res.data as List<int>);
    return filePath;
  }
}

final approvalRepositoryProvider = Provider<ApprovalRepository>((ref) {
  final dio = ref.watch(dioProvider);
  return ApprovalRepository(dio);
});
