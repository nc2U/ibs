import 'dart:convert';
import 'dart:io';
import 'package:dio/dio.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:path_provider/path_provider.dart';
import '../../../core/constants/api_endpoints.dart';
import '../../../core/models/common_models.dart';
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

  Future<FormData> _buildDocumentFormData(
    Map<String, dynamic> data, {
    List<String>? filePaths,
    List<PlatformFile>? files,
  }) async {
    final formData = FormData();
    data.forEach((key, value) {
      if (value != null) {
        if (value is List) {
          if (value.isEmpty) {
            formData.fields.add(MapEntry(key, jsonEncode(value)));
          } else {
            for (final item in value) {
              formData.fields.add(MapEntry(key, item.toString()));
            }
          }
        } else if (value is Map) {
          formData.fields.add(MapEntry(key, jsonEncode(value)));
        } else {
          formData.fields.add(MapEntry(key, value.toString()));
        }
      }
    });
    if (files != null && files.isNotEmpty) {
      for (final f in files) {
        if (f.bytes != null) {
          formData.files.add(
            MapEntry(
              'files',
              MultipartFile.fromBytes(f.bytes!, filename: f.name),
            ),
          );
        } else if (f.path != null && f.path!.isNotEmpty) {
          formData.files.add(
            MapEntry(
              'files',
              await MultipartFile.fromFile(f.path!, filename: f.name),
            ),
          );
        }
      }
    } else if (filePaths != null && filePaths.isNotEmpty) {
      for (final path in filePaths) {
        formData.files.add(
          MapEntry(
            'files',
            await MultipartFile.fromFile(
              path,
              filename: path.split(RegExp(r'[/\\]')).last,
            ),
          ),
        );
      }
    }
    return formData;
  }

  /// 12. 문서 기안 생성 (Multipart 또는 JSON)
  Future<ApprovalDocumentModel> createDocument(
    Map<String, dynamic> data, {
    List<String>? filePaths,
    List<PlatformFile>? files,
  }) async {
    final hasFiles = (files != null && files.isNotEmpty) ||
        (filePaths != null && filePaths.isNotEmpty);
    if (hasFiles) {
      final formData = await _buildDocumentFormData(
        data,
        filePaths: filePaths,
        files: files,
      );
      final res = await _dio.post(ApiEndpoints.approvalDocuments, data: formData);
      return ApprovalDocumentModel.fromJson(res.data as Map<String, dynamic>);
    } else {
      final res = await _dio.post(ApiEndpoints.approvalDocuments, data: data);
      return ApprovalDocumentModel.fromJson(res.data as Map<String, dynamic>);
    }
  }

  /// 13. 문서 수정 (Multipart 또는 JSON)
  Future<ApprovalDocumentModel> updateDocument(
    int id,
    Map<String, dynamic> data, {
    List<String>? filePaths,
    List<PlatformFile>? files,
  }) async {
    final url = ApiEndpoints.resolve(ApiEndpoints.approvalDocumentDetail, {'id': id});
    final hasFiles = (files != null && files.isNotEmpty) ||
        (filePaths != null && filePaths.isNotEmpty);
    if (hasFiles) {
      final formData = await _buildDocumentFormData(
        data,
        filePaths: filePaths,
        files: files,
      );
      final res = await _dio.patch(url, data: formData);
      return ApprovalDocumentModel.fromJson(res.data as Map<String, dynamic>);
    } else {
      final res = await _dio.patch(url, data: data);
      return ApprovalDocumentModel.fromJson(res.data as Map<String, dynamic>);
    }
  }

  /// 13-1. 개별 첨부파일 삭제
  Future<void> deleteAttachment(int attachmentId) async {
    final url = '${ApiEndpoints.approvalAttachments}$attachmentId/';
    await _dio.delete(url);
  }

  /// 13-2. 활성 사용자 목록 조회 (참조자 및 대결 위임자 지정용)
  Future<List<SimpleUserModel>> fetchActiveUsers() async {
    final res = await _dio.get(
      ApiEndpoints.users,
      queryParameters: {'is_active': 'true', 'is_system': 'false'},
    );
    final list = (res.data is List)
        ? res.data as List
        : ((res.data as Map<String, dynamic>)['results'] as List? ?? []);
    return list.map((raw) {
      final map = Map<String, dynamic>.from(raw as Map);
      final profile = map['profile'] as Map<String, dynamic>?;
      final profileName = profile?['name']?.toString() ?? '';
      final name = map['name']?.toString() ?? profileName;
      final fullName = map['full_name']?.toString() ?? (name.isNotEmpty ? name : null);
      return SimpleUserModel.fromJson({
        ...map,
        'name': name,
        if (fullName != null) 'full_name': fullName,
      });
    }).toList();
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

  /// 18. 결재 문서 인쇄용 PDF 바이트 조회 (S3 만료 시 백엔드 print_pdf 폴백 포함)
  Future<List<int>> fetchDocumentPdfBytes(int docId, {String? pdfUrl}) async {
    final printUrl = ApiEndpoints.resolve(ApiEndpoints.approvalPrintPdf, {'id': docId});
    final options = Options(
      responseType: ResponseType.bytes,
      headers: {'Accept': 'application/pdf, */*'},
    );

    Response<List<int>>? res;
    if (pdfUrl != null && pdfUrl.isNotEmpty) {
      try {
        final candidate = await _dio.get<List<int>>(pdfUrl, options: options);
        final ct = candidate.headers.value('content-type')?.toLowerCase() ?? '';
        if (!ct.contains('text/html') &&
            candidate.data != null &&
            candidate.data!.isNotEmpty) {
          res = candidate;
        }
      } catch (_) {
        // S3 Presigned URL 만료 등 실패 시 print_pdf 엔드포인트로 폴백
      }
    }

    res ??= await _dio.get<List<int>>(printUrl, options: options);
    final ct = res.headers.value('content-type')?.toLowerCase() ?? '';
    final bytes = res.data;
    if (ct.contains('text/html') || bytes == null || bytes.isEmpty) {
      throw Exception('PDF 파일을 내려받을 수 없습니다.');
    }
    return bytes;
  }

  /// 18-1. 결재 문서 인쇄용 PDF 다운로드 (모바일/데스크톱 로컬 파일 저장)
  Future<String> downloadDocumentPdf(int docId, String title, {String? pdfUrl}) async {
    final bytes = await fetchDocumentPdfBytes(docId, pdfUrl: pdfUrl);
    final tempDir = await getTemporaryDirectory();
    var sanitizedTitle = title.replaceAll(RegExp(r'[\\/:*?"<>|\s]+'), '_');
    if (sanitizedTitle.length > 50) {
      sanitizedTitle = sanitizedTitle.substring(0, 50);
    }
    if (sanitizedTitle.isEmpty) sanitizedTitle = '결재문서';
    final filePath = '${tempDir.path}/전자결재_${sanitizedTitle}_#$docId.pdf';
    final file = File(filePath);
    await file.writeAsBytes(bytes, flush: true);
    return filePath;
  }

  /// 19. 결재 권한 위임(대결) 목록 조회
  Future<List<ApprovalDelegationModel>> fetchDelegations() async {
    final res = await _dio.get(ApiEndpoints.approvalDelegations);
    final list = (res.data is List)
        ? res.data as List
        : ((res.data as Map<String, dynamic>)['results'] as List? ?? []);
    return list
        .map((e) => ApprovalDelegationModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// 20. 결재 권한 위임(대결) 등록
  Future<ApprovalDelegationModel> createDelegation(Map<String, dynamic> data) async {
    final res = await _dio.post(ApiEndpoints.approvalDelegations, data: data);
    return ApprovalDelegationModel.fromJson(res.data as Map<String, dynamic>);
  }

  /// 21. 결재 권한 위임(대결) 수정
  Future<ApprovalDelegationModel> updateDelegation(int id, Map<String, dynamic> data) async {
    final url = ApiEndpoints.resolve(ApiEndpoints.approvalDelegationDetail, {'id': id});
    final res = await _dio.patch(url, data: data);
    return ApprovalDelegationModel.fromJson(res.data as Map<String, dynamic>);
  }

  /// 22. 결재 권한 위임(대결) 삭제
  Future<void> deleteDelegation(int id) async {
    final url = ApiEndpoints.resolve(ApiEndpoints.approvalDelegationDetail, {'id': id});
    await _dio.delete(url);
  }
}

final approvalRepositoryProvider = Provider<ApprovalRepository>((ref) {
  final dio = ref.watch(dioProvider);
  return ApprovalRepository(dio);
});
