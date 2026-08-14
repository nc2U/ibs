import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/widgets/error_view.dart';
import '../../../../core/widgets/loading_shimmer.dart';
import '../data/models/meeting_model.dart';
import '../providers/meeting_provider.dart';
import 'meeting_form_screen.dart';

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
            data: (meeting) => IconButton(
              icon: const Icon(Icons.edit_outlined, size: 22),
              tooltip: '수정',
              onPressed: () => Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => MeetingFormScreen(initialMeeting: meeting),
                ),
              ),
            ),
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
        data: (meeting) => _buildBody(context, ref, meeting),
      ),
    );
  }

  Widget _buildBody(BuildContext context, WidgetRef ref, MeetingModel meeting) {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── 기본 정보 섹션 ──────────────────────────────────────────────
          _InfoCard(meeting: meeting),
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
          const SizedBox(height: 12),

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

          const SizedBox(height: 30),
        ],
      ),
    );
  }
}

// ── 기본 정보 카드 ─────────────────────────────────────────────────────────────
class _InfoCard extends StatelessWidget {
  final MeetingModel meeting;
  const _InfoCard({required this.meeting});

  String _formatDateTime(String dateStr) {
    if (dateStr.isEmpty) return '';
    // 예: "2026-08-10 10:00+09:00" -> "2026-08-10 10:00"
    // 예: "2026-08-10T10:00:00+09:00" -> "2026-08-10 10:00"
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
          _Row(
              label: '상태',
              value: meeting.statusDisplay,
              icon: Icons.flag_outlined),
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
