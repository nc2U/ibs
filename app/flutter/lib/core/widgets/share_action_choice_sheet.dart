import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../constants/app_text_styles.dart';
import '../constants/permissions.dart';
import '../providers/permission_provider.dart';
import '../providers/share_payload_provider.dart';
import '../router/app_router.dart';
import '../theme/app_colors_extension.dart';
import '../../features/chat/presentation/widgets/chat_share_target_sheet.dart';
import '../../features/docs/presentation/widgets/document_form_sheet.dart';
import '../../features/meeting/presentation/widgets/meeting_share_target_sheet.dart';
import '../../features/issue/presentation/widgets/issue_share_target_sheet.dart';

/// 외부 앱(갤러리, 파일, 브라우저 등)에서 공유된 파일/링크를 감지했을 때
/// [💬 메신저로 전송], [📁 문서에 등록], [📝 회의록에 첨부], [✅ 업무에 첨부] 중
/// 원하는 비즈니스 액션을 선택하는 바텀시트
class ShareActionChoiceSheet extends ConsumerStatefulWidget {
  final SharePayload payload;

  const ShareActionChoiceSheet({
    super.key,
    required this.payload,
  });

  static bool _isShowing = false;

  static Future<void> show(BuildContext context, SharePayload payload) async {
    if (_isShowing) return;
    _isShowing = true;
    try {
      await showModalBottomSheet(
        context: context,
        isScrollControlled: true,
        useRootNavigator: true,
        backgroundColor: Colors.transparent,
        builder: (_) => ShareActionChoiceSheet(payload: payload),
      );
    } finally {
      _isShowing = false;
    }
  }

  @override
  ConsumerState<ShareActionChoiceSheet> createState() => _ShareActionChoiceSheetState();
}

class _ShareActionChoiceSheetState extends ConsumerState<ShareActionChoiceSheet> {
  late final DateTime _mountedTime;

  @override
  void initState() {
    super.initState();
    _mountedTime = DateTime.now();
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
  Widget build(BuildContext context) {
    final payload = widget.payload;
    final totalSize = payload.files.fold<int>(0, (sum, f) => sum + f.size);
    final hasFiles = payload.files.isNotEmpty;

    return PopScope(
      onPopInvokedWithResult: (didPop, result) {
        if (didPop && result != 'handover') {
          final elapsed = DateTime.now().difference(_mountedTime).inMilliseconds;
          // 사용자의 자발적 닫기([X]버튼)이거나 시트가 정상 노출된 후(400ms 이상) 닫힌 경우만 clear()
          // 라우트 전환 등 비정상적인 즉시 닫힘(400ms 미만)일 때는 페이로드를 보존하여 재표출 보장
          if (result == 'user_cancel' || elapsed >= 400) {
            ref.read(pendingSharePayloadProvider.notifier).clear();
          } else {
            debugPrint('🛡️ [ShareActionChoiceSheet] Premature pop detected ($elapsed ms). Preserving payload for retry.');
          }
        }
      },
      child: Container(
        constraints: BoxConstraints(
          maxHeight: MediaQuery.of(context).size.height * 0.9,
        ),
        decoration: BoxDecoration(
          color: context.colors.bgSurface,
          borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
        ),
        padding: const EdgeInsets.fromLTRB(20, 14, 20, 24),
        child: SingleChildScrollView(
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
                      Navigator.pop(context, 'user_cancel');
                    },
                  ),
                ],
              ),
              Text(
                '공유받은 항목을 메신저, 사내 문서, 회의록 또는 업무에 바로 연결할 수 있습니다.',
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
              const SizedBox(height: 16),

              // ── 선택지 1: 메신저로 전송하기 ─────────────────────────
              _buildChoiceCard(
                context: context,
                icon: Icons.chat_bubble_outline_rounded,
                iconColor: context.colors.accentWork,
                iconBgColor: context.colors.accentWork.withAlpha(35),
                title: '메신저로 전송하기',
                subtitle: '나와의 채팅, 특정 대화방 또는 임직원에게 즉시 공유',
                badgeText: '추천',
                borderColor: context.colors.accentWork.withAlpha(90),
                bgColor: context.colors.accentWork.withAlpha(15),
                onTap: () {
                  final navContext = rootNavigatorKey.currentContext ?? context;
                  Navigator.pop(context, 'handover');
                  ChatShareTargetSheet.show(navContext, payload);
                },
              ),
              const SizedBox(height: 10),

              // ── 선택지 2: 사내 문서에 등록하기 ───────────────────────
              _buildChoiceCard(
                context: context,
                icon: Icons.folder_open_rounded,
                iconColor: const Color(0xFF1565C0),
                iconBgColor: const Color(0xFF1565C0).withAlpha(30),
                title: '사내 문서에 등록하기',
                subtitle: '프로젝트 또는 본사 관리 문서함에 첨부하여 저장',
                borderColor: context.colors.border,
                bgColor: context.colors.bgPrimary,
                onTap: () {
                  final navContext = rootNavigatorKey.currentContext ?? context;
                  Navigator.pop(context, 'handover');

                  // 문서 등록 권한 검증
                  if (!ref.can(Perm.docsCreate)) {
                    ScaffoldMessenger.of(navContext).showSnackBar(
                      const SnackBar(
                        content: Text('문서 등록 권한(docs.create)이 없어 공유된 문서를 등록할 수 없습니다.'),
                        backgroundColor: Colors.redAccent,
                      ),
                    );
                    ref.read(pendingSharePayloadProvider.notifier).clear();
                    return;
                  }

                  // DocumentFormSheet 팝업 (안정적인 최상단 navContext 사용)
                  showModalBottomSheet(
                    context: navContext,
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
              ),
              const SizedBox(height: 10),

              // ── 선택지 3: 회의록에 첨부하기 ─────────────────────────
              _buildChoiceCard(
                context: context,
                icon: Icons.event_note_rounded,
                iconColor: const Color(0xFF8B5CF6),
                iconBgColor: const Color(0xFF8B5CF6).withAlpha(30),
                title: '회의록에 첨부하기',
                subtitle: hasFiles
                    ? '기존 회의록을 검색·선택하여 관련 파일 추가'
                    : '파일이 포함된 공유 항목만 첨부할 수 있습니다.',
                borderColor: context.colors.border,
                bgColor: context.colors.bgPrimary,
                enabled: hasFiles,
                onTap: () {
                  final navContext = rootNavigatorKey.currentContext ?? context;
                  Navigator.pop(context, 'handover');

                  // 회의 수정/첨부 권한 검증
                  if (!ref.can(Perm.meetingUpdate) && !ref.can(Perm.meetingOwnUpdate)) {
                    ScaffoldMessenger.of(navContext).showSnackBar(
                      const SnackBar(
                        content: Text('회의록 수정/첨부 권한이 없어 파일을 첨부할 수 없습니다.'),
                        backgroundColor: Colors.redAccent,
                      ),
                    );
                    ref.read(pendingSharePayloadProvider.notifier).clear();
                    return;
                  }

                  MeetingShareTargetSheet.show(navContext, payload);
                },
              ),
              const SizedBox(height: 10),

              // ── 선택지 4: 업무(Issue)에 첨부하기 ───────────────────
              _buildChoiceCard(
                context: context,
                icon: Icons.task_alt_rounded,
                iconColor: const Color(0xFF0284C7),
                iconBgColor: const Color(0xFF0284C7).withAlpha(30),
                title: '업무(Issue)에 첨부하기',
                subtitle: hasFiles
                    ? '진행 중인 업무를 검색·선택하여 현장 사진/자료 추가'
                    : '파일이 포함된 공유 항목만 첨부할 수 있습니다.',
                borderColor: context.colors.border,
                bgColor: context.colors.bgPrimary,
                enabled: hasFiles,
                onTap: () {
                  final navContext = rootNavigatorKey.currentContext ?? context;
                  Navigator.pop(context, 'handover');

                  // 업무 수정/첨부 권한 검증
                  if (!ref.can(Perm.issueUpdate) && !ref.can(Perm.issueOwnUpdate)) {
                    ScaffoldMessenger.of(navContext).showSnackBar(
                      const SnackBar(
                        content: Text('업무 수정/첨부 권한이 없어 파일을 첨부할 수 없습니다.'),
                        backgroundColor: Colors.redAccent,
                      ),
                    );
                    ref.read(pendingSharePayloadProvider.notifier).clear();
                    return;
                  }

                  IssueShareTargetSheet.show(navContext, payload);
                },
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildChoiceCard({
    required BuildContext context,
    required IconData icon,
    required Color iconColor,
    required Color iconBgColor,
    required String title,
    required String subtitle,
    required Color borderColor,
    required Color bgColor,
    required VoidCallback onTap,
    String? badgeText,
    bool enabled = true,
  }) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        borderRadius: BorderRadius.circular(14),
        onTap: enabled ? onTap : null,
        child: Opacity(
          opacity: enabled ? 1.0 : 0.45,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: borderColor, width: 1.0),
              color: bgColor,
            ),
            child: Row(
              children: [
                Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(
                    color: iconBgColor,
                    shape: BoxShape.circle,
                  ),
                  child: Icon(icon, color: iconColor, size: 22),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Text(
                            title,
                            style: AppTextStyles.bodyMd.copyWith(
                              fontWeight: FontWeight.bold,
                              color: context.colors.textPrimary,
                            ),
                          ),
                          if (badgeText != null) ...[
                            const SizedBox(width: 6),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(
                                color: iconColor,
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: Text(
                                badgeText,
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontSize: 10,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                          ],
                        ],
                      ),
                      const SizedBox(height: 3),
                      Text(
                        subtitle,
                        style: AppTextStyles.caption.copyWith(
                          color: context.colors.textMuted,
                        ),
                      ),
                    ],
                  ),
                ),
                Icon(
                  Icons.arrow_forward_ios_rounded,
                  color: enabled ? iconColor : context.colors.textMuted,
                  size: 16,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
