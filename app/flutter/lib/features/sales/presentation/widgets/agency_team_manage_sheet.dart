import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/models/sales_models.dart';
import '../../data/sales_repository.dart';
import '../../providers/sales_provider.dart';

/// 대행사 및 영업 팀 조직 체계 관리 바텀시트 열기 함수
void showAgencyTeamManageSheet(
  BuildContext context, {
  required int projectId,
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
      child: AgencyTeamManageSheet(projectId: projectId),
    ),
  );
}

class AgencyTeamManageSheet extends ConsumerStatefulWidget {
  final int projectId;

  const AgencyTeamManageSheet({super.key, required this.projectId});

  @override
  ConsumerState<AgencyTeamManageSheet> createState() =>
      _AgencyTeamManageSheetState();
}

class _AgencyTeamManageSheetState
    extends ConsumerState<AgencyTeamManageSheet> {
  Future<void> _openAgencyDialog({SalesAgencyModel? agency}) async {
    final nameController = TextEditingController(text: agency?.name ?? '');
    final ceoController = TextEditingController(text: agency?.ceoName ?? '');
    final phoneController = TextEditingController(text: agency?.phone ?? '');
    final bizController = TextEditingController(text: agency?.businessNumber ?? '');
    bool isDirect = agency?.isDirectManaged ?? false;

    final saved = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDlgState) => AlertDialog(
          shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
          title: Text(
            agency == null ? '신규 분양 대행사 등록' : '대행사 정보 수정',
            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
          ),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                TextField(
                  controller: nameController,
                  decoration: const InputDecoration(
                    labelText: '대행사명 *',
                    hintText: '예: ㈜미래분양대행',
                    border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                  ),
                  style: const TextStyle(fontSize: 13),
                ),
                const SizedBox(height: 14),
                Text(
                  '운영 형태',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: context.colors.textSecond,
                  ),
                ),
                const SizedBox(height: 6),
                Row(
                  children: [
                    Expanded(
                      child: InkWell(
                        onTap: () => setDlgState(() => isDirect = false),
                        child: Container(
                          padding: const EdgeInsets.symmetric(vertical: 9),
                          decoration: BoxDecoration(
                            color: !isDirect
                                ? const Color(0xFF6366F1).withAlpha(18)
                                : context.colors.bgSurface,
                            border: Border.all(
                              color: !isDirect
                                  ? const Color(0xFF6366F1)
                                  : context.colors.border,
                              width: !isDirect ? 1.4 : 0.8,
                            ),
                            borderRadius: BorderRadius.zero,
                          ),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(
                                !isDirect
                                    ? Icons.check_circle
                                    : Icons.radio_button_unchecked,
                                size: 15,
                                color: !isDirect
                                    ? const Color(0xFF6366F1)
                                    : context.colors.textMuted,
                              ),
                              const SizedBox(width: 6),
                              Text(
                                '외주 대행',
                                style: TextStyle(
                                  fontSize: 13,
                                  fontWeight: !isDirect
                                      ? FontWeight.bold
                                      : FontWeight.normal,
                                  color: !isDirect
                                      ? const Color(0xFF6366F1)
                                      : context.colors.textPrimary,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: InkWell(
                        onTap: () => setDlgState(() => isDirect = true),
                        child: Container(
                          padding: const EdgeInsets.symmetric(vertical: 9),
                          decoration: BoxDecoration(
                            color: isDirect
                                ? const Color(0xFF6366F1).withAlpha(18)
                                : context.colors.bgSurface,
                            border: Border.all(
                              color: isDirect
                                  ? const Color(0xFF6366F1)
                                  : context.colors.border,
                              width: isDirect ? 1.4 : 0.8,
                            ),
                            borderRadius: BorderRadius.zero,
                          ),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(
                                isDirect
                                    ? Icons.check_circle
                                    : Icons.radio_button_unchecked,
                                size: 15,
                                color: isDirect
                                    ? const Color(0xFF6366F1)
                                    : context.colors.textMuted,
                              ),
                              const SizedBox(width: 6),
                              Text(
                                '직영 대행',
                                style: TextStyle(
                                  fontSize: 13,
                                  fontWeight: isDirect
                                      ? FontWeight.bold
                                      : FontWeight.normal,
                                  color: isDirect
                                      ? const Color(0xFF6366F1)
                                      : context.colors.textPrimary,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 14),
                TextField(
                  controller: ceoController,
                  decoration: const InputDecoration(
                    labelText: '대표자명',
                    border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                  ),
                  style: const TextStyle(fontSize: 13),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: phoneController,
                  keyboardType: TextInputType.phone,
                  decoration: const InputDecoration(
                    labelText: '대표 전화번호',
                    border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                  ),
                  style: const TextStyle(fontSize: 13),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: bizController,
                  decoration: const InputDecoration(
                    labelText: '사업자등록번호',
                    border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                  ),
                  style: const TextStyle(fontSize: 13),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(ctx).pop(false),
              child: const Text('취소'),
            ),
            FilledButton(
              style: FilledButton.styleFrom(
                backgroundColor: const Color(0xFF6366F1),
                shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
              ),
              onPressed: () async {
                if (nameController.text.trim().isEmpty) return;
                final repository = ref.read(salesRepositoryProvider);
                final payload = {
                  'project': widget.projectId,
                  'name': nameController.text.trim(),
                  'is_direct_managed': isDirect,
                  'ceo_name': ceoController.text.trim(),
                  'phone': phoneController.text.trim(),
                  'business_number': bizController.text.trim(),
                };
                if (agency != null) {
                  await repository.updateSalesAgency(agency.id, payload);
                } else {
                  await repository.createSalesAgency(payload);
                }
                if (ctx.mounted) {
                  Navigator.of(ctx).pop(true);
                }
              },
              child: const Text('저장'),
            ),
          ],
        ),
      ),
    );

    if (saved == true) {
      ref.invalidate(salesAgenciesProvider);
      ref.invalidate(salesTeamsProvider);
    }
  }

  Future<void> _openTeamDialog({required int agencyId, SalesTeamModel? team}) async {
    final nameController = TextEditingController(text: team?.name ?? '');

    final saved = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
        title: Text(
          team == null ? '영업 팀 신설' : '팀 명칭 수정',
          style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: nameController,
              decoration: const InputDecoration(
                labelText: '팀 / 본부 명칭 *',
                hintText: '예: 영업1본부, 분양1팀',
                border: OutlineInputBorder(borderRadius: BorderRadius.zero),
              ),
              style: const TextStyle(fontSize: 13),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text('취소'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: const Color(0xFF6366F1),
              shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
            ),
            onPressed: () async {
              if (nameController.text.trim().isEmpty) return;
              final repository = ref.read(salesRepositoryProvider);
              final payload = {
                'agency': agencyId,
                'name': nameController.text.trim(),
              };
              if (team != null) {
                await repository.updateSalesTeam(team.id, payload);
              } else {
                await repository.createSalesTeam(payload);
              }
              if (ctx.mounted) {
                Navigator.of(ctx).pop(true);
              }
            },
            child: const Text('저장'),
          ),
        ],
      ),
    );

    if (saved == true) {
      ref.invalidate(salesTeamsProvider);
    }
  }

  Future<void> _deleteAgency(SalesAgencyModel agency) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
        title: const Text('대행사 삭제 확인', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        content: Text("'${agency.name}' 대행사를 삭제하시겠습니까?\n(소속 팀 및 인력이 함께 삭제되거나 오류가 발생할 수 있습니다)"),
        actions: [
          TextButton(onPressed: () => Navigator.of(ctx).pop(false), child: const Text('취소')),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: context.colors.error,
              shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
            ),
            onPressed: () => Navigator.of(ctx).pop(true),
            child: const Text('삭제'),
          ),
        ],
      ),
    );
    if (confirm == true) {
      final repository = ref.read(salesRepositoryProvider);
      await repository.deleteSalesAgency(agency.id);
      ref.invalidate(salesAgenciesProvider);
      ref.invalidate(salesTeamsProvider);
    }
  }

  Future<void> _deleteTeam(SalesTeamModel team) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
        title: const Text('영업 팀 삭제 확인', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        content: Text("'${team.name}' 팀을 삭제하시겠습니까?"),
        actions: [
          TextButton(onPressed: () => Navigator.of(ctx).pop(false), child: const Text('취소')),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: context.colors.error,
              shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
            ),
            onPressed: () => Navigator.of(ctx).pop(true),
            child: const Text('삭제'),
          ),
        ],
      ),
    );
    if (confirm == true) {
      final repository = ref.read(salesRepositoryProvider);
      await repository.deleteSalesTeam(team.id);
      ref.invalidate(salesTeamsProvider);
    }
  }

  @override
  Widget build(BuildContext context) {
    final agenciesAsync = ref.watch(salesAgenciesProvider);
    final teams = ref.watch(salesTeamsProvider).valueOrNull ?? [];

    return Container(
      constraints: BoxConstraints(
        maxHeight: MediaQuery.of(context).size.height * 0.85,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // 드래그 핸들
          Center(
            child: Container(
              margin: const EdgeInsets.only(top: 10, bottom: 8),
              width: 38,
              height: 4,
              decoration: BoxDecoration(
                color: context.colors.textDisabled,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),

          // 헤더
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
            child: Row(
              children: [
                const Icon(Icons.account_tree_outlined, size: 20, color: Color(0xFF6366F1)),
                const SizedBox(width: 8),
                Text(
                  '영업 조직 체계 관리',
                  style: AppTextStyles.titleSm.copyWith(
                    color: context.colors.textPrimary,
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                  ),
                ),
                const Spacer(),
                IconButton(
                  icon: const Icon(Icons.close_rounded, size: 20),
                  onPressed: () => Navigator.of(context).pop(),
                  color: context.colors.textMuted,
                ),
              ],
            ),
          ),
          const Divider(height: 1),

          // 상단 액션 바
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  '분양 대행사 및 산하 팀 목록',
                  style: AppTextStyles.label.copyWith(color: context.colors.textMuted, fontWeight: FontWeight.bold),
                ),
                FilledButton.icon(
                  style: FilledButton.styleFrom(
                    backgroundColor: const Color(0xFF6366F1),
                    shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                    minimumSize: Size.zero,
                  ),
                  icon: const Icon(Icons.add, size: 14),
                  label: const Text('대행사 등록', style: TextStyle(fontSize: 12)),
                  onPressed: () => _openAgencyDialog(),
                ),
              ],
            ),
          ),

          // 조직 목록
          Flexible(
            child: agenciesAsync.when(
              loading: () => const Center(
                child: Padding(
                  padding: EdgeInsets.all(40),
                  child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF6366F1)),
                ),
              ),
              error: (err, _) => Padding(
                padding: const EdgeInsets.all(20),
                child: Text('데이터 로드 오류: $err', style: TextStyle(color: context.colors.error)),
              ),
              data: (agencies) {
                if (agencies.isEmpty) {
                  return Container(
                    padding: const EdgeInsets.all(40),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.domain_disabled_rounded, size: 36, color: context.colors.textMuted),
                        const SizedBox(height: 10),
                        const Text('등록된 분양 대행사가 없습니다.', style: TextStyle(fontWeight: FontWeight.bold)),
                        const SizedBox(height: 6),
                        const Text('상단 [+ 대행사 등록] 버튼을 눌러 대행사를 먼저 등록해 주세요.', style: TextStyle(fontSize: 12, color: Colors.grey)),
                      ],
                    ),
                  );
                }

                return ListView.builder(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 4),
                  itemCount: agencies.length,
                  itemBuilder: (ctx, idx) {
                    final agency = agencies[idx];
                    final agencyTeams = teams.where((t) => t.agency == agency.id).toList();

                    return Container(
                      margin: const EdgeInsets.only(bottom: 14),
                      decoration: BoxDecoration(
                        color: context.colors.bgSurface,
                        border: Border.all(color: context.colors.border, width: 0.8),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // 대행사 헤더
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                            color: context.colors.bgCard,
                            child: Row(
                              children: [
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                  decoration: BoxDecoration(
                                    color: agency.isDirectManaged
                                        ? const Color(0xFF10B981).withAlpha(20)
                                        : const Color(0xFFF59E0B).withAlpha(20),
                                    border: Border.all(
                                      color: agency.isDirectManaged
                                          ? const Color(0xFF10B981)
                                          : const Color(0xFFF59E0B),
                                      width: 0.8,
                                    ),
                                  ),
                                  child: Text(
                                    agency.isDirectManaged ? '직영' : '외주',
                                    style: TextStyle(
                                      fontSize: 10,
                                      fontWeight: FontWeight.bold,
                                      color: agency.isDirectManaged
                                          ? const Color(0xFF10B981)
                                          : const Color(0xFFF59E0B),
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        agency.name,
                                        style: AppTextStyles.titleSm.copyWith(
                                          color: context.colors.textPrimary,
                                          fontWeight: FontWeight.bold,
                                          fontSize: 13.5,
                                        ),
                                      ),
                                      if (agency.ceoName != null || agency.phone != null)
                                        Text(
                                          '대표: ${agency.ceoName ?? '-'} · 연락처: ${agency.phone ?? '-'}',
                                          style: AppTextStyles.caption.copyWith(
                                            color: context.colors.textMuted,
                                            fontSize: 10.5,
                                          ),
                                        ),
                                    ],
                                  ),
                                ),
                                IconButton(
                                  icon: const Icon(Icons.edit_outlined, size: 16),
                                  onPressed: () => _openAgencyDialog(agency: agency),
                                  color: context.colors.textMuted,
                                  constraints: const BoxConstraints(minWidth: 28, minHeight: 28),
                                  padding: EdgeInsets.zero,
                                ),
                                IconButton(
                                  icon: const Icon(Icons.delete_outline_rounded, size: 16),
                                  onPressed: () => _deleteAgency(agency),
                                  color: context.colors.error,
                                  constraints: const BoxConstraints(minWidth: 28, minHeight: 28),
                                  padding: EdgeInsets.zero,
                                ),
                              ],
                            ),
                          ),
                          const Divider(height: 1),

                          // 산하 팀 목록
                          Padding(
                            padding: const EdgeInsets.all(10),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Text(
                                      '산하 팀 (${agencyTeams.length}개)',
                                      style: AppTextStyles.caption.copyWith(
                                        color: context.colors.textMuted,
                                        fontWeight: FontWeight.bold,
                                        fontSize: 11,
                                      ),
                                    ),
                                    InkWell(
                                      onTap: () => _openTeamDialog(agencyId: agency.id),
                                      child: const Padding(
                                        padding: EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                                        child: Row(
                                          children: [
                                            Icon(Icons.add, size: 12, color: Color(0xFF6366F1)),
                                            SizedBox(width: 2),
                                            Text(
                                              '팀 추가',
                                              style: TextStyle(
                                                color: Color(0xFF6366F1),
                                                fontSize: 11,
                                                fontWeight: FontWeight.bold,
                                              ),
                                            ),
                                          ],
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 6),
                                if (agencyTeams.isEmpty)
                                  Padding(
                                    padding: const EdgeInsets.symmetric(vertical: 8),
                                    child: Text(
                                      '등록된 팀이 없습니다. [+ 팀 추가]를 눌러 팀을 등록하세요.',
                                      style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 11),
                                    ),
                                  )
                                else
                                  Wrap(
                                    spacing: 8,
                                    runSpacing: 6,
                                    children: agencyTeams.map((t) {
                                      return Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                        decoration: BoxDecoration(
                                          color: context.colors.bgCard,
                                          border: Border.all(color: context.colors.border, width: 0.8),
                                        ),
                                        child: Row(
                                          mainAxisSize: MainAxisSize.min,
                                          children: [
                                            Text(
                                              '${t.name} (${t.membersCount}명)',
                                              style: TextStyle(
                                                fontSize: 11.5,
                                                color: context.colors.textPrimary,
                                              ),
                                            ),
                                            const SizedBox(width: 4),
                                            InkWell(
                                              onTap: () => _openTeamDialog(agencyId: agency.id, team: t),
                                              child: const Icon(Icons.edit_outlined, size: 12, color: Colors.grey),
                                            ),
                                            const SizedBox(width: 4),
                                            InkWell(
                                              onTap: () => _deleteTeam(t),
                                              child: const Icon(Icons.close_rounded, size: 12, color: Colors.red),
                                            ),
                                          ],
                                        ),
                                      );
                                    }).toList(),
                                  ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    );
                  },
                );
              },
            ),
          ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }
}
