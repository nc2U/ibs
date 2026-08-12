import 'dart:io';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/constants/api_endpoints.dart';
import '../../../core/providers/dio_provider.dart';
import 'models/issue_model.dart';

class IssueRepository {
  final Dio _dio;

  IssueRepository(this._dio);

  /// 업무 목록 조회 (페이지네이션)
  Future<IssueListResponse> fetchIssues(IssueFilterModel filter) async {
    final response = await _dio.get(
      ApiEndpoints.issues,
      queryParameters: filter.toQueryParams(),
    );
    return IssueListResponse.fromJson(response.data as Map<String, dynamic>);
  }

  /// 업무 상세 조회
  Future<IssueModel> fetchIssueDetail(int id) async {
    final url = ApiEndpoints.resolve(ApiEndpoints.issueDetail, {'id': id});
    final response = await _dio.get(url);
    return IssueModel.fromJson(response.data as Map<String, dynamic>);
  }

  /// 진척률 업데이트 (PATCH)
  Future<void> updateDoneRatio(int issueId, int ratio) async {
    final url = ApiEndpoints.resolve(ApiEndpoints.issueDetail, {'id': issueId});
    await _dio.patch(url, data: {'done_ratio': ratio});
  }

  /// 댓글 목록 조회
  Future<List<IssueCommentModel>> fetchComments(int issueId) async {
    final response = await _dio.get(
      ApiEndpoints.issueComments,
      queryParameters: {'issue': issueId, 'ordering': 'created'},
    );
    final data = response.data;
    if (data is Map && data.containsKey('results')) {
      return (data['results'] as List)
          .map((e) => IssueCommentModel.fromJson(e as Map<String, dynamic>))
          .toList();
    }
    return (data as List)
        .map((e) => IssueCommentModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// 댓글 작성
  Future<void> addComment(int issueId, String content) async {
    await _dio.post(
      ApiEndpoints.issueComments,
      data: {'issue': issueId, 'content': content},
    );
  }

  /// 파일 첨부 (multipart/form-data)
  Future<void> uploadFile(int issueId, File file) async {
    final formData = FormData.fromMap({
      'issue': issueId,
      'file': await MultipartFile.fromFile(
        file.path,
        filename: file.path.split('/').last,
      ),
    });
    await _dio.post(
      ApiEndpoints.issueFiles,
      data: formData,
      options: Options(contentType: 'multipart/form-data'),
    );
  }
}

/// Riverpod 프로바이더
final issueRepositoryProvider = Provider<IssueRepository>((ref) {
  return IssueRepository(ref.watch(dioProvider));
});
