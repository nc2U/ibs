import 'dart:io';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:path_provider/path_provider.dart';
import '../../../core/constants/api_endpoints.dart';
import '../../../core/providers/dio_provider.dart';
import 'models/inbound_letter_model.dart';

final inboundLetterRepositoryProvider = Provider<InboundLetterRepository>((ref) {
  final dio = ref.watch(dioProvider);
  return InboundLetterRepository(dio);
});

class InboundLetterRepository {
  final Dio _dio;
  InboundLetterRepository(this._dio);

  /// 수신 공문 목록 조회
  Future<InboundLetterListResponseModel> fetchInboundLetters({
    int? company,
    String? status,
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
      if (status != null && status.isNotEmpty) {
        queryParams['status'] = status;
      }
      if (search != null && search.trim().isNotEmpty) {
        queryParams['search'] = search.trim();
      }

      final res = await _dio.get(
        ApiEndpoints.inboundLetters,
        queryParameters: queryParams,
      );
      return InboundLetterListResponseModel.fromJson(res.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? '수신 공문 목록을 불러오지 못했습니다.');
    }
  }

  /// 수신 공문 상세 조회
  Future<InboundLetterModel> fetchInboundLetterDetail(int id) async {
    try {
      final url = ApiEndpoints.resolve(ApiEndpoints.inboundLetterDetail, {'id': id});
      final res = await _dio.get(url);
      return InboundLetterModel.fromJson(res.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? '수신 공문 상세 정보를 불러오지 못했습니다.');
    }
  }

  /// 수신 공문 원본 스캔본 다운로드 (임시 파일로 저장 후 로컬 경로 반환)
  Future<String> downloadScanPdf(int id, String receiptNumber, {String? scanUrl}) async {
    if (scanUrl == null || scanUrl.isEmpty) {
      throw Exception('첨부된 원본 스캔 파일이 없습니다.');
    }

    final sanitizedNumber = (receiptNumber.isNotEmpty ? receiptNumber : '수신공문_$id')
        .replaceAll(RegExp(r'[\\/:*?"<>|]'), '_');
    final tempDir = await getTemporaryDirectory();
    final targetPath = '${tempDir.path}/${sanitizedNumber}_scan.pdf';

    final targetFile = File(targetPath);
    if (await targetFile.exists() && (await targetFile.length()) > 0) {
      return targetPath;
    }

    try {
      final res = await _dio.get<List<int>>(
        scanUrl,
        options: Options(
          responseType: ResponseType.bytes,
          headers: {'Accept': 'application/pdf, */*'},
        ),
      );

      final bytes = res.data;
      if (bytes == null || bytes.isEmpty) {
        throw Exception('스캔 파일 데이터를 읽을 수 없습니다.');
      }

      await targetFile.writeAsBytes(bytes, flush: true);
      return targetPath;
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? '스캔본 PDF 다운로드에 실패했습니다: ${e.message}');
    }
  }

  /// 수신 공문 전자결재 상신
  Future<Map<String, dynamic>> submitApproval(int id) async {
    try {
      final url = ApiEndpoints.resolve(ApiEndpoints.inboundLetterSubmitApproval, {'id': id});
      final res = await _dio.post(url);
      return res.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? '전자결재 상신에 실패했습니다.');
    }
  }
}
