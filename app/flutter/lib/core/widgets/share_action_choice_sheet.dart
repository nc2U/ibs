import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../constants/app_text_styles.dart';
import '../constants/permissions.dart';
import '../providers/permission_provider.dart';
import '../providers/share_payload_provider.dart';
import '../theme/app_colors_extension.dart';
import '../../features/chat/presentation/widgets/chat_share_target_sheet.dart';
import '../../features/docs/presentation/widgets/document_form_sheet.dart';

/// 외부 앱(갤러리, 파일, 브라우저 등)에서 공유된 파일/링크를 감지했을 때
/// [💬 메신저로 전송] 또는 [📁 문서에 등록] 중 원하는 동작을 선택하는 바텀시트
class ShareActionChoiceSheet extends ConsumerWidget {
  final SharePayload payload;

  const ShareActionChoiceSheet({
    super.key,
    required this.payload,
  });

  static Future<void> show(BuildContext context, SharePayload payload) {
    return showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useRootNavigator: true,
      backgroundColor: Colors.transparent,
      builder: (_) => ShareActionChoiceSheet(payload: payload),
    );
  }

  String _formatFileSize(int bytes) {
    if (bytes <= 0) return '';
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }

  IconData _getFileIcon(String fileName) {
    final ext = fileName.split('.').last.toLowerCase();
    if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'heic'].contains(ext)) {
      return Icons.image_rounded;
    }
    if (ext == 'pdf') return Icons.picture_as_pdf_rounded;
    if (['zip', 'rar', '7z', 'tar', 'gz'].contains(ext)) {
      return Icons.folder_zip_rounded;
    }
    if (['xls', 'xlsx', 'csv'].contains(ext)) return Icons.table_chart_rounded;
    if (['doc', 'docx', 'hwp', 'hwpx'].contains(ext)) return Icons.description_rounded;
    if (['ppt', 'pptx'].contains(ext)) return Icons.slideshow_rounded;
    if (['mp4', 'mov', 'avi', 'mkv'].contains(ext)) return Icons.movie_rounded;
    if (['mp3', 'wav', 'm4a'].contains(ext)) return Icons.audiotrack_rounded;
    return Icons.insert_drive_file_rounded;
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final totalSize = payload.files.fold<int>(0, (sum, f) => sum + f.size);

    return PopScope(
      onPopInvokedWithResult: (didPop, result) {
        if (didPop && result != 'handover') {
          // 명시적인 메신저/문서 핸드오버가 아닌 뒤로가기/외부 터치 닫기인 경우 payload 초기화
          ref.read(pendingSharePayloadProvider.notifier).clear();
        }
      },
      child: Container(
        decoration: BoxDecoration(
          color: context.colors.bgSurface,
          borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
        ),
        padding: const EdgeInsets.fromLTRB(20, 14, 20, 28),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── 상단 핸들바 ─────────────────────────────────────────
            Center(
              child: Container(
                width: 36,
                height: 4,
                decoration: BoxDecoration(
                  color: context.colors.border,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: 16),

            // ── 헤더 타이틀 ─────────────────────────────────────────
            Row(
              children: [
                Icon(Icons.share_rounded, color: context.colors.accentWork, size: 22),
                const SizedBox(width: 8),
                Text(
                  '공유 항목 처리 선택',
                  style: AppTextStyles.titleMd.copyWith(
                    fontWeight: FontWeight.bold,
                    color: context.colors.textPrimary,
                  ),
                ),
                const Spacer(),
                IconButton(
                  icon: Icon(Icons.close_rounded, color: context.colors.textMuted, size: 20),
                  onPressed: () {
                    ref.read(pendingSharePayloadProvider.notifier).clear();
                    Navigator.pop(context);
                  },
                ),
              ],
            ),
            Text(
              '공유받은 항목을 메신저로 전송하거나 사내 문서함에 등록할 수 있습니다.',
              style: AppTextStyles.bodySm.copyWith(color: context.colors.textMuted),
            ),
            const SizedBox(height: 16),

            // ── 수신 항목 요약 카드 ─────────────────────────────────
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: context.colors.bgPrimary,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: context.colors.border, width: 0.8),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.inventory_2_outlined, size: 16, color: context.colors.accentWork),
                      const SizedBox(width: 6),
                      Text(
                        '수신된 항목 요약',
                        style: AppTextStyles.caption.copyWith(
                          fontWeight: FontWeight.bold,
                          color: context.colors.textPrimary,
                        ),
                      ),
                      const Spacer(),
                      if (totalSize > 0)
                        Text(
                          '총 ${_formatFileSize(totalSize)}',
                          style: AppTextStyles.caption.copyWith(
                            color: context.colors.textMuted,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  if (payload.files.isNotEmpty)
                    ...payload.files.take(2).map((f) => Padding(
                          padding: const EdgeInsets.only(bottom: 6),
                          child: Row(
                            children: [
                              Icon(_getFileIcon(f.name), size: 16, color: context.colors.textMuted),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  f.name,
                                  style: AppTextStyles.bodySm.copyWith(
                                    color: context.colors.textPrimary,
                                  ),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                              if (f.size > 0) ...[
                                const SizedBox(width: 8),
                                Text(
                                  _formatFileSize(f.size),
                                  style: AppTextStyles.caption.copyWith(
                                    color: context.colors.textMuted,
                                  ),
                                ),
                              ],
                            ],
                          ),
                        )),
                  if (payload.files.length > 2)
                    Text(
                      '... 외 ${payload.files.length - 2}개 파일',
                      style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                    ),
                  if (payload.links.isNotEmpty)
                    ...payload.links.take(2).map((link) => Padding(
                          padding: const EdgeInsets.only(bottom: 4),
                          child: Row(
                            children: [
                              Icon(Icons.link_rounded, size: 16, color: context.colors.accentWork),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  link,
                                  style: AppTextStyles.caption.copyWith(
                                    color: context.colors.accentWork,
                                  ),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                            ],
                          ),
                        )),
                ],
              ),
            ),
            const SizedBox(height: 18),

            // ── 선택지 1: 메신저로 전송하기 ─────────────────────────
            Material(
              color: Colors.transparent,
              child: InkWell(
                borderRadius: BorderRadius.circular(14),
                onTap: () {
                  Navigator.pop(context, 'handover');
                  ChatShareTargetSheet.show(context, payload);
                },
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(
                      color: context.colors.accentWork.withAlpha(90),
                      width: 1.2,
                    ),
                    color: context.colors.accentWork.withAlpha(15),
                  ),
                  child: Row(
                    children: [
                      Container(
                        width: 44,
                        height: 44,
                        decoration: BoxDecoration(
                          color: context.colors.accentWork.withAlpha(35),
                          shape: BoxShape.circle,
                        ),
                        child: Icon(
                          Icons.chat_bubble_outline_rounded,
                          color: context.colors.accentWork,
                          size: 22,
                        ),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Text(
                                  '메신저로 전송하기',
                                  style: AppTextStyles.bodyMd.copyWith(
                                    fontWeight: FontWeight.bold,
                                    color: context.colors.textPrimary,
                                  ),
                                ),
                                const SizedBox(width: 6),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                  decoration: BoxDecoration(
                                    color: context.colors.accentWork,
                                    borderRadius: BorderRadius.circular(4),
                                  ),
                                  child: const Text(
                                    '추천',
                                    style: TextStyle(
                                      color: Colors.white,
                                      fontSize: 10,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 3),
                            Text(
                              '나와의 채팅, 특정 대화방 또는 임직원에게 즉시 공유',
                              style: AppTextStyles.caption.copyWith(
                                color: context.colors.textMuted,
                              ),
                            ),
                          ],
                        ),
                      ),
                      Icon(
                        Icons.arrow_forward_ios_rounded,
                        color: context.colors.accentWork,
                        size: 16,
                      ),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(height: 12),

            // ── 선택지 2: 사내 문서에 등록하기 ───────────────────────
            Material(
              color: Colors.transparent,
              child: InkWell(
                borderRadius: BorderRadius.circular(14),
                onTap: () {
                  Navigator.pop(context, 'handover');

                  // 문서 등록 권한 검증
                  if (!ref.can(Perm.docsCreate)) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text('문서 등록 권한(docs.create)이 없어 공유된 문서를 등록할 수 없습니다.'),
                        backgroundColor: Colors.redAccent,
                      ),
                    );
                    ref.read(pendingSharePayloadProvider.notifier).clear();
                    return;
                  }

                  // DocumentFormSheet 팝업
                  showModalBottomSheet(
                    context: context,
                    isScrollControlled: true,
                    useRootNavigator: true,
                    backgroundColor: Colors.transparent,
                    builder: (ctx) => DocumentFormSheet(
                      initialFiles: payload.files,
                      initialLinks: payload.links,
                      initialTitle: payload.defaultTitle,
                    ),
                  );
                  ref.read(pendingSharePayloadProvider.notifier).clear();
                },
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(
                      color: context.colors.border,
                      width: 1,
                    ),
                    color: context.colors.bgPrimary,
                  ),
                  child: Row(
                    children: [
                      Container(
                        width: 44,
                        height: 44,
                        decoration: BoxDecoration(
                          color: const Color(0xFF1565C0).withAlpha(30),
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(
                          Icons.folder_open_rounded,
                          color: Color(0xFF1565C0),
                          size: 22,
                        ),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '사내 문서에 등록하기',
                              style: AppTextStyles.bodyMd.copyWith(
                                fontWeight: FontWeight.bold,
                                color: context.colors.textPrimary,
                              ),
                            ),
                            const SizedBox(height: 3),
                            Text(
                              '프로젝트 또는 본사 관리 문서함에 첨부하여 저장',
                              style: AppTextStyles.caption.copyWith(
                                color: context.colors.textMuted,
                              ),
                            ),
                          ],
                        ),
                      ),
                      Icon(
                        Icons.arrow_forward_ios_rounded,
                        color: context.colors.textMuted,
                        size: 16,
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
