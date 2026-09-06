import 'dart:io';
import 'dart:math';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:open_filex/open_filex.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/constants/permissions.dart';
import '../../../../core/providers/dio_provider.dart';
import '../../../../core/providers/permission_provider.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/models/sales_models.dart';
import '../../data/sales_repository.dart';
import '../../providers/sales_provider.dart';

/// 영업 인력 증빙 서류 목록 및 열람/공유 바텀시트 열기 함수
void showPersonDocumentSheet(
  BuildContext context, {
  required SalesPersonModel person,
  String? projectSlug,
  bool? canManage,
}) {
  showModalBottomSheet(
    context: context,
    isScrollControlled: true,
    backgroundColor: context.colors.bgCard,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
    ),
    builder: (ctx) => Padding(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(ctx).viewInsets.bottom,
      ),
      child: PersonDocumentSheet(
        person: person,
        projectSlug: projectSlug,
        canManage: canManage,
      ),
    ),
  );
}

/// 영업 인력 증빙 서류 바텀시트
class PersonDocumentSheet extends ConsumerStatefulWidget {
  final SalesPersonModel person;
  final String? projectSlug;
  final bool? canManage;

  const PersonDocumentSheet({
    super.key,
    required this.person,
    this.projectSlug,
    this.canManage,
  });

  @override
  ConsumerState<PersonDocumentSheet> createState() => _PersonDocumentSheetState();
}

class _PersonDocumentSheetState extends ConsumerState<PersonDocumentSheet> {
  int? _downloadingDocId;
  int? _sharingDocId;
  int? _verifyingDocId;

  /// 서류 종류 한글 라벨
  String _getDocTypeLabel(String docType, String? docTypeDisplay) {
    if (docTypeDisplay != null && docTypeDisplay.isNotEmpty) return docTypeDisplay;
    switch (docType) {
      case '1':
        return '주민등록등본/초본';
      case '2':
        return '통장 사본';
      case '3':
        return '신분증 사본';
      case '4':
        return '영업 위촉계약서';
      case '5':
        return '각종 서약서/각서';
      case '9':
        return '기타 증빙서류';
      default:
        return '기타 서류';
    }
  }

  /// 서류 종류 테마 색상
  Color _getDocTypeColor(String docType) {
    switch (docType) {
      case '1':
        return const Color(0xFF3B82F6); // 파랑
      case '2':
        return const Color(0xFF10B981); // 초록
      case '3':
        return const Color(0xFF06B6D4); // 시안
      case '4':
        return const Color(0xFFF59E0B); // 주황
      case '5':
        return const Color(0xFFEF4444); // 빨강
      case '9':
      default:
        return const Color(0xFF6B7280); // 그레이
    }
  }

  /// 파일 크기 포맷팅 (B, KB, MB)
  String _formatFileSize(int? bytes) {
    if (bytes == null || bytes <= 0) return '0 B';
    const suffixes = ['B', 'KB', 'MB', 'GB'];
    var i = (log(bytes) / log(1024)).floor();
    if (i >= suffixes.length) i = suffixes.length - 1;
    return '${(bytes / pow(1024, i)).toStringAsFixed(1)} ${suffixes[i]}';
  }

  /// 파일 다운로드 및 로컬 캐시 경로 반환
  Future<String?> _downloadDocumentFile(SalesPersonDocumentModel doc) async {
    if (doc.file == null || doc.file!.isEmpty) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('등록된 파일 링크가 없습니다.')),
        );
      }
      return null;
    }

    final dio = ref.read(dioProvider);
    final tempDir = await getTemporaryDirectory();

    // 파일명 산출 및 특수문자 정제
    var fileName = doc.fileName;
    if (fileName == null || fileName.isEmpty) {
      fileName = doc.file!.split('/').last;
      if (fileName.contains('?')) {
        fileName = fileName.split('?').first;
      }
    }
    final cleanFileName = fileName.replaceAll(RegExp(r'[\\/:*?"<>|]'), '_');
    final savePath = '${tempDir.path}/doc_${doc.id}_$cleanFileName';

    // 이미 다운로드된 파일이 있으면 재사용
    final targetFile = File(savePath);
    if (await targetFile.exists() && await targetFile.length() > 0) {
      return savePath;
    }

    // 서버에서 다운로드
    var fileUrl = doc.file!;
    await dio.download(fileUrl, savePath);
    return savePath;
  }

  /// 파일 다운로드 후 OS 기본 뷰어로 열람
  Future<void> _viewDocument(SalesPersonDocumentModel doc) async {
    setState(() => _downloadingDocId = doc.id);
    try {
      final savePath = await _downloadDocumentFile(doc);
      if (savePath == null) return;

      final result = await OpenFilex.open(savePath);
      if (result.type != ResultType.done && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('파일 열기 상태: ${result.message}')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('파일 열람 실패: $e'),
            backgroundColor: context.colors.error,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _downloadingDocId = null);
    }
  }

  /// 파일 다운로드 후 네이티브 공유 시트 호출
  Future<void> _shareDocument(SalesPersonDocumentModel doc) async {
    setState(() => _sharingDocId = doc.id);
    try {
      final savePath = await _downloadDocumentFile(doc);
      if (savePath == null) return;

      final title = doc.title.isNotEmpty ? doc.title : (doc.fileName ?? '증빙서류');
      final personName = widget.person.name;

      // ignore: deprecated_member_use
      await Share.shareXFiles(
        [XFile(savePath)],
        text: '[$personName] $title',
        subject: '영업 인력 증빙 서류 - $personName ($title)',
      );
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('서류 공유 실패: $e'),
            backgroundColor: context.colors.error,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _sharingDocId = null);
    }
  }

  /// 서류 검증 토글
  Future<void> _toggleVerify(SalesPersonDocumentModel doc) async {
    setState(() => _verifyingDocId = doc.id);
    try {
      final repository = ref.read(salesRepositoryProvider);
      final newStatus = !doc.isVerified;
      await repository.verifySalesPersonDocument(doc.id, isVerified: newStatus);

      // 프로바이더 캐시 무효화
      ref.invalidate(salesPersonDocumentsProvider(widget.person.id));
      ref.invalidate(salesPersonsProvider);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              newStatus ? '서류 검증이 완료되었습니다.' : '서류 검증이 취소(대기)되었습니다.',
            ),
            backgroundColor: newStatus ? const Color(0xFF10B981) : context.colors.textSecond,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('검증 상태 변경 실패: $e'),
            backgroundColor: context.colors.error,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _verifyingDocId = null);
    }
  }

  @override
  Widget build(BuildContext context) {
    final docsAsync = ref.watch(salesPersonDocumentsProvider(widget.person.id));

    return Container(
      constraints: BoxConstraints(
        maxHeight: MediaQuery.of(context).size.height * 0.85,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // ── 상단 드래그 핸들 ──────────────────────────────────
          Container(
            margin: const EdgeInsets.only(top: 10, bottom: 6),
            width: 36,
            height: 4,
            decoration: BoxDecoration(
              color: context.colors.border,
              borderRadius: BorderRadius.circular(2),
            ),
          ),

          // ── 헤더: 성명 + 직책 + 닫기 버튼 ─────────────────────
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              children: [
                const Icon(
                  Icons.folder_shared_outlined,
                  size: 20,
                  color: Color(0xFF6366F1),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Text(
                            widget.person.name,
                            style: AppTextStyles.titleSm.copyWith(
                              color: context.colors.textPrimary,
                              fontWeight: FontWeight.bold,
                              fontSize: 15,
                            ),
                          ),
                          const SizedBox(width: 6),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: const Color(0xFF6366F1).withAlpha(20),
                              border: Border.all(
                                color: const Color(0xFF6366F1).withAlpha(70),
                                width: 0.8,
                              ),
                            ),
                            child: Text(
                              widget.person.dutyDisplay ?? '상담사',
                              style: const TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.bold,
                                color: Color(0xFF6366F1),
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 2),
                      Text(
                        widget.person.agencyName != null
                            ? '${widget.person.agencyName} > ${widget.person.teamName ?? ""}'
                            : (widget.person.teamName ?? '소속팀 미지정'),
                        style: AppTextStyles.caption.copyWith(
                          color: context.colors.textMuted,
                          fontSize: 11,
                        ),
                      ),
                    ],
                  ),
                ),
                IconButton(
                  icon: Icon(Icons.close, size: 20, color: context.colors.textMuted),
                  onPressed: () => Navigator.of(context).pop(),
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(),
                ),
              ],
            ),
          ),

          const Divider(height: 1),

          // ── 서류 목록 본문 ──────────────────────────────────
          Flexible(
            child: docsAsync.when(
              loading: () => const Padding(
                padding: EdgeInsets.all(40),
                child: Center(
                  child: SizedBox(
                    width: 24,
                    height: 24,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: Color(0xFF6366F1),
                    ),
                  ),
                ),
              ),
              error: (err, _) => Padding(
                padding: const EdgeInsets.all(24),
                child: Center(
                  child: Text(
                    '서류 목록을 불러오지 못했습니다:\n$err',
                    textAlign: TextAlign.center,
                    style: AppTextStyles.bodySecond.copyWith(
                      color: context.colors.error,
                    ),
                  ),
                ),
              ),
              data: (docs) {
                final total = docs.length;
                final verifiedCount = docs.where((d) => d.isVerified).length;
                final pendingCount = total - verifiedCount;

                return SingleChildScrollView(
                  padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // 1. 통계 요약 칩
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                        margin: const EdgeInsets.only(bottom: 14),
                        decoration: BoxDecoration(
                          color: context.colors.bgSurface,
                          border: Border.all(color: context.colors.border, width: 0.8),
                        ),
                        child: Row(
                          children: [
                            Text(
                              '전체 서류:',
                              style: AppTextStyles.caption.copyWith(
                                color: context.colors.textMuted,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                            const SizedBox(width: 4),
                            Text(
                              '$total건',
                              style: AppTextStyles.caption.copyWith(
                                color: context.colors.textPrimary,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const SizedBox(width: 14),
                            Container(
                              width: 6,
                              height: 6,
                              decoration: const BoxDecoration(
                                color: Color(0xFF10B981),
                                shape: BoxShape.circle,
                              ),
                            ),
                            const SizedBox(width: 4),
                            Text(
                              '검증완료 $verifiedCount',
                              style: AppTextStyles.caption.copyWith(
                                color: const Color(0xFF10B981),
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                            const SizedBox(width: 12),
                            Container(
                              width: 6,
                              height: 6,
                              decoration: const BoxDecoration(
                                color: Color(0xFFF59E0B),
                                shape: BoxShape.circle,
                              ),
                            ),
                            const SizedBox(width: 4),
                            Text(
                              '확인대기 $pendingCount',
                              style: AppTextStyles.caption.copyWith(
                                color: const Color(0xFFF59E0B),
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ],
                        ),
                      ),

                      // 2. 빈 상태
                      if (docs.isEmpty) ...[
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.symmetric(vertical: 40, horizontal: 20),
                          decoration: BoxDecoration(
                            color: context.colors.bgSurface,
                            border: Border.all(color: context.colors.border, width: 0.8),
                          ),
                          child: Column(
                            children: [
                              Icon(
                                Icons.file_present_outlined,
                                size: 36,
                                color: context.colors.textMuted,
                              ),
                              const SizedBox(height: 10),
                              Text(
                                '등록된 증빙 서류가 없습니다.',
                                style: AppTextStyles.titleSm.copyWith(
                                  color: context.colors.textPrimary,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              const SizedBox(height: 6),
                              Text(
                                '주민등록등본, 통장 사본, 신분증, 위촉계약서 등은\n웹 시스템 [영업 관리 > 영업 조직]에서 등록하실 수 있습니다.',
                                textAlign: TextAlign.center,
                                style: AppTextStyles.caption.copyWith(
                                  color: context.colors.textMuted,
                                  height: 1.4,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ] else ...[
                        // 3. 서류 카드 목록
                        ListView.separated(
                          shrinkWrap: true,
                          physics: const NeverScrollableScrollPhysics(),
                          itemCount: docs.length,
                          separatorBuilder: (_, __) => const SizedBox(height: 10),
                          itemBuilder: (ctx, i) {
                            final doc = docs[i];
                            return _buildDocumentCard(doc);
                          },
                        ),
                      ],
                    ],
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  /// 개별 서류 카드 위젯
  Widget _buildDocumentCard(SalesPersonDocumentModel doc) {
    final canManage = widget.canManage ?? ref.can(Perm.salesManage, projectSlug: widget.projectSlug);
    final typeColor = _getDocTypeColor(doc.docType);
    final typeLabel = _getDocTypeLabel(doc.docType, doc.docTypeDisplay);
    final isDownloading = _downloadingDocId == doc.id;
    final isSharing = _sharingDocId == doc.id;
    final isVerifying = _verifyingDocId == doc.id;

    final dateStr = doc.createdAt != null && doc.createdAt!.length >= 10
        ? doc.createdAt!.substring(0, 10)
        : '-';

    return Container(
      decoration: BoxDecoration(
        color: context.colors.bgSurface,
        border: Border.all(
          color: doc.isVerified
              ? const Color(0xFF10B981).withAlpha(60)
              : context.colors.border,
          width: 0.8,
        ),
      ),
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── 상단 뱃지 행: 서류 종류 + 검증 상태 ─────────────
          Row(
            children: [
              // 구분 뱃지
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: typeColor.withAlpha(20),
                  border: Border.all(color: typeColor.withAlpha(80), width: 0.8),
                ),
                child: Text(
                  typeLabel,
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                    color: typeColor,
                  ),
                ),
              ),
              const SizedBox(width: 6),
              // 검증 상태 뱃지
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: doc.isVerified
                      ? const Color(0xFF10B981).withAlpha(20)
                      : const Color(0xFFF59E0B).withAlpha(20),
                  border: Border.all(
                    color: doc.isVerified
                        ? const Color(0xFF10B981).withAlpha(80)
                        : const Color(0xFFF59E0B).withAlpha(80),
                    width: 0.8,
                  ),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      doc.isVerified ? Icons.check_circle : Icons.schedule,
                      size: 11,
                      color: doc.isVerified
                          ? const Color(0xFF10B981)
                          : const Color(0xFFF59E0B),
                    ),
                    const SizedBox(width: 3),
                    Text(
                      doc.isVerified ? '검증완료' : '확인대기',
                      style: TextStyle(
                        fontSize: 9.5,
                        fontWeight: FontWeight.bold,
                        color: doc.isVerified
                            ? const Color(0xFF10B981)
                            : const Color(0xFFF59E0B),
                      ),
                    ),
                  ],
                ),
              ),
              const Spacer(),
              // 등록일
              Text(
                dateStr,
                style: AppTextStyles.caption.copyWith(
                  color: context.colors.textMuted,
                  fontSize: 10.5,
                ),
              ),
            ],
          ),

          const SizedBox(height: 8),

          // ── 서류 세부 제목 및 파일명 ────────────────────────
          if (doc.title.isNotEmpty) ...[
            Text(
              doc.title,
              style: AppTextStyles.titleSm.copyWith(
                color: context.colors.textPrimary,
                fontWeight: FontWeight.bold,
                fontSize: 13,
              ),
            ),
            const SizedBox(height: 3),
          ],

          Row(
            children: [
              const Icon(
                Icons.insert_drive_file_outlined,
                size: 14,
                color: Color(0xFF6366F1),
              ),
              const SizedBox(width: 5),
              Expanded(
                child: Text(
                  doc.fileName ?? doc.file?.split('/').last ?? '첨부파일',
                  style: AppTextStyles.caption.copyWith(
                    color: context.colors.textSecond,
                    fontSize: 11.5,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              const SizedBox(width: 6),
              Text(
                _formatFileSize(doc.fileSize),
                style: AppTextStyles.caption.copyWith(
                  color: context.colors.textMuted,
                  fontSize: 10.5,
                ),
              ),
            ],
          ),

          const SizedBox(height: 10),
          Divider(color: context.colors.borderSubtle, height: 1),
          const SizedBox(height: 8),

          // ── 하단 액션 버튼 행: [열람] [공유] [검증] ─────────────
          Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              // 1. [열람] 버튼
              Material(
                color: const Color(0xFF6366F1).withAlpha(15),
                shape: Border.all(
                  color: const Color(0xFF6366F1).withAlpha(70),
                  width: 0.8,
                ),
                child: InkWell(
                  onTap: isDownloading ? null : () => _viewDocument(doc),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        if (isDownloading) ...[
                          const SizedBox(
                            width: 12,
                            height: 12,
                            child: CircularProgressIndicator(
                              strokeWidth: 1.5,
                              color: Color(0xFF6366F1),
                            ),
                          ),
                          const SizedBox(width: 5),
                        ] else ...[
                          const Icon(
                            Icons.visibility_outlined,
                            size: 13,
                            color: Color(0xFF6366F1),
                          ),
                          const SizedBox(width: 4),
                        ],
                        const Text(
                          '열람',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.bold,
                            color: Color(0xFF6366F1),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),

              const SizedBox(width: 6),

              // 2. [공유] 버튼
              Material(
                color: const Color(0xFF0EA5E9).withAlpha(15),
                shape: Border.all(
                  color: const Color(0xFF0EA5E9).withAlpha(70),
                  width: 0.8,
                ),
                child: InkWell(
                  onTap: isSharing ? null : () => _shareDocument(doc),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        if (isSharing) ...[
                          const SizedBox(
                            width: 12,
                            height: 12,
                            child: CircularProgressIndicator(
                              strokeWidth: 1.5,
                              color: Color(0xFF0EA5E9),
                            ),
                          ),
                          const SizedBox(width: 5),
                        ] else ...[
                          const Icon(
                            Icons.share_outlined,
                            size: 13,
                            color: Color(0xFF0EA5E9),
                          ),
                          const SizedBox(width: 4),
                        ],
                        const Text(
                          '공유',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.bold,
                            color: Color(0xFF0EA5E9),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),

              if (canManage) ...[
                const SizedBox(width: 6),

                // 3. [검증 / 검증취소] 버튼
                Material(
                  color: doc.isVerified
                      ? context.colors.borderSubtle
                      : const Color(0xFF10B981).withAlpha(15),
                  shape: Border.all(
                    color: doc.isVerified
                        ? context.colors.border
                        : const Color(0xFF10B981).withAlpha(70),
                    width: 0.8,
                  ),
                  child: InkWell(
                    onTap: isVerifying ? null : () => _toggleVerify(doc),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          if (isVerifying) ...[
                            SizedBox(
                              width: 12,
                              height: 12,
                              child: CircularProgressIndicator(
                                strokeWidth: 1.5,
                                color: doc.isVerified
                                    ? context.colors.textMuted
                                    : const Color(0xFF10B981),
                              ),
                            ),
                            const SizedBox(width: 5),
                          ] else ...[
                            Icon(
                              doc.isVerified ? Icons.remove_done : Icons.check,
                              size: 13,
                              color: doc.isVerified
                                  ? context.colors.textMuted
                                  : const Color(0xFF10B981),
                            ),
                            const SizedBox(width: 3),
                          ],
                          Text(
                            doc.isVerified ? '검증취소' : '검증',
                            style: TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.bold,
                              color: doc.isVerified
                                  ? context.colors.textMuted
                                  : const Color(0xFF10B981),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }
}
