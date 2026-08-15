import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/constants/permissions.dart';
import '../../../../core/providers/permission_provider.dart';
import '../../../../core/widgets/error_view.dart';
import '../../../../core/widgets/loading_shimmer.dart';
import '../data/models/meeting_model.dart';
import '../data/meeting_repository.dart';
import '../providers/meeting_provider.dart';
import 'meeting_form_screen.dart';
import 'widgets/meeting_pdf_helper.dart';

/// 회의 상세 화면
class MeetingDetailScreen extends ConsumerWidget {
  final int meetingId;
  const MeetingDetailScreen({super.key, required this.meetingId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final detailState = ref.watch(meetingDetailProvider(meetingId));

    return Scaffold(
      backgroundColor: AppColors.bgPrimary,
      appBar: AppBar(
        backgroundColor: AppColors.bgPrimary,
        foregroundColor: AppColors.textPrimary,
        elevation: 0,
        title: detailState.maybeWhen(
          data: (meeting) => Text(
            meeting.title,
            style: AppTextStyles.titleMd,
            overflow: TextOverflow.ellipsis,
          ),
          orElse: () => Text('회의 상세', style: AppTextStyles.titleMd),
        ),
        actions: [
          detailState.maybeWhen(
            data: (meeting) {
              final projectSlug = meeting.projectDesc.slug;
              final canConfirm = ref.can(Perm.meetingConfirm, projectSlug: projectSlug);
              final canUpdate = ref.can(Perm.meetingUpdate, projectSlug: projectSlug) ||
                  ref.can(Perm.meetingOwnUpdate, projectSlug: projectSlug);
              final canDelete = ref.can(Perm.meetingDelete, projectSlug: projectSlug);

              return Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  // ── 회의 확정 / 확정 취소 버튼 (meeting.confirm 권한) ────────────
                  if (canConfirm)
                    IconButton(
                      icon: Icon(
                        meeting.isConfirmed
                            ? Icons.check_circle_rounded
                            : Icons.check_circle_outline_rounded,
                        size: 22,
                        color: meeting.isConfirmed
                            ? AppColors.accentProject
                            : (meeting.status == '2'
                                ? AppColors.textPrimary
                                : AppColors.textDisabled),
                      ),
                      tooltip: meeting.isConfirmed ? '확정 취소' : '회의 확정',
                      onPressed: () => _handleConfirmToggle(context, ref, meeting),
                    ),
                  // ── 회의 수정 버튼 (meeting.update 권한 및 미확정 상태일 때만 노출) ──
                  if (canUpdate && !meeting.isConfirmed)
                    IconButton(
                      icon: const Icon(Icons.edit_outlined, size: 22),
                      tooltip: '수정',
                      onPressed: () => Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => MeetingFormScreen(initialMeeting: meeting),
                        ),
                      ),
                    ),
                  // ── 회의 삭제 버튼 (meeting.delete 권한) ──────────────────────────
                  if (canDelete)
                    IconButton(
                      icon: const Icon(Icons.delete_outline_rounded, size: 22),
                      tooltip: '삭제',
                      onPressed: () => _handleDelete(context, ref, meeting),
                    ),
                ],
              );
            },
            orElse: () => const SizedBox.shrink(),
          ),
          IconButton(
            icon: const Icon(Icons.refresh_rounded, size: 22),
            tooltip: '새로고침',
            onPressed: () =>
                ref.read(meetingDetailProvider(meetingId).notifier).refresh(),
          ),
        ],
      ),
      body: detailState.when(
        loading: () => const LoadingShimmer(itemCount: 4, itemHeight: 120),
        error: (e, _) => ErrorView.network(
          onRetry: () => ref.invalidate(meetingDetailProvider(meetingId)),
        ),
        data: (meeting) {
          final canRead = ref.can(Perm.meetingRead, projectSlug: meeting.projectDesc.slug);
          if (!canRead) {
            return const Center(
              child: Padding(
                padding: EdgeInsets.all(24.0),
                child: ErrorView.empty(
                  message: '회의 상세 내용을 조회할 권한이 없습니다.',
                  subMessage: '관리자에게 [회의 열람] 권한을 요청해 주세요.',
                ),
              ),
            );
          }
          return _buildBody(context, ref, meeting);
        },
      ),
    );
  }

  Future<void> _handleConfirmToggle(
      BuildContext context, WidgetRef ref, MeetingModel meeting) async {
    if (meeting.status != '2' && !meeting.isConfirmed) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('회의 상태가 [종료] 상태인 경우에만 확정할 수 있습니다.'),
          duration: Duration(seconds: 2),
        ),
      );
      return;
    }

    final willConfirm = !meeting.isConfirmed;
    final actionText = willConfirm ? '확정' : '확정 취소';

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.bgCard,
        shape: const RoundedRectangleBorder(),
        title: Text('회의 $actionText', style: AppTextStyles.titleMd),
        content: Text(
          willConfirm
              ? '이 회의를 확정하시겠습니까?\n확정 시 참석자들에게 확정 알림이 전송됩니다.'
              : '이 회의의 확정을 취소하시겠습니까?',
          style: AppTextStyles.bodyMd,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: Text('취소', style: AppTextStyles.bodyMuted),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: willConfirm
                  ? AppColors.accentProject
                  : AppColors.accentApproval,
              shape: const RoundedRectangleBorder(),
            ),
            onPressed: () => Navigator.pop(ctx, true),
            child: Text(actionText,
                style: const TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );

    if (confirmed == true && context.mounted) {
      try {
        final result = await ref
            .read(meetingDetailProvider(meeting.pk).notifier)
            .toggleConfirm();
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(result
                  ? '회의가 확정되었습니다.'
                  : '회의 확정이 취소되었습니다.'),
              duration: const Duration(seconds: 2),
            ),
          );
        }
      } catch (e) {
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('처리 중 오류가 발생했습니다: $e'),
              backgroundColor: AppColors.accentApproval,
            ),
          );
        }
      }
    }
  }

  Future<void> _handleDelete(
      BuildContext context, WidgetRef ref, MeetingModel meeting) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.bgCard,
        shape: const RoundedRectangleBorder(),
        title: Text('회의 삭제', style: AppTextStyles.titleMd),
        content: Text(
          '정말로 이 회의록을 삭제하시겠습니까?\n삭제된 데이터는 복구할 수 없습니다.',
          style: AppTextStyles.bodyMd,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: Text('취소', style: AppTextStyles.bodyMuted),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.accentApproval,
              shape: const RoundedRectangleBorder(),
            ),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('삭제', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );

    if (confirmed == true && context.mounted) {
      try {
        await ref
            .read(meetingRepositoryProvider)
            .deleteMeeting(meeting.pk);
        ref.invalidate(meetingListProvider);

        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('회의록이 삭제되었습니다.'),
              duration: Duration(seconds: 2),
            ),
          );
          context.pop();
        }
      } catch (e) {
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('삭제 실패: $e'),
              backgroundColor: AppColors.accentApproval,
            ),
          );
        }
      }
    }
  }

  Widget _buildBody(BuildContext context, WidgetRef ref, MeetingModel meeting) {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── 기본 정보 섹션 ──────────────────────────────────────────────
          _InfoCard(
            meeting: meeting,
            onExportPdf: () => exportMeetingPdf(context, ref, meeting),
          ),
          const SizedBox(height: 12),

          // ── 회의 의제 ──────────────────────────────────────────────
          if (meeting.agenda.isNotEmpty) ...[
            const _SectionLabel(label: '회의 의제'),
            _TextCard(content: meeting.agenda),
            const SizedBox(height: 12),
          ],

          // ── 회의 내용 (Content) ────────────────────────────────────────
          if (meeting.content.isNotEmpty) ...[
            const _SectionLabel(label: '회의 내용'),
            _TextCard(content: meeting.content),
            const SizedBox(height: 12),
          ],

          // ── 주요 결정 사항 ────────────────────────────────────────
          if (meeting.decisions.isNotEmpty) ...[
            const _SectionLabel(label: '주요 결정 사항'),
            _TextCard(
              content: meeting.decisions,
              borderColor: AppColors.accentProject,
            ),
            const SizedBox(height: 12),
          ],

          // ── 후속 조치 사항 ────────────────────────────────────
          if (meeting.actionItems.isNotEmpty) ...[
            const _SectionLabel(label: '후속 조치 사항'),
            _TextCard(
              content: meeting.actionItems,
              borderColor: AppColors.accentApproval,
            ),
            const SizedBox(height: 12),
          ],

          // ── 첨부 파일 ──────────────────────────────────────────────────
          if (meeting.files.isNotEmpty) ...[
            _SectionLabel(label: '첨부 파일', count: meeting.files.length),
            ...meeting.files.map((f) => _MeetingFileTile(file: f)),
            const SizedBox(height: 12),
          ],

          // ── 관련 링크 ──────────────────────────────────────────────────
          if (meeting.links.isNotEmpty) ...[
            _SectionLabel(label: '관련 링크', count: meeting.links.length),
            ...meeting.links.map((l) => _MeetingLinkTile(link: l)),
            const SizedBox(height: 12),
          ],

          // ── 관련 업무 (Issues) ──────────────────────────────────────────
          _SectionLabel(
            label: '관련 업무',
            count: meeting.issues.isNotEmpty ? meeting.issues.length : null,
            action: InkWell(
              onTap: () async {
                await context.push(
                  '/work/issues/new?meeting_id=${meeting.pk}&project_slug=${meeting.projectDesc.slug}',
                );
                // 새 업무가 등록되었으면 회의 상세 화면 새로고침
                if (context.mounted) {
                  ref.invalidate(meetingDetailProvider(meeting.pk));
                }
              },
              borderRadius: BorderRadius.circular(4),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.add, size: 14, color: AppColors.accentWork),
                    const SizedBox(width: 2),
                    Text(
                      '관련 업무 추가',
                      style: AppTextStyles.label.copyWith(color: AppColors.accentWork),
                    ),
                  ],
                ),
              ),
            ),
          ),
          if (meeting.issues.isNotEmpty)
            ...meeting.issues.map(
              (issue) => Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: _MeetingIssueTile(issue: issue),
              ),
            )
          else
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 14),
              decoration: BoxDecoration(
                color: AppColors.bgCard.withAlpha(50),
                border: Border.all(color: AppColors.border.withAlpha(50), width: 0.8),
              ),
              child: Text(
                '연결된 관련 업무가 없습니다.',
                style: AppTextStyles.caption.copyWith(color: AppColors.textDisabled),
              ),
            ),
          const SizedBox(height: 30),
        ],
      ),
    );
  }
}

// ── 기본 정보 카드 ─────────────────────────────────────────────────────────────
class _InfoCard extends StatelessWidget {
  final MeetingModel meeting;
  final VoidCallback onExportPdf;
  const _InfoCard({required this.meeting, required this.onExportPdf});

  String _formatDateTime(String dateStr) {
    if (dateStr.isEmpty) return '';
    var formatted = dateStr.replaceAll('T', ' ');
    if (formatted.length >= 16) {
      return formatted.substring(0, 16);
    }
    return formatted;
  }

  @override
  Widget build(BuildContext context) {
    final attendeesText = [
      ...meeting.attendeesDesc.map((u) => u.username),
      if (meeting.otherAttendees.isNotEmpty) meeting.otherAttendees,
    ].join(', ');

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.bgCard,
        border: Border.all(color: AppColors.border, width: 0.8),
      ),
      child: Column(
        children: [
          _Row(
              label: '프로젝트',
              value: meeting.projectDesc.name,
              icon: Icons.business_center_outlined),
          _Row(
              label: '회의 일시',
              value: _formatDateTime(meeting.meetingDate),
              icon: Icons.calendar_today_outlined),
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 5),
            child: Row(
              children: [
                const Icon(Icons.flag_outlined, size: 16, color: AppColors.textMuted),
                const SizedBox(width: 8),
                SizedBox(
                  width: 72,
                  child: Text('상태', style: AppTextStyles.bodyMuted),
                ),
                Text(
                  meeting.statusDisplay,
                  style: AppTextStyles.bodyMd,
                ),
                if (meeting.isConfirmed) ...[
                  const SizedBox(width: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1.5),
                    decoration: BoxDecoration(
                      color: AppColors.accentProject.withAlpha(30),
                      border: Border.all(color: AppColors.accentProject.withAlpha(80)),
                      borderRadius: BorderRadius.circular(3),
                    ),
                    child: Text(
                      '확정됨',
                      style: AppTextStyles.label.copyWith(color: AppColors.accentProject),
                    ),
                  ),
                ],
              ],
            ),
          ),
          if (meeting.categoryDesc != null)
            _Row(
                label: '카테고리',
                value: meeting.categoryDesc!.name,
                icon: Icons.category_outlined),
          if (attendeesText.isNotEmpty)
            _Row(
                label: '참석자',
                value: attendeesText,
                icon: Icons.people_outline_rounded),
          const SizedBox(height: 10),
          const Divider(height: 1, color: AppColors.border),
          const SizedBox(height: 10),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: onExportPdf,
              icon: const Icon(Icons.picture_as_pdf_outlined,
                  size: 16, color: Color(0xFFEF5350)),
              label: const Text('회의록 PDF 보기 / 출력'),
              style: OutlinedButton.styleFrom(
                foregroundColor: AppColors.textPrimary,
                side: const BorderSide(color: AppColors.border),
                shape: const RoundedRectangleBorder(
                    borderRadius: BorderRadius.zero),
                padding: const EdgeInsets.symmetric(vertical: 10),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _Row extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  const _Row({required this.label, required this.value, required this.icon});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Row(
        children: [
          Icon(icon, size: 16, color: AppColors.textMuted),
          const SizedBox(width: 8),
          SizedBox(
            width: 72,
            child: Text(label, style: AppTextStyles.bodyMuted),
          ),
          Expanded(
            child: Text(
              value,
              style: AppTextStyles.bodyMd,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}

// ── 텍스트 카드 (의제, 내용, 결정사항 등) ──────────────────────────────────────────
class _TextCard extends StatelessWidget {
  final String content;
  final Color? borderColor;
  const _TextCard({required this.content, this.borderColor});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.bgCard,
        border: Border.all(
          color: borderColor ?? AppColors.border,
          width: borderColor != null ? 1.2 : 0.8,
        ),
      ),
      child: Text(content, style: AppTextStyles.bodyMd),
    );
  }
}

// ── 섹션 레이블 ────────────────────────────────────────────────────────────────
class _SectionLabel extends StatelessWidget {
  final String label;
  final int? count;
  final Widget? action;
  const _SectionLabel({required this.label, this.count, this.action});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        children: [
          Text(label,
              style:
                  AppTextStyles.titleSm.copyWith(color: AppColors.textMuted)),
          if (count != null) ...[
            const SizedBox(width: 6),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
              decoration: BoxDecoration(
                color: AppColors.accentWork.withAlpha(40),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text('$count',
                  style: AppTextStyles.label
                      .copyWith(color: AppColors.accentWork)),
            ),
          ],
          if (action != null) ...[
            const Spacer(),
            action!,
          ],
        ],
      ),
    );
  }
}

// ── 연동 업무 타일 ─────────────────────────────────────────────────────────────
class _MeetingIssueTile extends StatelessWidget {
  final IssueInMeetingModel issue;
  const _MeetingIssueTile({required this.issue});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: () => context.push('/work/issues/${issue.pk}'),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        decoration: BoxDecoration(
          color: AppColors.bgCard,
          border: Border.all(color: AppColors.border, width: 0.8),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: AppColors.accentWork.withAlpha(30),
                borderRadius: BorderRadius.circular(3),
              ),
              child: Text(issue.status,
                  style: AppTextStyles.label
                      .copyWith(color: AppColors.accentWork)),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Text('#${issue.pk} ${issue.subject}',
                  style: AppTextStyles.bodyMd,
                  overflow: TextOverflow.ellipsis),
            ),
            if (issue.assignedTo != null) ...[
              const SizedBox(width: 6),
              Text(issue.assignedTo!.username,
                  style: AppTextStyles.caption),
            ],
          ],
        ),
      ),
    );
  }
}

// ── 첨부 파일 타일 ─────────────────────────────────────────────────────────────
class _MeetingFileTile extends StatelessWidget {
  final MeetingFileModel file;
  const _MeetingFileTile({required this.file});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: InkWell(
        onTap: () async {
          final uri = Uri.parse(file.file);
          if (await canLaunchUrl(uri)) launchUrl(uri);
        },
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          decoration: BoxDecoration(
            color: AppColors.bgCard,
            border: Border.all(color: AppColors.border, width: 0.8),
          ),
          child: Row(
            children: [
              const Icon(Icons.attach_file_rounded,
                  size: 18, color: AppColors.accentWork),
              const SizedBox(width: 10),
              Expanded(
                child: Text(file.fileName,
                    style: AppTextStyles.bodyMd,
                    overflow: TextOverflow.ellipsis),
              ),
              const Icon(Icons.open_in_new_rounded,
                  size: 16, color: AppColors.textMuted),
            ],
          ),
        ),
      ),
    );
  }
}

// ── 관련 링크 타일 ─────────────────────────────────────────────────────────────
class _MeetingLinkTile extends StatelessWidget {
  final MeetingLinkModel link;
  const _MeetingLinkTile({required this.link});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: InkWell(
        onTap: () async {
          final uri = Uri.parse(link.link);
          if (await canLaunchUrl(uri)) launchUrl(uri);
        },
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          decoration: BoxDecoration(
            color: AppColors.bgCard,
            border: Border.all(color: AppColors.border, width: 0.8),
          ),
          child: Row(
            children: [
              const Icon(Icons.link_rounded,
                  size: 18, color: AppColors.accentWork),
              const SizedBox(width: 10),
              Expanded(
                child: Text(link.name.isNotEmpty ? link.name : link.link,
                    style: AppTextStyles.bodyMd,
                    overflow: TextOverflow.ellipsis),
              ),
              const Icon(Icons.open_in_new_rounded,
                  size: 16, color: AppColors.textMuted),
            ],
          ),
        ),
      ),
    );
  }
}
