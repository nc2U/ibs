import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/contract_repository.dart';
import '../../data/models/contract_models.dart';
import '../../providers/contract_provider.dart';

/// 🏠 계약자 주소 변경 이력 및 신규 등록 시트
class ContractorAddressBottomSheet extends ConsumerWidget {
  final ContractItemModel contract;

  const ContractorAddressBottomSheet({
    super.key,
    required this.contract,
  });

  /// 바텀시트 표출 편의 헬퍼 메서드
  static void show(BuildContext context, {required ContractItemModel contract}) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => ContractorAddressBottomSheet(contract: contract),
    );
  }

  void _showAddAddressDialog(BuildContext context, WidgetRef ref) {
    final contractor = contract.contractor;
    if (contractor == null) return;

    showDialog(
      context: context,
      builder: (ctx) => _NewAddressDialog(
        contractorId: contractor.pk,
        contractorName: contractor.name,
        unitStr: contract.displayUnit,
        onSuccess: () {
          ref.invalidate(contractorAddressHistoryProvider(contractor.pk));
          ref.invalidate(validContractListProvider);
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final contractor = contract.contractor;
    if (contractor == null) {
      return Container(
        height: 200,
        color: context.colors.bgCard,
        child: const Center(child: Text('계약자 정보가 없습니다.')),
      );
    }

    final addressAsync = ref.watch(contractorAddressHistoryProvider(contractor.pk));

    return SafeArea(
      child: Container(
        height: MediaQuery.of(context).size.height * 0.75,
        color: context.colors.bgCard,
        child: Column(
          children: [
            // ── 1. 헤더 바 ──────────────────────────────────────────
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              color: context.colors.bgSurface,
              child: Row(
                children: [
                  const Icon(Icons.home_work_outlined, size: 20, color: Color(0xFF10B981)),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '${contractor.name} (${contract.displayUnit})',
                          style: AppTextStyles.titleSm.copyWith(
                            color: context.colors.textPrimary,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Text(
                          '주소 변경 이력 및 신규 주소 등록',
                          style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                        ),
                      ],
                    ),
                  ),
                  ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF10B981),
                      foregroundColor: Colors.white,
                      elevation: 0,
                      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                    ),
                    onPressed: () => _showAddAddressDialog(context, ref),
                    icon: const Icon(Icons.add_location_alt_outlined, size: 16),
                    label: const Text('주소 변경 등록', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                  ),
                ],
              ),
            ),
            Divider(color: context.colors.border, height: 1),

            // ── 2. 주소 이력 리스트 ────────────────────────────────
            Expanded(
              child: addressAsync.when(
                loading: () => const Center(
                  child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF10B981)),
                ),
                error: (err, _) => Center(
                  child: Text('주소 이력 로드 실패: $err', style: TextStyle(color: context.colors.error)),
                ),
                data: (addresses) {
                  if (addresses.isEmpty) {
                    return Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.location_off_outlined, size: 44, color: context.colors.textDisabled),
                          const SizedBox(height: 12),
                          Text(
                            '등록된 주소 정보가 없습니다.',
                            style: AppTextStyles.bodySecond.copyWith(color: context.colors.textMuted),
                          ),
                          const SizedBox(height: 8),
                          TextButton.icon(
                            onPressed: () => _showAddAddressDialog(context, ref),
                            icon: const Icon(Icons.add, size: 16, color: Color(0xFF10B981)),
                            label: const Text('주소 새로 등록하기', style: TextStyle(color: Color(0xFF10B981))),
                          ),
                        ],
                      ),
                    );
                  }

                  return ListView.separated(
                    padding: const EdgeInsets.all(16),
                    itemCount: addresses.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 12),
                    itemBuilder: (ctx, index) {
                      final item = addresses[index];
                      return _AddressHistoryCard(address: item);
                    },
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// 🗂️ 개별 주소 이력 카드 위젯
class _AddressHistoryCard extends StatelessWidget {
  final ContractorAddressModel address;

  const _AddressHistoryCard({required this.address});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: context.colors.bgSurface,
        borderRadius: BorderRadius.zero,
        border: Border.all(
          color: address.isCurrent ? const Color(0xFF10B981) : context.colors.border,
          width: address.isCurrent ? 1.4 : 0.8,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 상단 헤더 (현재 주소 여부 뱃지 & 등록일시)
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            color: address.isCurrent ? const Color(0xFF10B981).withAlpha(15) : context.colors.bgCard,
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: address.isCurrent ? const Color(0xFF10B981) : context.colors.textDisabled.withAlpha(50),
                    borderRadius: BorderRadius.zero,
                  ),
                  child: Text(
                    address.isCurrent ? '현재 적용 주소 (현주소)' : '이전 주소 (변경 이력)',
                    style: TextStyle(
                      fontSize: 10.5,
                      fontWeight: FontWeight.bold,
                      color: address.isCurrent ? Colors.white : context.colors.textMuted,
                    ),
                  ),
                ),
                const Spacer(),
                if (address.created != null)
                  Text(
                    '등록일: ${address.created!.split('T').first}',
                    style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 11),
                  ),
              ],
            ),
          ),
          Divider(color: context.colors.border, height: 1),

          // 주소 상세 본문
          Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 1. 주민등록 주소
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                      decoration: BoxDecoration(
                        border: Border.all(color: context.colors.textMuted.withAlpha(100), width: 0.6),
                      ),
                      child: Text('등본', style: TextStyle(fontSize: 10, color: context.colors.textMuted)),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        address.fullIdAddress,
                        style: AppTextStyles.bodySm.copyWith(
                          color: context.colors.textPrimary,
                          fontWeight: address.isCurrent ? FontWeight.w600 : FontWeight.normal,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),

                // 2. 우편 송부지 (DM) 주소
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                      decoration: BoxDecoration(
                        color: const Color(0xFF38BDF8).withAlpha(20),
                        border: Border.all(color: const Color(0xFF38BDF8), width: 0.6),
                      ),
                      child: const Text('우편',
                          style: TextStyle(fontSize: 10, color: Color(0xFF0284C7), fontWeight: FontWeight.bold)),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        address.fullDmAddress,
                        style: AppTextStyles.bodySm.copyWith(
                          color: context.colors.textSecond,
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// ➕ 신규 변경 주소 등록 다이얼로그
class _NewAddressDialog extends ConsumerStatefulWidget {
  final int contractorId;
  final String contractorName;
  final String unitStr;
  final VoidCallback onSuccess;

  const _NewAddressDialog({
    required this.contractorId,
    required this.contractorName,
    required this.unitStr,
    required this.onSuccess,
  });

  @override
  ConsumerState<_NewAddressDialog> createState() => _NewAddressDialogState();
}

class _NewAddressDialogState extends ConsumerState<_NewAddressDialog> {
  final _idZipController = TextEditingController();
  final _idAddr1Controller = TextEditingController();
  final _idAddr2Controller = TextEditingController();
  final _idAddr3Controller = TextEditingController();

  final _dmZipController = TextEditingController();
  final _dmAddr1Controller = TextEditingController();
  final _dmAddr2Controller = TextEditingController();
  final _dmAddr3Controller = TextEditingController();

  bool _isSameAsId = false;
  bool _isLoading = false;

  @override
  void dispose() {
    _idZipController.dispose();
    _idAddr1Controller.dispose();
    _idAddr2Controller.dispose();
    _idAddr3Controller.dispose();
    _dmZipController.dispose();
    _dmAddr1Controller.dispose();
    _dmAddr2Controller.dispose();
    _dmAddr3Controller.dispose();
    super.dispose();
  }

  void _syncDmAddressWithId() {
    if (_isSameAsId) {
      _dmZipController.text = _idZipController.text;
      _dmAddr1Controller.text = _idAddr1Controller.text;
      _dmAddr2Controller.text = _idAddr2Controller.text;
      _dmAddr3Controller.text = _idAddr3Controller.text;
    }
  }

  Future<void> _submit() async {
    if (_idZipController.text.trim().isEmpty || _idAddr1Controller.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('주민등록 우편번호와 기본주소를 입력하세요.'), behavior: SnackBarBehavior.floating),
      );
      return;
    }

    if (_isSameAsId) {
      _syncDmAddressWithId();
    }

    if (_dmZipController.text.trim().isEmpty || _dmAddr1Controller.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('우편송부지(DM) 우편번호와 기본주소를 입력하세요.'), behavior: SnackBarBehavior.floating),
      );
      return;
    }

    setState(() => _isLoading = true);

    final repository = ref.read(contractRepositoryProvider);

    final success = await repository.createAddress(
      contractorId: widget.contractorId,
      idZipcode: _idZipController.text,
      idAddress1: _idAddr1Controller.text,
      idAddress2: _idAddr2Controller.text,
      idAddress3: _idAddr3Controller.text,
      dmZipcode: _dmZipController.text,
      dmAddress1: _dmAddr1Controller.text,
      dmAddress2: _dmAddr2Controller.text,
      dmAddress3: _dmAddr3Controller.text,
    );

    // unmounted 상태에서 setState 호출 방지
    if (!mounted) return;
    setState(() => _isLoading = false);

    if (success) {
      widget.onSuccess();
      Navigator.pop(context);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('새로운 주소가 현주소로 등록되었으며, 기존 주소는 이력으로 보관됩니다.'),
          behavior: SnackBarBehavior.floating,
        ),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('주소 등록에 실패했습니다.'), behavior: SnackBarBehavior.floating),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      scrollable: true,
      backgroundColor: context.colors.bgCard,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.zero,
        side: BorderSide(color: context.colors.border, width: 0.8),
      ),
      titlePadding: const EdgeInsets.fromLTRB(16, 16, 16, 12),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16),
      actionsPadding: const EdgeInsets.all(12),
      title: Row(
        children: [
          const Icon(Icons.add_location_alt_outlined, size: 22, color: Color(0xFF10B981)),
          const SizedBox(width: 8),
          Text(
            '신규 주소 등록',
            style: AppTextStyles.titleSm.copyWith(
              color: context.colors.textPrimary,
              fontWeight: FontWeight.bold,
            ),
          ),
          const Spacer(),
          Text(
            '${widget.contractorName} (${widget.unitStr})',
            style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
          ),
        ],
      ),
      content: SizedBox(
        width: MediaQuery.of(context).size.width * 0.95,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Divider(color: context.colors.border, height: 1),
            const SizedBox(height: 10),

            // 안내 문구
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(8),
              color: const Color(0xFF10B981).withAlpha(15),
              child: Text(
                '💡 새 주소를 등록하면 기존 주소는 변경 이력으로 안전하게 보관되고 새 주소가 현주소로 지정됩니다.',
                style: TextStyle(fontSize: 11, color: context.colors.textPrimary, height: 1.3),
              ),
            ),
            const SizedBox(height: 14),

            // ── [1] 주민등록 주소 ──────────────────────────────
            Row(
              children: [
                const Icon(Icons.badge_outlined, size: 16, color: Color(0xFF10B981)),
                const SizedBox(width: 6),
                Text('주민등록 등본 주소', style: AppTextStyles.bodySm.copyWith(fontWeight: FontWeight.bold)),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                SizedBox(
                  width: 100,
                  child: TextField(
                    controller: _idZipController,
                    keyboardType: TextInputType.number,
                    style: const TextStyle(fontSize: 12.5),
                    decoration: const InputDecoration(
                      labelText: '우편번호',
                      hintText: '12345',
                      isDense: true,
                      border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                    ),
                    onChanged: (_) {
                      if (_isSameAsId) _syncDmAddressWithId();
                    },
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: TextField(
                    controller: _idAddr1Controller,
                    style: const TextStyle(fontSize: 12.5),
                    decoration: const InputDecoration(
                      labelText: '주민등록 기본주소',
                      hintText: '도로명 또는 지번 주소',
                      isDense: true,
                      border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                    ),
                    onChanged: (_) {
                      if (_isSameAsId) _syncDmAddressWithId();
                    },
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  flex: 6,
                  child: TextField(
                    controller: _idAddr2Controller,
                    style: const TextStyle(fontSize: 12.5),
                    decoration: const InputDecoration(
                      labelText: '상세주소',
                      hintText: '동·호수 등',
                      isDense: true,
                      border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                    ),
                    onChanged: (_) {
                      if (_isSameAsId) _syncDmAddressWithId();
                    },
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  flex: 4,
                  child: TextField(
                    controller: _idAddr3Controller,
                    style: const TextStyle(fontSize: 12.5),
                    decoration: const InputDecoration(
                      labelText: '참고항목',
                      hintText: '법정동/건물명',
                      isDense: true,
                      border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                    ),
                    onChanged: (_) {
                      if (_isSameAsId) _syncDmAddressWithId();
                    },
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // ── [2] 우편송부지 (DM) 주소 ──────────────────────────
            Row(
              children: [
                const Icon(Icons.mail_outline_rounded, size: 16, color: Color(0xFF38BDF8)),
                const SizedBox(width: 6),
                Text('우편 송부지 (DM) 주소', style: AppTextStyles.bodySm.copyWith(fontWeight: FontWeight.bold)),
                const Spacer(),
                InkWell(
                  onTap: () {
                    setState(() {
                      _isSameAsId = !_isSameAsId;
                      _syncDmAddressWithId();
                    });
                  },
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Checkbox(
                        value: _isSameAsId,
                        materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                        visualDensity: VisualDensity.compact,
                        onChanged: (val) {
                          setState(() {
                            _isSameAsId = val ?? false;
                            _syncDmAddressWithId();
                          });
                        },
                      ),
                      const Text('등본과 동일', style: TextStyle(fontSize: 11.5, color: Color(0xFF38BDF8))),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                SizedBox(
                  width: 100,
                  child: TextField(
                    controller: _dmZipController,
                    enabled: !_isSameAsId,
                    keyboardType: TextInputType.number,
                    style: const TextStyle(fontSize: 12.5),
                    decoration: const InputDecoration(
                      labelText: '우편번호',
                      hintText: '12345',
                      isDense: true,
                      border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: TextField(
                    controller: _dmAddr1Controller,
                    enabled: !_isSameAsId,
                    style: const TextStyle(fontSize: 12.5),
                    decoration: const InputDecoration(
                      labelText: '우편송부 기본주소',
                      hintText: '우편물 수령 도로명 주소',
                      isDense: true,
                      border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  flex: 6,
                  child: TextField(
                    controller: _dmAddr2Controller,
                    enabled: !_isSameAsId,
                    style: const TextStyle(fontSize: 12.5),
                    decoration: const InputDecoration(
                      labelText: '상세주소',
                      hintText: '동·호수 등',
                      isDense: true,
                      border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  flex: 4,
                  child: TextField(
                    controller: _dmAddr3Controller,
                    enabled: !_isSameAsId,
                    style: const TextStyle(fontSize: 12.5),
                    decoration: const InputDecoration(
                      labelText: '참고항목',
                      hintText: '법정동/건물명',
                      isDense: true,
                      border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: _isLoading ? null : () => Navigator.pop(context),
          child: Text('취소', style: TextStyle(color: context.colors.textMuted)),
        ),
        ElevatedButton(
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFF10B981),
            foregroundColor: Colors.white,
            shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
          ),
          onPressed: _isLoading ? null : _submit,
          child: _isLoading
              ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
              : const Text('변경 등록', style: TextStyle(fontWeight: FontWeight.bold)),
        ),
      ],
    );
  }
}
