import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/providers/auth_provider.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../../../core/widgets/error_view.dart';
import '../../../../core/widgets/loading_shimmer.dart';
import '../../approval/data/approval_repository.dart';
import '../../approval/data/models/approval_model.dart';
import '../../approval/providers/approval_providers.dart';

class DelegationSettingsScreen extends ConsumerStatefulWidget {
  const DelegationSettingsScreen({super.key});

  @override
  ConsumerState<DelegationSettingsScreen> createState() => _DelegationSettingsScreenState();
}

class _DelegationSettingsScreenState extends ConsumerState<DelegationSettingsScreen> {
  Future<void> _openAddOrEditModal({ApprovalDelegationModel? editItem}) async {
    final repo = ref.read(approvalRepositoryProvider);

    DateTime startDate = editItem != null
        ? DateTime.tryParse(editItem.startDate) ?? DateTime.now()
        : DateTime.now();
    DateTime endDate = editItem != null
        ? DateTime.tryParse(editItem.endDate) ?? DateTime.now().add(const Duration(days: 7))
        : DateTime.now().add(const Duration(days: 7));
    final reasonController = TextEditingController(text: editItem?.reason ?? '');
    bool isActive = editItem?.isActive ?? true;

    // 직원/사용자 목록 로드
    int? selectedDelegateeId = editItem?.delegatee?.pk;
    bool isSaving = false;
    final allUsers = ref.read(usersListProvider).valueOrNull ?? [];
    final myUser = ref.read(currentUserProvider).valueOrNull;
    // 1. 활성 계정(is_active=True), 2. 실제 임직원(has_staff=True 또는 is_superuser=True), 3. 본인 제외 필터링
    final eligibleUsers = allUsers
        .where((u) => u.pk != myUser?.pk && u.isActive && (u.hasStaff || u.isSuperuser))
        .toList();

    await showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: context.colors.bgCard,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) {
        return StatefulBuilder(
          builder: (ctx, setModalState) {
            return Padding(
              padding: EdgeInsets.only(
                left: 20,
                right: 20,
                top: 20,
                bottom: MediaQuery.of(ctx).viewInsets.bottom + 24,
              ),
              child: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          editItem != null ? '결재 위임(대결) 수정' : '신규 대결자 지정',
                          style: AppTextStyles.titleMd.copyWith(
                            fontWeight: FontWeight.w800,
                            color: context.colors.textPrimary,
                          ),
                        ),
                        IconButton(
                          icon: const Icon(Icons.close),
                          onPressed: () => Navigator.pop(ctx),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),

                    // ── 1. 대결자(위임받을 직원) 선택 ──────────────────────────
                    Row(
                      children: [
                        Text(
                          '대결자 (위임받을 직원)',
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w700,
                            color: context.colors.textPrimary,
                          ),
                        ),
                        const SizedBox(width: 4),
                        const Text('*', style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold)),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Builder(
                      builder: (builderCtx) {
                        final currentSelectedUser = allUsers
                            .where((u) => u.pk == selectedDelegateeId)
                            .firstOrNull;

                        return InkWell(
                          onTap: () async {
                            final picked = await showModalBottomSheet<int>(
                              context: ctx,
                              isScrollControlled: true,
                              backgroundColor: context.colors.bgCard,
                              shape: const RoundedRectangleBorder(
                                borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
                              ),
                              builder: (sheetCtx) {
                                return SafeArea(
                                  child: Container(
                                    constraints: BoxConstraints(
                                      maxHeight: MediaQuery.of(sheetCtx).size.height * 0.6,
                                    ),
                                    child: Column(
                                      mainAxisSize: MainAxisSize.min,
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Padding(
                                          padding: const EdgeInsets.fromLTRB(20, 18, 20, 12),
                                          child: Row(
                                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                            children: [
                                              Text(
                                                '대결자 (위임받을 직원) 선택',
                                                style: AppTextStyles.titleMd.copyWith(
                                                  fontWeight: FontWeight.w800,
                                                  color: context.colors.textPrimary,
                                                ),
                                              ),
                                              IconButton(
                                                icon: const Icon(Icons.close),
                                                onPressed: () => Navigator.pop(sheetCtx),
                                              ),
                                            ],
                                          ),
                                        ),
                                        const Divider(height: 1),
                                        if (eligibleUsers.isEmpty)
                                          Padding(
                                            padding: const EdgeInsets.all(32),
                                            child: Center(
                                              child: Text(
                                                '선택 가능한 임직원이 없습니다.',
                                                style: TextStyle(color: context.colors.textMuted),
                                              ),
                                            ),
                                          )
                                        else
                                          Expanded(
                                            child: ListView.separated(
                                              padding: const EdgeInsets.symmetric(vertical: 8),
                                              itemCount: eligibleUsers.length,
                                              separatorBuilder: (_, __) => const Divider(height: 1, indent: 16, endIndent: 16),
                                              itemBuilder: (_, idx) {
                                                final u = eligibleUsers[idx];
                                                final isSelected = u.pk == selectedDelegateeId;
                                                return ListTile(
                                                  leading: CircleAvatar(
                                                    radius: 18,
                                                    backgroundColor: isSelected
                                                        ? context.colors.accentApproval
                                                        : context.colors.bgSurface,
                                                    child: Text(
                                                      u.initial,
                                                      style: TextStyle(
                                                        color: isSelected ? Colors.white : context.colors.textPrimary,
                                                        fontWeight: FontWeight.bold,
                                                        fontSize: 13,
                                                      ),
                                                    ),
                                                  ),
                                                  title: Text(
                                                    u.displayName,
                                                    style: TextStyle(
                                                      fontSize: 14,
                                                      fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
                                                      color: isSelected
                                                          ? context.colors.accentApproval
                                                          : context.colors.textPrimary,
                                                    ),
                                                  ),
                                                  subtitle: u.email != null
                                                      ? Text(u.email!, style: TextStyle(fontSize: 12, color: context.colors.textMuted))
                                                      : null,
                                                  trailing: isSelected
                                                      ? Icon(Icons.check_circle_rounded, color: context.colors.accentApproval)
                                                      : null,
                                                  onTap: () => Navigator.pop(sheetCtx, u.pk),
                                                );
                                              },
                                            ),
                                          ),
                                      ],
                                    ),
                                  ),
                                );
                              },
                            );
                            if (picked != null) {
                              setModalState(() => selectedDelegateeId = picked);
                            }
                          },
                          borderRadius: BorderRadius.circular(4),
                          child: Container(
                            width: double.infinity,
                            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
                            decoration: BoxDecoration(
                              color: context.colors.bgInput,
                              borderRadius: BorderRadius.circular(4),
                              border: Border.all(color: context.colors.border),
                            ),
                            child: Row(
                              children: [
                                Icon(Icons.person_outline_rounded, size: 20, color: context.colors.accentApproval),
                                const SizedBox(width: 10),
                                Expanded(
                                  child: Text(
                                    currentSelectedUser != null
                                        ? currentSelectedUser.displayName
                                        : '대결 권한을 위임할 직원을 선택하세요',
                                    style: TextStyle(
                                      fontSize: 13.5,
                                      color: currentSelectedUser != null
                                          ? context.colors.textPrimary
                                          : context.colors.textMuted,
                                      fontWeight: currentSelectedUser != null ? FontWeight.w600 : FontWeight.normal,
                                    ),
                                  ),
                                ),
                                Icon(Icons.keyboard_arrow_down_rounded, color: context.colors.textMuted),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
                    const SizedBox(height: 16),

                    // ── 2. 위임 기간 선택 ────────────────────────────────────
                    Row(
                      children: [
                        Text(
                          '위임 기간',
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w700,
                            color: context.colors.textPrimary,
                          ),
                        ),
                        const SizedBox(width: 4),
                        const Text('*', style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold)),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Expanded(
                          child: OutlinedButton.icon(
                            onPressed: () async {
                              final picked = await showDatePicker(
                                context: ctx,
                                initialDate: startDate,
                                firstDate: DateTime.now().subtract(const Duration(days: 30)),
                                lastDate: DateTime.now().add(const Duration(days: 365)),
                              );
                              if (picked != null) {
                                setModalState(() => startDate = picked);
                              }
                            },
                            icon: const Icon(Icons.calendar_today, size: 16),
                            label: Text(
                              '${startDate.year}-${startDate.month.toString().padLeft(2, '0')}-${startDate.day.toString().padLeft(2, '0')}',
                              style: const TextStyle(fontSize: 12.5),
                            ),
                          ),
                        ),
                        const Padding(
                          padding: EdgeInsets.symmetric(horizontal: 6),
                          child: Text('~'),
                        ),
                        Expanded(
                          child: OutlinedButton.icon(
                            onPressed: () async {
                              final picked = await showDatePicker(
                                context: ctx,
                                initialDate: endDate,
                                firstDate: startDate,
                                lastDate: DateTime.now().add(const Duration(days: 365)),
                              );
                              if (picked != null) {
                                setModalState(() => endDate = picked);
                              }
                            },
                            icon: const Icon(Icons.calendar_today, size: 16),
                            label: Text(
                              '${endDate.year}-${endDate.month.toString().padLeft(2, '0')}-${endDate.day.toString().padLeft(2, '0')}',
                              style: const TextStyle(fontSize: 12.5),
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),

                    // ── 3. 대결 사유 ──────────────────────────────────────────
                    Text(
                      '부재 및 위임 사유',
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                        color: context.colors.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 8),
                    TextField(
                      controller: reasonController,
                      decoration: InputDecoration(
                        hintText: '예: 하기 휴가, 해외 출장 등으로 인한 대결',
                        hintStyle: TextStyle(color: context.colors.textMuted, fontSize: 13),
                        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                        border: OutlineInputBorder(
                          borderSide: BorderSide(color: context.colors.border),
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),

                    // ── 4. 활성화 토글 ────────────────────────────────────────
                    SwitchListTile(
                      contentPadding: EdgeInsets.zero,
                      title: const Text('대결 권한 즉시 활성화', style: TextStyle(fontSize: 13.5, fontWeight: FontWeight.w600)),
                      value: isActive,
                      onChanged: (val) => setModalState(() => isActive = val),
                    ),
                    const SizedBox(height: 20),

                    // ── 5. 저장 버튼 ──────────────────────────────────────────
                    SizedBox(
                      width: double.infinity,
                      height: 48,
                      child: ElevatedButton(
                        onPressed: isSaving
                            ? null
                            : () async {
                                if (selectedDelegateeId == null) {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(
                                      content: Text('대결 권한을 위임할 직원을 선택해주세요.'),
                                      behavior: SnackBarBehavior.floating,
                                      backgroundColor: Colors.redAccent,
                                    ),
                                  );
                                  return;
                                }

                                setModalState(() => isSaving = true);
                                try {
                                  final startStr = '${startDate.year}-${startDate.month.toString().padLeft(2, '0')}-${startDate.day.toString().padLeft(2, '0')}';
                                  final endStr = '${endDate.year}-${endDate.month.toString().padLeft(2, '0')}-${endDate.day.toString().padLeft(2, '0')}';

                                  if (editItem != null) {
                                    await repo.updateDelegation(editItem.id, {
                                      'delegatee_id': selectedDelegateeId,
                                      'start_date': startStr,
                                      'end_date': endStr,
                                      'reason': reasonController.text.trim(),
                                      'is_active': isActive,
                                    });
                                  } else {
                                    await repo.createDelegation({
                                      'delegatee_id': selectedDelegateeId,
                                      'start_date': startStr,
                                      'end_date': endStr,
                                      'reason': reasonController.text.trim(),
                                      'is_active': isActive,
                                    });
                                  }

                                  ref.invalidate(delegationsProvider);
                                  if (ctx.mounted) Navigator.pop(ctx);
                                  if (mounted) {
                                    ScaffoldMessenger.of(context).showSnackBar(
                                      SnackBar(
                                        content: Text(editItem != null ? '위임 설정이 수정되었습니다.' : '대결자가 지정되었습니다.'),
                                        backgroundColor: context.colors.success,
                                      ),
                                    );
                                  }
                                } catch (e) {
                                  setModalState(() => isSaving = false);
                                  if (mounted) {
                                    ScaffoldMessenger.of(context).showSnackBar(
                                      SnackBar(
                                        content: Text('오류가 발생했습니다: $e'),
                                        backgroundColor: context.colors.error,
                                      ),
                                    );
                                  }
                                }
                              },
                        style: ElevatedButton.styleFrom(
                          backgroundColor: context.colors.accentApproval,
                          shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                        ),
                        child: isSaving
                            ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                            : Text(editItem != null ? '수정 완료' : '대결자 등록', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
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
    final delegationsAsync = ref.watch(delegationsProvider);
    final myUser = ref.watch(currentUserProvider).valueOrNull;
    ref.watch(usersListProvider); // 대결자 선택 드롭다운용 사용자 목록 사전 로드

    return Scaffold(
      backgroundColor: context.colors.bgPrimary,
      appBar: AppBar(
        title: Text(
          '부재 및 결재 위임(대결)',
          style: AppTextStyles.titleMd.copyWith(
            fontWeight: FontWeight.w800,
            color: context.colors.textPrimary,
          ),
        ),
        backgroundColor: context.colors.bgCard,
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 안내 배너
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: context.colors.accentApproval.withAlpha(20),
                borderRadius: BorderRadius.zero,
                border: Border.all(color: context.colors.accentApproval.withAlpha(60), width: 0.8),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(Icons.shield_outlined, color: context.colors.accentApproval, size: 20),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '결재 권한 위임(대결·代決) 안내',
                          style: TextStyle(
                            fontWeight: FontWeight.w700,
                            color: context.colors.accentApprovalDeep,
                            fontSize: 13.5,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          '출장, 휴가 등으로 부재 시 결재 권한을 특정 임원/직원에게 위임할 수 있습니다. 위임 기간 동안 대결자가 대신 승인/반려하며 모든 이력은 공식 기록됩니다.',
                          style: TextStyle(fontSize: 12, color: context.colors.textSecond, height: 1.4),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  '결재 위임 내역',
                  style: AppTextStyles.titleSm.copyWith(
                    fontWeight: FontWeight.w700,
                    color: context.colors.textPrimary,
                  ),
                ),
                TextButton.icon(
                  onPressed: () => _openAddOrEditModal(),
                  icon: const Icon(Icons.add, size: 16),
                  label: const Text('신규 지정', style: TextStyle(fontWeight: FontWeight.w700)),
                ),
              ],
            ),
            const SizedBox(height: 8),

            delegationsAsync.when(
              data: (list) {
                if (list.isEmpty) {
                  return Container(
                    padding: const EdgeInsets.symmetric(vertical: 40),
                    alignment: Alignment.center,
                    decoration: BoxDecoration(
                      color: context.colors.bgCard,
                      border: Border.all(color: context.colors.border, width: 0.8),
                    ),
                    child: Text('등록된 결재 위임 내역이 없습니다.', style: TextStyle(color: context.colors.textMuted)),
                  );
                }

                return ListView.separated(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: list.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 10),
                  itemBuilder: (ctx, idx) {
                    final item = list[idx];
                    final isMyDelegation = item.delegator?.pk == myUser?.pk;
                    final delName = (item.delegator?.fullName != null && item.delegator!.fullName!.isNotEmpty)
                        ? item.delegator!.fullName!
                        : (item.delegator?.username ?? '본인');
                    final delegateeName = (item.delegatee?.fullName != null && item.delegatee!.fullName!.isNotEmpty)
                        ? item.delegatee!.fullName!
                        : (item.delegatee?.username ?? '대결자');

                    return Container(
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: context.colors.bgCard,
                        border: Border.all(
                          color: item.isValidNow ? context.colors.success.withAlpha(120) : context.colors.border,
                          width: item.isValidNow ? 1.2 : 0.8,
                        ),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                decoration: BoxDecoration(
                                  color: item.isValidNow
                                      ? context.colors.success.withAlpha(25)
                                      : (item.isActive ? Colors.blue.withAlpha(25) : Colors.grey.withAlpha(25)),
                                ),
                                child: Text(
                                  item.isValidNow ? '진행중 (유효)' : (item.isActive ? '예정/대기' : '해제됨'),
                                  style: TextStyle(
                                    fontSize: 11,
                                    fontWeight: FontWeight.w700,
                                    color: item.isValidNow
                                        ? context.colors.success
                                        : (item.isActive ? Colors.blue : Colors.grey),
                                  ),
                                ),
                              ),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  '$delName ➔ $delegateeName',
                                  style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13.5),
                                ),
                              ),
                              if (isMyDelegation) ...[
                                IconButton(
                                  icon: const Icon(Icons.edit_outlined, size: 18),
                                  onPressed: () => _openAddOrEditModal(editItem: item),
                                  padding: EdgeInsets.zero,
                                  constraints: const BoxConstraints(),
                                ),
                                const SizedBox(width: 8),
                                IconButton(
                                  icon: Icon(Icons.delete_outline, size: 18, color: context.colors.error),
                                  onPressed: () async {
                                    final confirmed = await showDialog<bool>(
                                      context: context,
                                      builder: (ctx) => AlertDialog(
                                        title: const Text('위임 삭제'),
                                        content: const Text('해당 결재 위임 설정을 삭제하시겠습니까?'),
                                        actions: [
                                          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('취소')),
                                          TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('삭제', style: TextStyle(color: Colors.red))),
                                        ],
                                      ),
                                    );
                                    if (confirmed == true) {
                                      await ref.read(approvalRepositoryProvider).deleteDelegation(item.id);
                                      ref.invalidate(delegationsProvider);
                                    }
                                  },
                                  padding: EdgeInsets.zero,
                                  constraints: const BoxConstraints(),
                                ),
                              ],
                            ],
                          ),
                          const SizedBox(height: 8),
                          Text(
                            '기간: ${item.startDate} ~ ${item.endDate}',
                            style: TextStyle(fontSize: 12, color: context.colors.textMuted),
                          ),
                          if (item.reason != null && item.reason!.isNotEmpty) ...[
                            const SizedBox(height: 4),
                            Text(
                              '사유: ${item.reason}',
                              style: TextStyle(fontSize: 12.5, color: context.colors.textSecond),
                            ),
                          ],
                        ],
                      ),
                    );
                  },
                );
              },
              loading: () => const LoadingShimmer(itemCount: 3, itemHeight: 80),
              error: (e, _) => ErrorView(message: '위임 목록을 불러올 수 없습니다: $e'),
            ),
          ],
        ),
      ),
    );
  }
}
