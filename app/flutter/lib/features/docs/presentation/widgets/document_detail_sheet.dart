import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_widget_from_html/flutter_widget_from_html.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/constants/permissions.dart';
import '../../../../core/providers/permission_provider.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/docs_repository.dart';
import '../../data/models/docs_model.dart';
import '../../providers/docs_provider.dart';
import 'document_form_sheet.dart';

/// 문서 상세 보기 바텀 시트 (radius = 0)
class DocumentDetailSheet extends ConsumerWidget {
  final DocumentModel doc;

  const DocumentDetailSheet({super.key, required this.doc});

  Future<void> _handleDelete(BuildContext context, WidgetRef ref) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: context.colors.bgCard,
        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
        title: Text('문서 삭제', style: AppTextStyles.titleLg.copyWith(color: context.colors.textPrimary)),
        content: Text(
          '\'${doc.title}\' 문서를 삭제하시겠습니까?\n삭제된 문서는 휴지통으로 이동합니다.',
          style: AppTextStyles.bodySecond.copyWith(color: context.colors.textPrimary),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: Text('취소', style: AppTextStyles.bodyMuted.copyWith(color: context.colors.textMuted)),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: ElevatedButton.styleFrom(
              backgroundColor: context.colors.error,
              foregroundColor: Colors.white,
              shape: const RoundedRectangleBorder(
                  borderRadius: BorderRadius.zero),
            ),
            child: const Text('삭제'),
          ),
        ],
      ),
    );

    if (confirm == true && context.mounted) {
      try {
        final repo = ref.read(docsRepositoryProvider);
        await repo.deleteDocument(doc.pk);
        ref.read(docsListProvider.notifier).refresh();
        if (context.mounted) Navigator.pop(context);
      } catch (e) {
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('삭제 실패: $e'),
              backgroundColor: context.colors.error,
            ),
          );
        }
      }
    }
  }

  String _formatFileSize(int? bytes) {
    if (bytes == null || bytes <= 0) return '';
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }

  IconData _getFileIcon(String? fileName, String? fileType) {
    final name = (fileName ?? '').toLowerCase();
    final type = (fileType ?? '').toLowerCase();
    if (name.endsWith('.pdf') || type.contains('pdf')) {
      return Icons.picture_as_pdf_outlined;
    }
    if (name.endsWith('.png') ||
        name.endsWith('.jpg') ||
        name.endsWith('.jpeg') ||
        name.endsWith('.gif') ||
        name.endsWith('.webp') ||
        type.contains('image')) {
      return Icons.image_outlined;
    }
    if (name.endsWith('.zip') || name.endsWith('.tar') || name.endsWith('.gz')) {
      return Icons.folder_zip_outlined;
    }
    if (name.endsWith('.doc') ||
        name.endsWith('.docx') ||
        name.endsWith('.hwp') ||
        name.endsWith('.hwpx') ||
        name.endsWith('.txt')) {
      return Icons.description_outlined;
    }
    if (name.endsWith('.xls') ||
        name.endsWith('.xlsx') ||
        name.endsWith('.csv')) {
      return Icons.table_chart_outlined;
    }
    return Icons.attach_file_rounded;
  }

  Future<void> _launchFileUrl(BuildContext context, String? rawUrl) async {
    if (rawUrl == null || rawUrl.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('파일 다운로드 링크가 유효하지 않습니다.')),
      );
      return;
    }
    var fullUrl = rawUrl.trim();
    if (!fullUrl.startsWith('http://') && !fullUrl.startsWith('https://')) {
      const envUrl = String.fromEnvironment('BASE_URL');
      final baseUrl = envUrl.isNotEmpty
          ? (envUrl.startsWith('http') ? envUrl : 'https://$envUrl')
          : 'https://dev.dyibs.com';
      final normalizedBase = baseUrl.endsWith('/')
          ? baseUrl.substring(0, baseUrl.length - 1)
          : baseUrl;
      final normalizedPath = fullUrl.startsWith('/') ? fullUrl : '/$fullUrl';
      fullUrl = '$normalizedBase$normalizedPath';
    }
    try {
      final uri = Uri.parse(fullUrl);
      final launched =
          await launchUrl(uri, mode: LaunchMode.externalApplication);
      if (!launched && context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('파일을 열 수 없습니다.')),
        );
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('오류 발생: $e')),
        );
      }
    }
  }

  Future<void> _launchWebLink(BuildContext context, String? rawUrl) async {
    if (rawUrl == null || rawUrl.trim().isEmpty) return;
    var fullUrl = rawUrl.trim();
    if (!fullUrl.startsWith('http://') && !fullUrl.startsWith('https://')) {
      fullUrl = 'https://$fullUrl';
    }
    try {
      final uri = Uri.parse(fullUrl);
      final launched =
          await launchUrl(uri, mode: LaunchMode.externalApplication);
      if (!launched && context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('링크를 열 수 없습니다.')),
        );
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('링크 열기 실패: $e')),
        );
      }
    }
  }

  String _getSecurityLevelLabel(DocumentModel doc) {
    switch (doc.securityLevel) {
      case '1':
        return '1등급 (비공개)';
      case '2':
        final dept = doc.creatorDeptName;
        return dept != null && dept.isNotEmpty ? '2등급 (팀 공개 - $dept)' : '2등급 (팀 공개)';
      case '3':
        return '3등급 (프로젝트 공개)';
      case '4':
        return '4등급 (전사 공개)';
      default:
        return doc.securityLevelDesc ?? '${doc.securityLevel}등급';
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isRealEstate = doc.projType == '2';
    final scopeLabel = doc.project != null
        ? (isRealEstate ? '🏗 ${doc.project!.name}' : '📋 ${doc.project!.name}')
        : '전체 공용';

    return Container(
      color: context.colors.bgCard,
      padding: EdgeInsets.only(
        left: 20,
        right: 20,
        top: 20,
        bottom: MediaQuery.of(context).padding.bottom + 20,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── 핸들바 ────────────────────────────────────────────────────────
          Center(
            child: Container(
              width: 36,
              height: 4,
              color: context.colors.border,
            ),
          ),
          const SizedBox(height: 16),

          // ── 소속 뱃지 & 액션 ──────────────────────────────────────────────
          Row(
            children: [
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: isRealEstate
                      ? context.colors.accentProject.withAlpha(30)
                      : const Color(0xFF1565C0).withAlpha(30),
                  borderRadius: BorderRadius.zero,
                  border: Border.all(
                    color: isRealEstate
                        ? context.colors.accentProject.withAlpha(60)
                        : const Color(0xFF1565C0).withAlpha(60),
                  ),
                ),
                child: Text(
                  scopeLabel,
                  style: AppTextStyles.caption.copyWith(
                    color: isRealEstate
                        ? context.colors.accentProject
                        : const Color(0xFF1565C0),
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              if (doc.securityLevel == '1') ...[
                const SizedBox(width: 8),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                  decoration: BoxDecoration(
                    color: context.colors.warning.withAlpha(25),
                    borderRadius: BorderRadius.zero,
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.lock_rounded,
                          size: 13, color: context.colors.warning),
                      const SizedBox(width: 4),
                      Text('비공개',
                          style: AppTextStyles.caption
                              .copyWith(color: context.colors.warning)),
                    ],
                  ),
                ),
              ] else if (doc.securityLevel == '2') ...[
                const SizedBox(width: 8),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                  decoration: BoxDecoration(
                    color: context.colors.textMuted.withAlpha(25),
                    borderRadius: BorderRadius.zero,
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.group_outlined,
                          size: 13, color: context.colors.textSecond),
                      const SizedBox(width: 4),
                      Text(
                        doc.creatorDeptName != null && doc.creatorDeptName!.isNotEmpty
                            ? '팀공개 (${doc.creatorDeptName})'
                            : '팀공개',
                        style: AppTextStyles.caption
                            .copyWith(color: context.colors.textSecond),
                      ),
                    ],
                  ),
                ),
              ],
              const Spacer(),
              if (ref.can(Perm.docsUpdate))
                IconButton(
                  icon: const Icon(Icons.edit_outlined, size: 20),
                  color: context.colors.textSecond,
                  onPressed: () {
                    Navigator.pop(context);
                    showModalBottomSheet(
                      context: context,
                      isScrollControlled: true,
                      backgroundColor: Colors.transparent,
                      builder: (ctx) => DocumentFormSheet(doc: doc),
                    );
                  },
                ),
              if (ref.can(Perm.docsDelete))
                IconButton(
                  icon: const Icon(Icons.delete_outline_rounded, size: 20),
                  color: context.colors.error,
                  onPressed: () => _handleDelete(context, ref),
                ),
            ],
          ),
          const SizedBox(height: 12),

          // ── 문서 제목 ───────────────────────────────────────────────────
          Text(doc.title, style: AppTextStyles.titleLg.copyWith(color: context.colors.textPrimary)),
          const SizedBox(height: 8),

          // ── 정보 목록 ────────────────────────────────────────────────────
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: context.colors.bgSurface,
              borderRadius: BorderRadius.zero,
              border: Border.all(color: context.colors.border, width: 0.8),
            ),
            child: Column(
              children: [
                _InfoRow(label: '카테고리', value: doc.cateName ?? '미지정'),
                const SizedBox(height: 6),
                _InfoRow(label: '보안등급', value: _getSecurityLevelLabel(doc)),
                if (doc.executionDate != null &&
                    doc.executionDate!.isNotEmpty) ...[
                  const SizedBox(height: 6),
                  _InfoRow(label: '시행일자', value: doc.executionDate!),
                ],
                if (doc.creator != null) ...[
                  const SizedBox(height: 6),
                  _InfoRow(label: '등록자', value: doc.creator!.username),
                ],
                if (doc.created != null && doc.created!.length >= 10) ...[
                  const SizedBox(height: 6),
                  _InfoRow(
                      label: '등록일시',
                      value: doc.created!.substring(0, 10)),
                ],
              ],
            ),
          ),
          const SizedBox(height: 16),

          // ── 상세 설명 (HTML 파싱 렌더링) ─────────────────────────────────
          Text('설명 / 비고', style: AppTextStyles.titleSm.copyWith(color: context.colors.textPrimary)),
          const SizedBox(height: 6),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: context.colors.bgSurface,
              borderRadius: BorderRadius.zero,
              border: Border.all(color: context.colors.border, width: 0.8),
            ),
            child: doc.description.isNotEmpty
                ? HtmlWidget(
                    doc.description,
                    textStyle: AppTextStyles.bodyMd.copyWith(
                      color: context.colors.textPrimary,
                      height: 1.5,
                    ),
                    customStylesBuilder: (element) {
                      if (element.localName == 'table') {
                        return {
                          'border-collapse': 'collapse',
                          'width': '100%',
                        };
                      }
                      if (element.localName == 'th' ||
                          element.localName == 'td') {
                        return {
                          'border': '1px solid #888',
                          'padding': '6px 8px',
                        };
                      }
                      if (element.localName == 'img') {
                        return {
                          'max-width': '100%',
                          'height': 'auto',
                        };
                      }
                      return null;
                    },
                  )
                : Text(
                    '등록된 상세 설명이 없습니다.',
                    style: AppTextStyles.bodyMuted.copyWith(color: context.colors.textMuted),
                  ),
          ),
          const SizedBox(height: 20),

          // ── 첨부파일 목록 ────────────────────────────────────────────────
          if (doc.files.isNotEmpty) ...[
            Text('첨부파일 (${doc.files.length})', style: AppTextStyles.titleSm.copyWith(color: context.colors.textPrimary)),
            const SizedBox(height: 8),
            ...doc.files.map(
              (f) {
                final sizeStr = _formatFileSize(f.fileSize);
                return Padding(
                  padding: const EdgeInsets.only(bottom: 6),
                  child: InkWell(
                    onTap: () => _launchFileUrl(context, f.file),
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 12, vertical: 10),
                      decoration: BoxDecoration(
                        color: context.colors.bgSurface,
                        borderRadius: BorderRadius.zero,
                        border: Border.all(color: context.colors.border, width: 0.8),
                      ),
                      child: Row(
                        children: [
                          Icon(_getFileIcon(f.fileName, f.fileType),
                              size: 18, color: context.colors.accentWork),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  f.fileName ?? '첨부파일',
                                  style: AppTextStyles.bodySm.copyWith(
                                    fontWeight: FontWeight.w600,
                                    color: context.colors.textPrimary,
                                  ),
                                  overflow: TextOverflow.ellipsis,
                                ),
                                if (sizeStr.isNotEmpty ||
                                    (f.description != null &&
                                        f.description!.isNotEmpty))
                                  Text(
                                    [
                                      if (sizeStr.isNotEmpty) sizeStr,
                                      if (f.description != null &&
                                          f.description!.isNotEmpty)
                                        f.description!,
                                    ].join(' • '),
                                    style: AppTextStyles.caption.copyWith(
                                      color: context.colors.textMuted,
                                    ),
                                  ),
                              ],
                            ),
                          ),
                          const SizedBox(width: 8),
                          Icon(Icons.download_rounded,
                              size: 18, color: context.colors.accentWork),
                        ],
                      ),
                    ),
                  ),
                );
              },
            ),
          ],

          // ── 관련 링크 목록 ────────────────────────────────────────────────
          if (doc.links.isNotEmpty) ...[
            const SizedBox(height: 16),
            Text('관련 링크 (${doc.links.length})', style: AppTextStyles.titleSm.copyWith(color: context.colors.textPrimary)),
            const SizedBox(height: 8),
            ...doc.links.map(
              (l) => Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: InkWell(
                  onTap: () => _launchWebLink(context, l.link),
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                          horizontal: 12, vertical: 10),
                    decoration: BoxDecoration(
                      color: context.colors.bgSurface,
                      borderRadius: BorderRadius.zero,
                      border: Border.all(color: context.colors.border, width: 0.8),
                    ),
                    child: Row(
                      children: [
                        Icon(Icons.link_rounded,
                            size: 18, color: context.colors.accentWork),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            l.description != null && l.description!.isNotEmpty
                                ? '${l.description} (${l.link})'
                                : l.link,
                            style: AppTextStyles.bodySm.copyWith(
                              color: context.colors.accentWork,
                              decoration: TextDecoration.underline,
                            ),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Icon(Icons.open_in_new_rounded,
                            size: 16, color: context.colors.textMuted),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  final String label;
  final String value;

  const _InfoRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        SizedBox(
          width: 80,
          child: Text(label, style: AppTextStyles.caption.copyWith(color: context.colors.textMuted)),
        ),
        Expanded(
          child: Text(
            value,
            style: AppTextStyles.bodySm.copyWith(
              fontWeight: FontWeight.w500,
              color: context.colors.textPrimary,
            ),
          ),
        ),
      ],
    );
  }
}
