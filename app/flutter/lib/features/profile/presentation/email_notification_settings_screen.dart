import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/providers/auth_provider.dart';
import '../../../core/providers/dio_provider.dart';
import '../../../core/theme/app_colors_extension.dart';
import '../../project/data/models/project_model.dart';
import '../../project/providers/project_provider.dart';

/// ✉️ 이메일 및 업무 모니터링 알림 설정 화면
class EmailNotificationSettingsScreen extends ConsumerStatefulWidget {
  const EmailNotificationSettingsScreen({super.key});

  @override
  ConsumerState<EmailNotificationSettingsScreen> createState() =>
      _EmailNotificationSettingsScreenState();
}

class _EmailNotificationSettingsScreenState
    extends ConsumerState<EmailNotificationSettingsScreen> {
  bool _meetingCreated = true;
  bool _meetingConfirmed = true;
  bool _autoWatchCreated = true;
  bool _autoWatchAssigned = true;
  Set<int> _subscribedProjectIds = {};

  bool _isLoading = true;
  bool _isSaving = false;

  @override
  void initState() {
    super.initState();
    _loadInitialData();
  }

  Future<void> _loadInitialData() async {
    final user = ref.read(currentUserProvider).valueOrNull;
    final profile = user?.profile;

    if (profile != null) {
      _meetingCreated = profile.meetingCreatedNotification;
      _meetingConfirmed = profile.meetingConfirmedNotification;
      _autoWatchCreated = profile.autoWatchCreated;
      _autoWatchAssigned = profile.autoWatchAssigned;
    }

    // 구독 프로젝트 목록 조회
    if (user != null) {
      final dio = ref.read(dioProvider);
      try {
        final res = await dio.get(
          '/api/v1/project-subscription/',
          queryParameters: {'user': user.pk},
        );
        if (res.data is List) {
          final pids = (res.data as List)
              .map((item) => item['project'] as int?)
              .whereType<int>()
              .toSet();
          _subscribedProjectIds = pids;
        }
      } catch (e) {
        debugPrint('⚠️ [EmailNotification] 구독 프로젝트 로드 실패: $e');
      }
    }

    if (mounted) {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _saveSettings() async {
    final user = ref.read(currentUserProvider).valueOrNull;
    if (user == null) return;

    setState(() => _isSaving = true);
    final dio = ref.read(dioProvider);

    try {
      // 1. Profile 모델 업데이트 (회의 알림, 업무 자동 지켜보기)
      if (user.profile?.pk != null) {
        await dio.patch(
          '/api/v1/profile/${user.profile!.pk}/',
          data: {
            'meeting_created_notification': _meetingCreated,
            'meeting_confirmed_notification': _meetingConfirmed,
            'auto_watch_created': _autoWatchCreated,
            'auto_watch_assigned': _autoWatchAssigned,
          },
        );
      }

      // 2. 알림 구독 프로젝트 일괄 업데이트 (bulk_update)
      await dio.post(
        '/api/v1/project-subscription/bulk-update/',
        data: {
          'user': user.pk,
          'project_ids': _subscribedProjectIds.toList(),
        },
      );

      // 사용자 정보 프로바이더 무효화 및 재조회
      ref.invalidate(currentUserProvider);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('알림 설정이 성공적으로 저장되었습니다.'),
            behavior: SnackBarBehavior.floating,
            backgroundColor: Color(0xFF10B981),
          ),
        );
        Navigator.pop(context);
      }
    } on DioException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('저장 실패: ${e.response?.data ?? e.message}'),
            behavior: SnackBarBehavior.floating,
            backgroundColor: context.colors.error,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('오류 발생: $e'),
            behavior: SnackBarBehavior.floating,
            backgroundColor: context.colors.error,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isSaving = false);
    }
  }

  void _openProjectSelectBottomSheet(List<ProjectModel> allProjects) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: context.colors.bgCard,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) {
        return StatefulBuilder(
          builder: (ctx, setModalState) {
            return SafeArea(
              child: Container(
                constraints: BoxConstraints(
                  maxHeight: MediaQuery.of(context).size.height * 0.75,
                ),
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          '알림 구독 프로젝트 선택',
                          style: AppTextStyles.titleSm.copyWith(
                            fontWeight: FontWeight.bold,
                            color: context.colors.textPrimary,
                          ),
                        ),
                        IconButton(
                          icon: const Icon(Icons.close_rounded),
                          onPressed: () => Navigator.pop(ctx),
                          color: context.colors.textMuted,
                          padding: EdgeInsets.zero,
                          constraints: const BoxConstraints(),
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Text(
                      '선택한 프로젝트의 모든 업무 등록/변경 알림 메일을 수신합니다.',
                      style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                    ),
                    const SizedBox(height: 12),
                    Divider(color: context.colors.border, height: 1),
                    Expanded(
                      child: ListView.builder(
                        itemCount: allProjects.length,
                        itemBuilder: (context, index) {
                          final project = allProjects[index];
                          final isSelected = _subscribedProjectIds.contains(project.pk);

                          return CheckboxListTile(
                            contentPadding: EdgeInsets.zero,
                            title: Text(
                              project.name,
                              style: TextStyle(
                                fontSize: 13.5,
                                color: context.colors.textPrimary,
                                fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                              ),
                            ),
                            subtitle: project.description.isNotEmpty
                                ? Text(
                                    project.description,
                                    style: TextStyle(fontSize: 11.5, color: context.colors.textMuted),
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                  )
                                : null,
                            value: isSelected,
                            activeColor: context.colors.accentWork,
                            onChanged: (bool? val) {
                              setModalState(() {
                                if (val == true) {
                                  _subscribedProjectIds.add(project.pk);
                                } else {
                                  _subscribedProjectIds.remove(project.pk);
                                }
                              });
                              setState(() {});
                            },
                          );
                        },
                      ),
                    ),
                    const SizedBox(height: 10),
                    SizedBox(
                      width: double.infinity,
                      child: FilledButton(
                        style: FilledButton.styleFrom(
                          backgroundColor: context.colors.accentWork,
                          shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                          padding: const EdgeInsets.symmetric(vertical: 12),
                        ),
                        onPressed: () => Navigator.pop(ctx),
                        child: Text(
                          '선택 완료 (${_subscribedProjectIds.length}개 선택됨)',
                          style: const TextStyle(fontWeight: FontWeight.bold),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final allProjects = ref.watch(projectListProvider).valueOrNull ?? [];

    return Scaffold(
      backgroundColor: context.colors.bgPrimary,
      appBar: AppBar(
        backgroundColor: context.colors.bgPrimary,
        elevation: 0,
        leading: IconButton(
          icon: Icon(Icons.arrow_back_ios_new_rounded, color: context.colors.textPrimary, size: 20),
          onPressed: () => Navigator.pop(context),
        ),
        title: Text(
          '업무 및 이메일 알림 설정',
          style: AppTextStyles.titleLg.copyWith(
            fontWeight: FontWeight.bold,
            color: context.colors.textPrimary,
          ),
        ),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 12),
            child: TextButton(
              onPressed: _isSaving ? null : _saveSettings,
              child: _isSaving
                  ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                  : Text(
                      '저장',
                      style: TextStyle(
                        color: context.colors.accentWork,
                        fontWeight: FontWeight.bold,
                        fontSize: 14.5,
                      ),
                    ),
            ),
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(strokeWidth: 2))
          : SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // ── 1. 회의 알림 설정 섹션 ─────────────────────────────────────
                  const _SectionHeader(title: '회의 알림 설정 (이메일)', icon: Icons.groups_outlined),
                  Container(
                    decoration: BoxDecoration(
                      color: context.colors.bgCard,
                      border: Border.all(color: context.colors.border, width: 0.8),
                    ),
                    child: Column(
                      children: [
                        _SwitchTile(
                          title: '회의록 등록 시 알림 메일 수신',
                          subtitle: '내가 속한 워크스페이스에 새 회의록이 등록되면 이메일로 수신합니다.',
                          value: _meetingCreated,
                          onChanged: (v) => setState(() => _meetingCreated = v),
                        ),
                        Divider(color: context.colors.border, height: 1),
                        _SwitchTile(
                          title: '회의록 확정 시 알림 메일 수신',
                          subtitle: '회의록이 최종 확정(Confirm)되었을 때 알림 메일을 수신합니다.',
                          value: _meetingConfirmed,
                          onChanged: (v) => setState(() => _meetingConfirmed = v),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),

                  // ── 2. 업무 자동 모니터링 섹션 ──────────────────────────────────
                  const _SectionHeader(title: '업무 모니터링 (자동 지켜보기)', icon: Icons.visibility_outlined),
                  Container(
                    decoration: BoxDecoration(
                      color: context.colors.bgCard,
                      border: Border.all(color: context.colors.border, width: 0.8),
                    ),
                    child: Column(
                      children: [
                        _SwitchTile(
                          title: '내가 생성한 업무 자동 지켜보기',
                          subtitle: '내가 등록한 업무에 댓글이나 상태 변경이 생기면 알림을 받습니다.',
                          value: _autoWatchCreated,
                          onChanged: (v) => setState(() => _autoWatchCreated = v),
                        ),
                        Divider(color: context.colors.border, height: 1),
                        _SwitchTile(
                          title: '나에게 할당된 업무 자동 지켜보기',
                          subtitle: '담당자로 지정된 업무의 진척 및 변경사항을 자동으로 모니터링합니다.',
                          value: _autoWatchAssigned,
                          onChanged: (v) => setState(() => _autoWatchAssigned = v),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),

                  // ── 3. 알림 구독 프로젝트 섹션 ────────────────────────────────
                  const _SectionHeader(title: '알림 구독 프로젝트', icon: Icons.bookmark_added_outlined),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: context.colors.bgCard,
                      border: Border.all(color: context.colors.border, width: 0.8),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              '구독 중인 프로젝트 (${_subscribedProjectIds.length}개)',
                              style: AppTextStyles.titleSm.copyWith(
                                fontWeight: FontWeight.bold,
                                color: context.colors.textPrimary,
                                fontSize: 13,
                              ),
                            ),
                            OutlinedButton.icon(
                              style: OutlinedButton.styleFrom(
                                foregroundColor: context.colors.accentWork,
                                side: BorderSide(color: context.colors.accentWork.withAlpha(120)),
                                shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                minimumSize: Size.zero,
                                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                              ),
                              onPressed: () => _openProjectSelectBottomSheet(allProjects),
                              icon: const Icon(Icons.edit_outlined, size: 13),
                              label: const Text('프로젝트 선택', style: TextStyle(fontSize: 11.5)),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Text(
                          '선택한 프로젝트의 모든 업무 생성 및 수정 이메일 알림을 수신합니다.',
                          style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 11.5),
                        ),
                        const SizedBox(height: 10),
                        if (_subscribedProjectIds.isEmpty) ...[
                          Container(
                            width: double.infinity,
                            padding: const EdgeInsets.symmetric(vertical: 14),
                            color: context.colors.bgSurface,
                            child: Center(
                              child: Text(
                                '구독 중인 프로젝트가 없습니다.\n담당 업무 및 모니터링 업무에 대한 알림만 수신합니다.',
                                textAlign: TextAlign.center,
                                style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                              ),
                            ),
                          ),
                        ] else ...[
                          Wrap(
                            spacing: 6,
                            runSpacing: 6,
                            children: _subscribedProjectIds.map((pid) {
                              final matched = allProjects.where((p) => p.pk == pid).toList();
                              final name = matched.isNotEmpty ? matched.first.name : '프로젝트 #$pid';
                              return Chip(
                                label: Text(name, style: const TextStyle(fontSize: 11.5)),
                                backgroundColor: context.colors.accentWork.withAlpha(25),
                                labelStyle: TextStyle(color: context.colors.accentWork, fontWeight: FontWeight.bold),
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(4),
                                  side: BorderSide(color: context.colors.accentWork.withAlpha(90), width: 0.8),
                                ),
                                deleteIcon: const Icon(Icons.close_rounded, size: 14),
                                deleteIconColor: context.colors.accentWork,
                                onDeleted: () {
                                  setState(() => _subscribedProjectIds.remove(pid));
                                },
                              );
                            }).toList(),
                          ),
                        ],
                      ],
                    ),
                  ),
                  const SizedBox(height: 32),
                ],
              ),
            ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  final String title;
  final IconData icon;

  const _SectionHeader({required this.title, required this.icon});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(left: 4, bottom: 8),
      child: Row(
        children: [
          Icon(icon, size: 17, color: context.colors.accentWork),
          const SizedBox(width: 6),
          Text(
            title,
            style: AppTextStyles.titleSm.copyWith(
              color: context.colors.textPrimary,
              fontWeight: FontWeight.bold,
              fontSize: 13,
            ),
          ),
        ],
      ),
    );
  }
}

class _SwitchTile extends StatelessWidget {
  final String title;
  final String subtitle;
  final bool value;
  final ValueChanged<bool> onChanged;

  const _SwitchTile({
    required this.title,
    required this.subtitle,
    required this.value,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: context.colors.textPrimary,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  subtitle,
                  style: TextStyle(
                    fontSize: 11,
                    color: context.colors.textMuted,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          Switch(
            value: value,
            onChanged: onChanged,
            activeTrackColor: context.colors.accentWork,
            activeThumbColor: Colors.white,
          ),
        ],
      ),
    );
  }
}
