import 'dart:io';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:path_provider/path_provider.dart';
import '../../../core/constants/api_endpoints.dart';
import '../../../core/providers/dio_provider.dart';
import 'models/letter_model.dart';

final letterRepositoryProvider = Provider<LetterRepository>((ref) {
  final dio = ref.watch(dioProvider);
  return LetterRepository(dio);
});

class LetterRepository {
  final Dio _dio;
  LetterRepository(this._dio);

  /// 공문 목록 조회
  Future<OfficialLetterListResponseModel> fetchLetters({
    int? company,
    String? approvalStatus,
    String? dispatchMethod,
    String? search,
    int page = 1,
  }) async {
    try {
      final queryParams = <String, dynamic>{
        'page': page,
      };
      if (company != null) {
        queryParams['company'] = company;
      }
      if (approvalStatus != null && approvalStatus.isNotEmpty) {
        queryParams['approval_status'] = approvalStatus;
      }
      if (dispatchMethod != null && dispatchMethod.isNotEmpty) {
        queryParams['dispatch_method'] = dispatchMethod;
      }
      if (search != null && search.trim().isNotEmpty) {
        queryParams['search'] = search.trim();
      }

      final res = await _dio.get(
        ApiEndpoints.officialLetters,
        queryParameters: queryParams,
      );
      return OfficialLetterListResponseModel.fromJson(res.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? '공문 목록을 불러오지 못했습니다.');
    }
  }

  /// 공문 상세 조회
  Future<OfficialLetterModel> fetchLetterDetail(int id) async {
    try {
      final url = ApiEndpoints.resolve(ApiEndpoints.officialLetterDetail, {'id': id});
      final res = await _dio.get(url);
      return OfficialLetterModel.fromJson(res.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? '공문 상세 정보를 불러오지 못했습니다.');
    }
  }

  /// 공문 PDF 다운로드 (임시 파일로 저장 후 파일 경로 반환)
  Future<String> downloadLetterPdf(int id, String documentNumber, {String? pdfUrl}) async {
    final apiDownloadUrl = ApiEndpoints.resolve(ApiEndpoints.officialLetterDownloadPdf, {'id': id});

    Response<List<int>> res;
    if (pdfUrl != null && pdfUrl.isNotEmpty) {
      try {
        res = await _dio.get<List<int>>(
          pdfUrl,
          options: Options(
            responseType: ResponseType.bytes,
            headers: {'Accept': 'application/pdf, */*'},
          ),
        );
      } catch (e) {
        // S3 Presigned URL 만료 또는 파일 부재 시 백엔드 download_pdf 엔드포인트로 폴백
        res = await _dio.get<List<int>>(
          apiDownloadUrl,
          options: Options(
            responseType: ResponseType.bytes,
            headers: {'Accept': 'application/pdf, */*'},
          ),
        );
      }
    } else {
      res = await _dio.get<List<int>>(
        apiDownloadUrl,
        options: Options(
          responseType: ResponseType.bytes,
          headers: {'Accept': 'application/pdf, */*'},
        ),
      );
    }

    final tempDir = await getTemporaryDirectory();
    final sanitizedNumber = (documentNumber.isNotEmpty ? documentNumber : '공문_$id')
        .replaceAll(RegExp(r'[\\/:*?"<>|]'), '_');
    final filePath = '${tempDir.path}/$sanitizedNumber.pdf';
    final file = File(filePath);
    await file.writeAsBytes(res.data!);
    return filePath;
  }

  /// 공문 전자결재 상신
  Future<Map<String, dynamic>> submitApproval(int id) async {
    try {
      final url = ApiEndpoints.resolve(ApiEndpoints.officialLetterSubmitApproval, {'id': id});
      final res = await _dio.post(url);
      return res.data as Map<String, dynamic>;
    } on DioException catch (e) {
      final data = e.response?.data;
      final msg = (data is Map && data['detail'] != null)
          ? data['detail'].toString()
          : (data is Map && data['error'] != null)
              ? data['error'].toString()
              : '전자결재 상신에 실패했습니다.';
      throw Exception(msg);
    }
  }
}
