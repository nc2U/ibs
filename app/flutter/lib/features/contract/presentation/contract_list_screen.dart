import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/providers/project_provider.dart';
import '../../../core/theme/app_colors_extension.dart';
import '../data/models/contract_models.dart';
import '../providers/contract_provider.dart';

/// 계약 관리 (Contract) 메인 화면
class ContractListScreen extends ConsumerStatefulWidget {
  final VoidCallback onBackToMain;

  const ContractListScreen({
    super.key,
    required this.onBackToMain,
  });

  @override
  ConsumerState<ContractListScreen> createState() => _ContractListScreenState();
}

class _ContractListScreenState extends ConsumerState<ContractListScreen> {
  final TextEditingController _searchController = TextEditingController();

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  void _onSearchChanged(String value) {
    ref.read(contractSearchQueryProvider.notifier).state = value;
  }

  void _onClearSearch() {
    _searchController.clear();
    ref.read(contractSearchQueryProvider.notifier).state = '';
  }

  Future<void> _makePhoneCall(String? phoneNumber) async {
    if (phoneNumber == null || phoneNumber.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('등록된 연락처가 없습니다.'),
          behavior: SnackBarBehavior.floating,
          duration: Duration(seconds: 2),
        ),
      );
      return;
    }
    final Uri launchUri = Uri(
      scheme: 'tel',
      path: phoneNumber.replaceAll(RegExp(r'[^0-9]'), ''),
    );
    if (await canLaunchUrl(launchUri)) {
      await launchUrl(launchUri);
    }
  }

  void _showActionBottomSheet(ContractItemModel contract) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.zero,
      ),
      backgroundColor: context.colors.bgCard,
      builder: (ctx) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 8),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                  child: Row(
                    children: [
                      Icon(Icons.assignment_outlined,
                          size: 18, color: context.colors.accentProject),
                      const SizedBox(width: 8),
                      Text(
                        '${contract.contractor?.name ?? '계약자'} (${contract.displayUnit})',
                        style: AppTextStyles.titleSm.copyWith(
                          color: context.colors.textPrimary,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 8),
                Divider(color: context.colors.border, height: 1),
                ListTile(
                  leading: const Icon(Icons.phone_outlined, size: 20, color: Color(0xFF0D9488)),
                  title: const Text('계약자 전화 연결', style: TextStyle(fontSize: 13.5)),
                  subtitle: Text(
                    contract.contractor?.contact?.cellPhone ?? '연락처 미등록',
                    style: TextStyle(fontSize: 11.5, color: context.colors.textMuted),
                  ),
                  onTap: () {
                    Navigator.pop(ctx);
                    _makePhoneCall(contract.contractor?.contact?.cellPhone);
                  },
                ),
                ListTile(
                  leading: const Icon(Icons.picture_as_pdf_outlined, size: 20, color: Color(0xFF38BDF8)),
                  title: const Text('분양대금 납부확인서 발급', style: TextStyle(fontSize: 13.5)),
                  subtitle: const Text('기납부 및 약정 내역 PDF 출력', style: TextStyle(fontSize: 11.5)),
                  onTap: () {
                    Navigator.pop(ctx);
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text('납부확인서 PDF 발급 기능 연동 중입니다.'),
                        behavior: SnackBarBehavior.floating,
                      ),
                    );
                  },
                ),
                ListTile(
                  leading: const Icon(Icons.edit_calendar_outlined, size: 20, color: Color(0xFFF59E0B)),
                  title: const Text('민원 및 상담 기록 등록', style: TextStyle(fontSize: 13.5)),
                  subtitle: const Text('계약자 상담일지 작성', style: TextStyle(fontSize: 11.5)),
                  onTap: () {
                    Navigator.pop(ctx);
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text('상담일지 작성 폼으로 이동합니다.'),
                        behavior: SnackBarBehavior.floating,
                      ),
                    );
                  },
                ),
                ListTile(
                  leading: const Icon(Icons.swap_horiz_rounded, size: 20, color: Color(0xFF8B5CF6)),
                  title: const Text('권리의무 승계 / 계약 해약 신청', style: TextStyle(fontSize: 13.5)),
                  subtitle: const Text('명의변경 및 계약종결 프로세스', style: TextStyle(fontSize: 11.5)),
                  onTap: () {
                    Navigator.pop(ctx);
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text('권리변동(승계/해약) 관리 메뉴입니다.'),
                        behavior: SnackBarBehavior.floating,
                      ),
                    );
                  },
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final selectedProject = ref.watch(selectedRealEstateProjectProvider);
    final aggregateAsync = ref.watch(contractAggregateProvider);
    final currentTab = ref.watch(contractCurrentSubTabProvider);

    final numFormat = NumberFormat('#,###');

    return Scaffold(
      backgroundColor: context.colors.bgPrimary,
      body: Column(
        children: [
          // ── 1. 계약 모듈 헤더 배너 ─────────────────────────────────────────
          Container(
            color: context.colors.bgSurface,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            child: Row(
              children: [
                Container(
                  width: 36,
                  height: 36,
                  decoration: BoxDecoration(
                    color: const Color(0xFF38BDF8).withAlpha(30),
                    borderRadius: BorderRadius.zero,
                  ),
                  child: const Icon(Icons.assignment_outlined,
                      size: 20, color: Color(0xFF38BDF8)),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Text(
                            '계약 정보 관리 (Contract)',
                            style: AppTextStyles.titleSm.copyWith(
                              color: context.colors.textPrimary,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 2),
                      Text(
                        selectedProject?.name ?? '부동산 개발 프로젝트',
                        style: AppTextStyles.caption.copyWith(
                          color: context.colors.textMuted,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ),
                ),
                IconButton(
                  onPressed: () {
                    ref.invalidate(contractAggregateProvider);
                    ref.invalidate(validContractListProvider);
                    ref.invalidate(successionListProvider);
                    ref.invalidate(contractorReleaseListProvider);
                  },
                  icon: const Icon(Icons.refresh_rounded, size: 18),
                  tooltip: '새로고침',
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(),
                  color: context.colors.textSecond,
                ),
              ],
            ),
          ),
          Divider(color: context.colors.border, height: 1),

          // ── 2. KPI 대시보드 (분양 현황 요약 카드) ───────────────────────────
          aggregateAsync.when(
            loading: () => const SizedBox(
              height: 72,
              child: Center(child: SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))),
            ),
            error: (_, __) => const SizedBox.shrink(),
            data: (aggregate) {
              return Container(
                color: context.colors.bgCard,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                child: Row(
                  children: [
                    _KpiItem(
                      label: '총 세대수',
                      value: '${numFormat.format(aggregate.totalUnits)}세대',
                      color: context.colors.textPrimary,
                    ),
                    _divider(),
                    _KpiItem(
                      label: '계약 완료',
                      value: '${numFormat.format(aggregate.contsNum)}세대',
                      color: const Color(0xFF38BDF8),
                    ),
                    _divider(),
                    _KpiItem(
                      label: '분양률',
                      value: '${aggregate.contractRate.toStringAsFixed(1)}%',
                      color: const Color(0xFF34D399),
                    ),
                    _divider(),
                    _KpiItem(
                      label: '청약(대기)',
                      value: '${numFormat.format(aggregate.subsNum)}건',
                      color: const Color(0xFFFBBF24),
                    ),
                  ],
                ),
              );
            },
          ),
          Divider(color: context.colors.border, height: 1),

          // ── 3. 3대 서브도메인 탭 (유효 계약 / 권리의무 승계 / 계약 해약) ────────
          Container(
            color: context.colors.bgSurface,
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
            child: Row(
              children: [
                _SubTabButton(
                  title: '유효 계약',
                  icon: Icons.assignment_outlined,
                  isSelected: currentTab == ContractSubTab.contracts,
                  onTap: () {
                    ref.read(contractCurrentSubTabProvider.notifier).state =
                        ContractSubTab.contracts;
                  },
                ),
                const SizedBox(width: 8),
                _SubTabButton(
                  title: '권리의무 승계',
                  icon: Icons.swap_horiz_rounded,
                  isSelected: currentTab == ContractSubTab.successions,
                  onTap: () {
                    ref.read(contractCurrentSubTabProvider.notifier).state =
                        ContractSubTab.successions;
                  },
                ),
                const SizedBox(width: 8),
                _SubTabButton(
                  title: '계약 해약',
                  icon: Icons.cancel_outlined,
                  isSelected: currentTab == ContractSubTab.releases,
                  onTap: () {
                    ref.read(contractCurrentSubTabProvider.notifier).state =
                        ContractSubTab.releases;
                  },
                ),
              ],
            ),
          ),
          Divider(color: context.colors.border, height: 1),

          // ── 4. 검색창 ──────────────────────────────────────────────────
          Container(
            color: context.colors.bgCard,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Container(
              height: 38,
              decoration: BoxDecoration(
                color: context.colors.bgSurface,
                borderRadius: BorderRadius.zero,
                border: Border.all(color: context.colors.border, width: 0.8),
              ),
              child: TextField(
                controller: _searchController,
                onChanged: _onSearchChanged,
                style: AppTextStyles.bodySecond.copyWith(
                  color: context.colors.textPrimary,
                  fontSize: 13,
                ),
                decoration: InputDecoration(
                  isDense: true,
                  hintText: currentTab == ContractSubTab.contracts
                      ? '계약자명, 동·호수, 연락처, 일련번호 검색...'
                      : (currentTab == ContractSubTab.successions
                          ? '양도인, 양수인, 일련번호 검색...'
                          : '해약 신청자명 검색...'),
                  hintStyle: AppTextStyles.bodySecond.copyWith(
                    color: context.colors.textMuted,
                    fontSize: 12.5,
                  ),
                  prefixIcon: Icon(
                    Icons.search_rounded,
                    size: 18,
                    color: context.colors.textMuted,
                  ),
                  suffixIcon: _searchController.text.isNotEmpty
                      ? IconButton(
                          icon: const Icon(Icons.clear_rounded, size: 16),
                          color: context.colors.textMuted,
                          onPressed: _onClearSearch,
                        )
                      : null,
                  border: InputBorder.none,
                  contentPadding: const EdgeInsets.symmetric(vertical: 9),
                ),
              ),
            ),
          ),
          Divider(color: context.colors.border, height: 1),

          // ── 5. 탭별 맞춤 리스트 ────────────────────────────────────────
          Expanded(
            child: Builder(
              builder: (context) {
                switch (currentTab) {
                  case ContractSubTab.contracts:
                    return _buildContractsView();
                  case ContractSubTab.successions:
                    return _buildSuccessionsView();
                  case ContractSubTab.releases:
                    return _buildReleasesView();
                }
              },
            ),
          ),
        ],
      ),
    );
  }

  /// 1. 유효 계약 목록 뷰
  Widget _buildContractsView() {
    final contractsAsync = ref.watch(validContractListProvider);

    return contractsAsync.when(
      loading: () => Center(
        child: CircularProgressIndicator(
          strokeWidth: 2,
          color: context.colors.accentProject,
        ),
      ),
      error: (err, _) => Center(
        child: Text('데이터 로드 실패: $err', style: TextStyle(color: context.colors.error)),
      ),
      data: (contracts) {
        if (contracts.isEmpty) {
          return Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.search_off_rounded, size: 40, color: context.colors.textDisabled),
                const SizedBox(height: 12),
                Text(
                  '일치하는 유효 계약 정보가 없습니다.',
                  style: AppTextStyles.bodySecond.copyWith(
                    color: context.colors.textMuted,
                  ),
                ),
              ],
            ),
          );
        }

        return ListView.separated(
          padding: const EdgeInsets.all(12),
          itemCount: contracts.length,
          separatorBuilder: (_, __) => const SizedBox(height: 10),
          itemBuilder: (ctx, index) {
            final item = contracts[index];
            return _ContractCard(
              contract: item,
              onMoreTap: () => _showActionBottomSheet(item),
              onCallTap: () => _makePhoneCall(item.contractor?.contact?.cellPhone),
            );
          },
        );
      },
    );
  }

  /// 2. 권리의무 승계 목록 뷰
  Widget _buildSuccessionsView() {
    final successionsAsync = ref.watch(successionListProvider);

    return successionsAsync.when(
      loading: () => Center(
        child: CircularProgressIndicator(
          strokeWidth: 2,
          color: context.colors.accentProject,
        ),
      ),
      error: (err, _) => Center(
        child: Text('승계 내역 로드 실패: $err', style: TextStyle(color: context.colors.error)),
      ),
      data: (successions) {
        if (successions.isEmpty) {
          return Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.swap_horiz_rounded, size: 40, color: context.colors.textDisabled),
                const SizedBox(height: 12),
                Text(
                  '등록된 권리의무 승계 내역이 없습니다.',
                  style: AppTextStyles.bodySecond.copyWith(
                    color: context.colors.textMuted,
                  ),
                ),
              ],
            ),
          );
        }

        return ListView.separated(
          padding: const EdgeInsets.all(12),
          itemCount: successions.length,
          separatorBuilder: (_, __) => const SizedBox(height: 10),
          itemBuilder: (ctx, index) {
            final item = successions[index];
            return _SuccessionCard(
              succession: item,
              onCallBuyer: () => _makePhoneCall(item.buyerCellPhone),
            );
          },
        );
      },
    );
  }

  /// 3. 계약 해약/해지 목록 뷰
  Widget _buildReleasesView() {
    final releasesAsync = ref.watch(contractorReleaseListProvider);

    return releasesAsync.when(
      loading: () => Center(
        child: CircularProgressIndicator(
          strokeWidth: 2,
          color: context.colors.accentProject,
        ),
      ),
      error: (err, _) => Center(
        child: Text('해약 내역 로드 실패: $err', style: TextStyle(color: context.colors.error)),
      ),
      data: (releases) {
        if (releases.isEmpty) {
          return Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.cancel_outlined, size: 40, color: context.colors.textDisabled),
                const SizedBox(height: 12),
                Text(
                  '등록된 계약 해약 내역이 없습니다.',
                  style: AppTextStyles.bodySecond.copyWith(
                    color: context.colors.textMuted,
                  ),
                ),
              ],
            ),
          );
        }

        return ListView.separated(
          padding: const EdgeInsets.all(12),
          itemCount: releases.length,
          separatorBuilder: (_, __) => const SizedBox(height: 10),
          itemBuilder: (ctx, index) {
            final item = releases[index];
            return _ReleaseCard(release: item);
          },
        );
      },
    );
  }

  Widget _divider() {
    return Container(
      width: 1,
      height: 24,
      color: context.colors.border,
      margin: const EdgeInsets.symmetric(horizontal: 4),
    );
  }
}

class _SubTabButton extends StatelessWidget {
  final String title;
  final IconData icon;
  final bool isSelected;
  final VoidCallback onTap;

  const _SubTabButton({
    required this.title,
    required this.icon,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Material(
        color: isSelected
            ? context.colors.accentProject.withAlpha(25)
            : context.colors.bgCard,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.zero,
          side: BorderSide(
            color: isSelected ? context.colors.accentProject : context.colors.border,
            width: isSelected ? 1 : 0.8,
          ),
        ),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.zero,
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  icon,
                  size: 14,
                  color: isSelected
                      ? context.colors.accentProject
                      : context.colors.textSecond,
                ),
                const SizedBox(width: 5),
                Text(
                  title,
                  style: AppTextStyles.caption.copyWith(
                    color: isSelected
                        ? context.colors.accentProject
                        : context.colors.textSecond,
                    fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _KpiItem extends StatelessWidget {
  final String label;
  final String value;
  final Color color;

  const _KpiItem({
    required this.label,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Text(
            label,
            style: AppTextStyles.caption.copyWith(
              color: context.colors.textMuted,
              fontSize: 10.5,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            value,
            style: AppTextStyles.titleSm.copyWith(
              color: color,
              fontSize: 13,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
}

/// 📋 유효 계약 카드
class _ContractCard extends StatelessWidget {
  final ContractItemModel contract;
  final VoidCallback onMoreTap;
  final VoidCallback onCallTap;

  const _ContractCard({
    required this.contract,
    required this.onMoreTap,
    required this.onCallTap,
  });

  @override
  Widget build(BuildContext context) {
    final numFormat = NumberFormat('#,###');
    final contractor = contract.contractor;

    return Container(
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.zero,
        border: Border.all(color: context.colors.border, width: 0.8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            color: context.colors.bgSurface,
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: (contract.unitTypeColor != null
                            ? Color(int.parse('0xFF${contract.unitTypeColor!.replaceAll('#', '')}'))
                            : const Color(0xFF38BDF8))
                        .withAlpha(25),
                    borderRadius: BorderRadius.zero,
                  ),
                  child: Text(
                    contract.unitTypeName ?? '타입',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      color: contract.unitTypeColor != null
                          ? Color(int.parse('0xFF${contract.unitTypeColor!.replaceAll('#', '')}'))
                          : const Color(0xFF38BDF8),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    contract.displayUnit,
                    style: AppTextStyles.titleSm.copyWith(
                      color: context.colors.textPrimary,
                      fontWeight: FontWeight.bold,
                      fontSize: 14,
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: const Color(0xFF34D399).withAlpha(20),
                    borderRadius: BorderRadius.zero,
                    border: Border.all(color: const Color(0xFF34D399).withAlpha(80), width: 0.6),
                  ),
                  child: const Text(
                    '계약유효',
                    style: TextStyle(
                      fontSize: 10.5,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF34D399),
                    ),
                  ),
                ),
              ],
            ),
          ),
          Divider(color: context.colors.border, height: 1),
          Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(
                      contractor?.name ?? '계약자 미등록',
                      style: AppTextStyles.titleSm.copyWith(
                        color: context.colors.textPrimary,
                        fontWeight: FontWeight.bold,
                        fontSize: 14.5,
                      ),
                    ),
                    const SizedBox(width: 8),
                    if (contract.serialNumber != null && contract.serialNumber!.isNotEmpty)
                      Text(
                        '[${contract.serialNumber}]',
                        style: AppTextStyles.caption.copyWith(
                          color: context.colors.textMuted,
                          fontSize: 11,
                        ),
                      ),
                    const Spacer(),
                    if (contractor?.contractDate != null)
                      Text(
                        '계약일: ${contractor!.contractDate}',
                        style: AppTextStyles.caption.copyWith(
                          color: context.colors.textMuted,
                          fontSize: 11,
                        ),
                      ),
                  ],
                ),
                const SizedBox(height: 10),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                  decoration: BoxDecoration(
                    color: context.colors.bgSurface,
                    borderRadius: BorderRadius.zero,
                  ),
                  child: Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('분양 공급가',
                                style: AppTextStyles.caption.copyWith(
                                    color: context.colors.textMuted, fontSize: 10.5)),
                            const SizedBox(height: 2),
                            Text(
                              contract.price > 0
                                  ? '${numFormat.format(contract.price)}원'
                                  : '동호지정 후 산정',
                              style: AppTextStyles.bodySecond.copyWith(
                                color: context.colors.textPrimary,
                                fontWeight: FontWeight.bold,
                                fontSize: 12.5,
                              ),
                            ),
                          ],
                        ),
                      ),
                      Container(width: 1, height: 20, color: context.colors.border),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '기납부액 (${contract.paymentRate.toStringAsFixed(0)}%)',
                              style: AppTextStyles.caption.copyWith(
                                  color: context.colors.textMuted, fontSize: 10.5),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              '${numFormat.format(contract.totalPaid)}원',
                              style: AppTextStyles.bodySecond.copyWith(
                                color: const Color(0xFF38BDF8),
                                fontWeight: FontWeight.bold,
                                fontSize: 12.5,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          Divider(color: context.colors.border, height: 1),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            child: Row(
              children: [
                TextButton.icon(
                  onPressed: onCallTap,
                  icon: const Icon(Icons.phone_outlined, size: 14, color: Color(0xFF0D9488)),
                  label: const Text('전화걸기', style: TextStyle(fontSize: 11.5, color: Color(0xFF0D9488))),
                  style: TextButton.styleFrom(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    minimumSize: Size.zero,
                    tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                  ),
                ),
                const SizedBox(width: 8),
                TextButton.icon(
                  onPressed: onMoreTap,
                  icon: Icon(Icons.description_outlined, size: 14, color: context.colors.textSecond),
                  label: Text('확인서/상담', style: TextStyle(fontSize: 11.5, color: context.colors.textSecond)),
                  style: TextButton.styleFrom(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    minimumSize: Size.zero,
                    tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                  ),
                ),
                const Spacer(),
                IconButton(
                  onPressed: onMoreTap,
                  icon: const Icon(Icons.more_horiz_rounded, size: 18),
                  color: context.colors.textMuted,
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(),
                  tooltip: '더보기',
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// 🔄 권리의무 승계 카드
class _SuccessionCard extends StatelessWidget {
  final SuccessionItemModel succession;
  final VoidCallback onCallBuyer;

  const _SuccessionCard({
    required this.succession,
    required this.onCallBuyer,
  });

  @override
  Widget build(BuildContext context) {
    Color statusColor;
    if (succession.status == '3') {
      statusColor = const Color(0xFF34D399); // 승계완료
    } else if (succession.status == '9') {
      statusColor = context.colors.error; // 취소
    } else {
      statusColor = const Color(0xFF8B5CF6); // 접수/대기
    }

    return Container(
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.zero,
        border: Border.all(color: context.colors.border, width: 0.8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            color: context.colors.bgSurface,
            child: Row(
              children: [
                Icon(Icons.swap_horiz_rounded, size: 16, color: context.colors.accentProject),
                const SizedBox(width: 8),
                Text(
                  '일련번호: ${succession.serialNumber ?? '-'}',
                  style: AppTextStyles.titleSm.copyWith(
                    color: context.colors.textPrimary,
                    fontWeight: FontWeight.bold,
                    fontSize: 13,
                  ),
                ),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: statusColor.withAlpha(20),
                    borderRadius: BorderRadius.zero,
                    border: Border.all(color: statusColor.withAlpha(80), width: 0.6),
                  ),
                  child: Text(
                    succession.statusDisplay,
                    style: TextStyle(
                      fontSize: 10.5,
                      fontWeight: FontWeight.bold,
                      color: statusColor,
                    ),
                  ),
                ),
              ],
            ),
          ),
          Divider(color: context.colors.border, height: 1),
          Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('양도인 (매도)',
                              style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 11)),
                          const SizedBox(height: 2),
                          Text(succession.sellerName,
                              style: AppTextStyles.titleSm.copyWith(
                                color: context.colors.textPrimary,
                                fontWeight: FontWeight.bold,
                                fontSize: 14,
                              )),
                        ],
                      ),
                    ),
                    const Icon(Icons.arrow_forward_rounded, size: 16, color: Color(0xFF8B5CF6)),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          Text('양수인 (매수)',
                              style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 11)),
                          const SizedBox(height: 2),
                          Text(succession.buyerName,
                              style: AppTextStyles.titleSm.copyWith(
                                color: const Color(0xFF38BDF8),
                                fontWeight: FontWeight.bold,
                                fontSize: 14,
                              )),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                Divider(color: context.colors.border, height: 1),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Text('신청일: ${succession.applyDate}',
                        style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 11.5)),
                    const Spacer(),
                    if (succession.approvalDate != null)
                      Text('승인일: ${succession.approvalDate}',
                          style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 11.5)),
                  ],
                ),
              ],
            ),
          ),
          if (succession.buyerCellPhone != null && succession.buyerCellPhone!.isNotEmpty) ...[
            Divider(color: context.colors.border, height: 1),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              child: Row(
                children: [
                  TextButton.icon(
                    onPressed: onCallBuyer,
                    icon: const Icon(Icons.phone_outlined, size: 14, color: Color(0xFF0D9488)),
                    label: Text('양수인 전화 (${succession.buyerCellPhone})',
                        style: const TextStyle(fontSize: 11.5, color: Color(0xFF0D9488))),
                    style: TextButton.styleFrom(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      minimumSize: Size.zero,
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}

/// 🚫 계약 해약 카드
class _ReleaseCard extends StatelessWidget {
  final ContractorReleaseItemModel release;

  const _ReleaseCard({required this.release});

  @override
  Widget build(BuildContext context) {
    final numFormat = NumberFormat('#,###');

    Color statusColor;
    if (release.status == '4') {
      statusColor = context.colors.error; // 해지확정
    } else if (release.status == '3') {
      statusColor = const Color(0xFF38BDF8); // 환불완료
    } else {
      statusColor = const Color(0xFFFBBF24); // 신청/정산
    }

    return Container(
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.zero,
        border: Border.all(color: context.colors.border, width: 0.8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            color: context.colors.bgSurface,
            child: Row(
              children: [
                Icon(Icons.cancel_outlined, size: 16, color: context.colors.error),
                const SizedBox(width: 8),
                Text(
                  release.contractorName,
                  style: AppTextStyles.titleSm.copyWith(
                    color: context.colors.textPrimary,
                    fontWeight: FontWeight.bold,
                    fontSize: 13.5,
                  ),
                ),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: statusColor.withAlpha(20),
                    borderRadius: BorderRadius.zero,
                    border: Border.all(color: statusColor.withAlpha(80), width: 0.6),
                  ),
                  child: Text(
                    release.statusDisplay,
                    style: TextStyle(
                      fontSize: 10.5,
                      fontWeight: FontWeight.bold,
                      color: statusColor,
                    ),
                  ),
                ),
              ],
            ),
          ),
          Divider(color: context.colors.border, height: 1),
          Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text('해약 신청일: ${release.requestDate}',
                        style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 11.5)),
                    const Spacer(),
                    if (release.completionDate != null)
                      Text('완결일: ${release.completionDate}',
                          style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 11.5)),
                  ],
                ),
                const SizedBox(height: 8),
                if (release.refundAmount != null)
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                    decoration: BoxDecoration(
                      color: context.colors.bgSurface,
                      borderRadius: BorderRadius.zero,
                    ),
                    child: Row(
                      children: [
                        Text('환불 정산액',
                            style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 11.5)),
                        const Spacer(),
                        Text('${numFormat.format(release.refundAmount)}원',
                            style: AppTextStyles.titleSm.copyWith(
                              color: const Color(0xFF38BDF8),
                              fontWeight: FontWeight.bold,
                              fontSize: 13,
                            )),
                      ],
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
