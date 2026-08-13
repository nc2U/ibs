import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_text_styles.dart';
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
        backgroundColor: AppColors.bgCard,
        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
        title: Text('문서 삭제', style: AppTextStyles.titleLg),
        content: Text(
          '\'${doc.title}\' 문서를 삭제하시겠습니까?\n삭제된 문서는 휴지통으로 이동합니다.',
          style: AppTextStyles.bodySecond,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: Text('취소', style: AppTextStyles.bodyMuted),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.error,
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
            SnackBar(content: Text('삭제 실패: $e')),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isRealEstate = doc.projType == '2';
    final scopeLabel = doc.project != null
        ? (isRealEstate ? '🏗 ${doc.project!.name}' : '📋 ${doc.project!.name}')
        : '전체 공용';

    return Container(
      color: AppColors.bgCard,
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
              color: AppColors.border,
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
                      ? AppColors.accentProject.withAlpha(30)
                      : const Color(0xFF1565C0).withAlpha(30),
                  borderRadius: BorderRadius.zero,
                  border: Border.all(
                    color: isRealEstate
                        ? AppColors.accentProject.withAlpha(60)
                        : const Color(0xFF1565C0).withAlpha(60),
                  ),
                ),
                child: Text(
                  scopeLabel,
                  style: AppTextStyles.caption.copyWith(
                    color: isRealEstate
                        ? AppColors.accentProject
                        : const Color(0xFF1565C0),
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              if (doc.isSecret) ...[
                const SizedBox(width: 8),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                  decoration: BoxDecoration(
                    color: AppColors.warning.withAlpha(25),
                    borderRadius: BorderRadius.zero,
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.lock_rounded,
                          size: 13, color: AppColors.warning),
                      const SizedBox(width: 4),
                      Text('비밀글',
                          style: AppTextStyles.caption
                              .copyWith(color: AppColors.warning)),
                    ],
                  ),
                ),
              ],
              const Spacer(),
              IconButton(
                icon: const Icon(Icons.edit_outlined, size: 20),
                color: AppColors.textSecond,
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
              IconButton(
                icon: const Icon(Icons.delete_outline_rounded, size: 20),
                color: AppColors.error,
                onPressed: () => _handleDelete(context, ref),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // ── 문서 제목 ───────────────────────────────────────────────────
          Text(doc.title, style: AppTextStyles.titleLg),
          const SizedBox(height: 8),

          // ── 정보 목록 ────────────────────────────────────────────────────
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppColors.bgSurface,
              borderRadius: BorderRadius.zero,
              border: Border.all(color: AppColors.border, width: 0.8),
            ),
            child: Column(
              children: [
                _InfoRow(label: '카테고리', value: doc.cateName ?? '미지정'),
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

          // ── 상세 설명 ────────────────────────────────────────────────────
          Text('설명 / 비고', style: AppTextStyles.titleSm),
          const SizedBox(height: 6),
          Text(
            doc.description.isNotEmpty ? doc.description : '등록된 상세 설명이 없습니다.',
            style: AppTextStyles.bodySecond,
          ),
          const SizedBox(height: 20),

          // ── 첨부파일 목록 ────────────────────────────────────────────────
          if (doc.files.isNotEmpty) ...[
            Text('첨부파일 (${doc.files.length})', style: AppTextStyles.titleSm),
            const SizedBox(height: 8),
            ...doc.files.map(
              (f) => Container(
                margin: const EdgeInsets.only(bottom: 6),
                padding:
                    const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                decoration: BoxDecoration(
                  color: AppColors.bgSurface,
                  borderRadius: BorderRadius.zero,
                  border: Border.all(color: AppColors.border, width: 0.8),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.attach_file_rounded,
                        size: 16, color: AppColors.accentWork),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        f.fileName ?? '첨부파일',
                        style: AppTextStyles.bodySm,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    const Icon(Icons.download_rounded,
                        size: 18, color: AppColors.textSecond),
                  ],
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
          child: Text(label, style: AppTextStyles.caption),
        ),
        Expanded(
          child: Text(
            value,
            style: AppTextStyles.bodySm.copyWith(fontWeight: FontWeight.w500),
          ),
        ),
      ],
    );
  }
}
