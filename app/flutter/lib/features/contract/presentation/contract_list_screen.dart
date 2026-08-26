import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:open_filex/open_filex.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/providers/project_provider.dart';
import '../../../core/theme/app_colors_extension.dart';
import '../data/contract_repository.dart';
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
  final ScrollController _contractsScrollController = ScrollController();
  final ScrollController _successionsScrollController = ScrollController();
  final ScrollController _releasesScrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    _contractsScrollController.addListener(_onContractsScroll);
    _successionsScrollController.addListener(_onSuccessionsScroll);
    _releasesScrollController.addListener(_onReleasesScroll);
  }

  @override
  void dispose() {
    _searchController.dispose();
    _contractsScrollController.dispose();
    _successionsScrollController.dispose();
    _releasesScrollController.dispose();
    super.dispose();
  }

  void _onContractsScroll() {
    if (_contractsScrollController.position.pixels >=
        _contractsScrollController.position.maxScrollExtent - 200) {
      ref.read(validContractListProvider.notifier).fetchNextPage();
    }
  }

  void _onSuccessionsScroll() {
    if (_successionsScrollController.position.pixels >=
        _successionsScrollController.position.maxScrollExtent - 200) {
      ref.read(successionListProvider.notifier).fetchNextPage();
    }
  }

  void _onReleasesScroll() {
    if (_releasesScrollController.position.pixels >=
        _releasesScrollController.position.maxScrollExtent - 200) {
      ref.read(contractorReleaseListProvider.notifier).fetchNextPage();
    }
  }

  void _onSearchChanged(String value) {
    ref.read(contractSearchQueryProvider.notifier).state = value;
    ref.read(validContractListProvider.notifier).fetchInitial();
    ref.read(successionListProvider.notifier).fetchInitial();
    ref.read(contractorReleaseListProvider.notifier).fetchInitial();
  }

  void _onClearSearch() {
    _searchController.clear();
    ref.read(contractSearchQueryProvider.notifier).state = '';
    ref.read(validContractListProvider.notifier).fetchInitial();
    ref.read(successionListProvider.notifier).fetchInitial();
    ref.read(contractorReleaseListProvider.notifier).fetchInitial();
  }

  Future<void> _makePhoneCall(String? phoneNumber, {String? contractorName, String? unitStr}) async {
    if (phoneNumber == null || phoneNumber.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('등록된 연락처가 없습니다.'),
          behavior: SnackBarBehavior.floating,
          duration: Duration(seconds: 2),
        ),
      );
      return;
    }

    final cleanNumber = phoneNumber.replaceAll(RegExp(r'[^0-9]'), '');

    // ── 2단계 확인 다이얼로그 (오발신 및 개인정보 노출 안내) ──
    final bool? shouldCall = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: context.colors.bgCard,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.zero,
          side: BorderSide(color: context.colors.border, width: 0.8),
        ),
        title: Row(
          children: [
            const Icon(Icons.phone_in_talk_outlined, size: 20, color: Color(0xFF0D9488)),
            const SizedBox(width: 8),
            Text(
              '계약자 전화 연결',
              style: AppTextStyles.titleSm.copyWith(
                color: context.colors.textPrimary,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '${contractorName ?? '계약자'}${unitStr != null ? ' ($unitStr)' : ''}',
              style: AppTextStyles.bodyMd.copyWith(
                color: context.colors.textPrimary,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              phoneNumber,
              style: AppTextStyles.titleMd.copyWith(
                color: const Color(0xFF0D9488),
                fontWeight: FontWeight.bold,
                letterSpacing: 0.5,
              ),
            ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(8),
              color: context.colors.bgSurface,
              child: Row(
                children: [
                  Icon(Icons.info_outline, size: 14, color: context.colors.textMuted),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      '개인 모바일 발신 번호가 상대방에게 표시됩니다.',
                      style: AppTextStyles.caption.copyWith(
                        color: context.colors.textMuted,
                        fontSize: 11,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: Text('취소', style: TextStyle(color: context.colors.textMuted)),
          ),
          ElevatedButton.icon(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF0D9488),
              foregroundColor: Colors.white,
              shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            ),
            onPressed: () => Navigator.pop(ctx, true),
            icon: const Icon(Icons.phone, size: 16),
            label: const Text('통화 연결', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );

    if (shouldCall == true) {
      final Uri launchUri = Uri(scheme: 'tel', path: cleanNumber);
      if (await canLaunchUrl(launchUri)) {
        await launchUrl(launchUri);
      }
    }
  }

  void _copyToClipboard(String text, String label) {
    Clipboard.setData(ClipboardData(text: text));
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('$label ($text) 복사되었습니다.'),
        behavior: SnackBarBehavior.floating,
        duration: const Duration(seconds: 2),
      ),
    );
  }

  Future<void> _downloadAndSharePaymentCertPdf(ContractItemModel contract) async {
    final contractorName = contract.contractor?.name ?? '계약자';
    final unitStr = contract.displayUnit;

    BuildContext? progressDialogContext;

    // 로딩 인디케이터 표시
    showDialog(
      context: context,
      barrierDismissible: false,
      barrierColor: Colors.black45,
      useRootNavigator: true,
      builder: (ctx) {
        progressDialogContext = ctx;
        return Center(
          child: Material(
            color: Colors.transparent,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
              decoration: BoxDecoration(
                color: context.colors.bgCard,
                borderRadius: BorderRadius.circular(4),
                border: Border.all(color: context.colors.border, width: 0.8),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withAlpha(50),
                    blurRadius: 16,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const SizedBox(
                    width: 22,
                    height: 22,
                    child: CircularProgressIndicator(
                      strokeWidth: 2.5,
                      color: Color(0xFF38BDF8),
                    ),
                  ),
                  const SizedBox(width: 16),
                  Text(
                    '납부확인서 PDF 생성 중...',
                    style: AppTextStyles.bodyMd.copyWith(
                      color: context.colors.textPrimary,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );

    try {
      final repository = ref.read(contractRepositoryProvider);
      final pdfBytes = await repository.downloadPaymentCertPdf(
        contractId: contract.pk,
      );

      // 로딩 닫기 (안전한 dialog context 사용)
      if (progressDialogContext != null && progressDialogContext!.mounted) {
        Navigator.of(progressDialogContext!).pop();
        progressDialogContext = null;
      }

      if (pdfBytes == null || pdfBytes.isEmpty) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('납부확인서 PDF를 생성할 수 없습니다. (데이터 확인 필요)'),
              behavior: SnackBarBehavior.floating,
            ),
          );
        }
        return;
      }

      // 임시 디렉토리에 파일 저장
      final tempDir = await getTemporaryDirectory();
      final nowStr = DateFormat('yyyyMMdd_HHmmss').format(DateTime.now());
      final cleanUnitStr = unitStr.replaceAll(RegExp(r'[^a-zA-Z0-9가-힣]'), '_');
      final fileName = '납부확인서_${contractorName}_${cleanUnitStr}_$nowStr.pdf';
      final file = File('${tempDir.path}/$fileName');
      await file.writeAsBytes(pdfBytes);

      if (!mounted) return;

      // 액션 선택 다이얼로그 (바로 열람 vs 공유)
      showModalBottomSheet(
        context: context,
        backgroundColor: context.colors.bgCard,
        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
        builder: (dialogCtx) => SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.picture_as_pdf, size: 22, color: Color(0xFF38BDF8)),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        '납부확인서 PDF 준비 완료',
                        style: AppTextStyles.titleSm.copyWith(
                          color: context.colors.textPrimary,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                Text(
                  fileName,
                  style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                ),
                const SizedBox(height: 12),
                Divider(color: context.colors.border, height: 1),
                ListTile(
                  leading: const Icon(Icons.visibility_outlined, color: Color(0xFF38BDF8)),
                  title: const Text('PDF 바로 열기 (뷰어 확인)'),
                  subtitle: const Text('화면에서 기납부 내역 직접 확인', style: TextStyle(fontSize: 11.5)),
                  onTap: () async {
                    Navigator.pop(dialogCtx);
                    await OpenFilex.open(file.path);
                  },
                ),
                ListTile(
                  leading: const Icon(Icons.share_outlined, color: Color(0xFF34D399)),
                  title: const Text('모바일 전송 / 공유 (카카오톡, 문자, 메일)'),
                  subtitle: const Text('계약자 또는 대출기관에 파일 직접 전송', style: TextStyle(fontSize: 11.5)),
                  onTap: () async {
                    Navigator.pop(dialogCtx);
                    // ignore: deprecated_member_use
                    await Share.shareXFiles(
                      [XFile(file.path, mimeType: 'application/pdf')],
                      text: '$contractorName님 ($unitStr) 분양대금 납부확인서입니다.',
                      subject: '분양대금 납부확인서 - $contractorName',
                    );
                  },
                ),
              ],
            ),
          ),
        ),
      );
    } catch (e) {
      if (progressDialogContext != null && progressDialogContext!.mounted) {
        Navigator.of(progressDialogContext!).pop();
        progressDialogContext = null;
      }
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('납부확인서 발급 중 오류가 발생했습니다: $e'),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }

  void _showActionBottomSheet(ContractItemModel contract) {
    final cellPhone = contract.contractor?.contact?.cellPhone;
    final contractorName = contract.contractor?.name ?? '계약자';

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.zero,
      ),
      backgroundColor: context.colors.bgCard,
      builder: (ctx) {
        return SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
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
                        '$contractorName (${contract.displayUnit})',
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
                    cellPhone ?? '연락처 미등록',
                    style: TextStyle(fontSize: 11.5, color: context.colors.textMuted),
                  ),
                  trailing: cellPhone != null && cellPhone.isNotEmpty
                      ? IconButton(
                          icon: const Icon(Icons.copy_rounded, size: 16),
                          tooltip: '전화번호 복사',
                          color: context.colors.textMuted,
                          onPressed: () {
                            Navigator.pop(ctx);
                            _copyToClipboard(cellPhone, '$contractorName 연락처');
                          },
                        )
                      : null,
                  onTap: () {
                    Navigator.pop(ctx);
                    _makePhoneCall(
                      cellPhone,
                      contractorName: contractorName,
                      unitStr: contract.displayUnit,
                    );
                  },
                ),
                ListTile(
                  leading: const Icon(Icons.picture_as_pdf_outlined, size: 20, color: Color(0xFF38BDF8)),
                  title: const Text('분양대금 납부확인서 발급', style: TextStyle(fontSize: 13.5)),
                  subtitle: const Text('기납부 및 약정 내역 PDF 출력·공유', style: TextStyle(fontSize: 11.5)),
                  onTap: () {
                    Navigator.pop(ctx);
                    _downloadAndSharePaymentCertPdf(contract);
                  },
                ),
                ListTile(
                  leading: const Icon(Icons.edit_calendar_outlined, size: 20, color: Color(0xFFF59E0B)),
                  title: const Text('민원 및 상담 이력 / 기록 등록', style: TextStyle(fontSize: 13.5)),
                  subtitle: const Text('과거 상담 이력 조회 및 신규 상담일지 작성', style: TextStyle(fontSize: 11.5)),
                  onTap: () {
                    Navigator.pop(ctx);
                    showModalBottomSheet(
                      context: context,
                      isScrollControlled: true,
                      backgroundColor: Colors.transparent,
                      builder: (consultationCtx) => ContractorConsultationBottomSheet(contract: contract),
                    );
                  },
                ),
                ListTile(
                  leading: const Icon(Icons.home_work_outlined, size: 20, color: Color(0xFF10B981)),
                  title: const Text('주소 변경 이력 / 신규 등록', style: TextStyle(fontSize: 13.5)),
                  subtitle: const Text('주민등록 및 우편물 수령지 변경 내역 관리', style: TextStyle(fontSize: 11.5)),
                  onTap: () {
                    Navigator.pop(ctx);
                    showModalBottomSheet(
                      context: context,
                      isScrollControlled: true,
                      backgroundColor: Colors.transparent,
                      builder: (addressCtx) => ContractorAddressBottomSheet(contract: contract),
                    );
                  },
                ),
                ListTile(
                  leading: const Icon(Icons.swap_horiz_rounded, size: 20, color: Color(0xFF8B5CF6)),
                  title: const Text('권리의무 승계 (명의변경) 내역 / 관리', style: TextStyle(fontSize: 13.5)),
                  subtitle: const Text('양도·양수 승계 심사 및 변경인가 프로세스', style: TextStyle(fontSize: 11.5)),
                  onTap: () {
                    Navigator.pop(ctx);
                    // 1. 검색창에 계약자명 자동 주입
                    _searchController.text = contractorName;
                    ref.read(contractSearchQueryProvider.notifier).state = contractorName;
                    // 2. 권리의무 승계 탭으로 전환
                    ref.read(contractCurrentSubTabProvider.notifier).state = ContractSubTab.successions;
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text('[$contractorName] 계약자의 권리의무 승계 탭으로 이동했습니다.'),
                        behavior: SnackBarBehavior.floating,
                        duration: const Duration(seconds: 2),
                      ),
                    );
                  },
                ),
                ListTile(
                  leading: const Icon(Icons.cancel_outlined, size: 20, color: Color(0xFFEF4444)),
                  title: const Text('계약 해약·해지 신청 / 정산 내역', style: TextStyle(fontSize: 13.5)),
                  subtitle: const Text('계약종결, 환불 정산금 및 계좌 관리', style: TextStyle(fontSize: 11.5)),
                  onTap: () {
                    Navigator.pop(ctx);
                    // 1. 검색창에 계약자명 자동 주입
                    _searchController.text = contractorName;
                    ref.read(contractSearchQueryProvider.notifier).state = contractorName;
                    // 2. 계약 해약 탭으로 전환
                    ref.read(contractCurrentSubTabProvider.notifier).state = ContractSubTab.releases;
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text('[$contractorName] 계약자의 계약 해약 탭으로 이동했습니다.'),
                        behavior: SnackBarBehavior.floating,
                        duration: const Duration(seconds: 2),
                      ),
                    );
                  },
                ),
                const SizedBox(height: 12),
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
                    ref.read(validContractListProvider.notifier).fetchInitial();
                    ref.read(successionListProvider.notifier).fetchInitial();
                    ref.read(contractorReleaseListProvider.notifier).fetchInitial();
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
    final state = ref.watch(validContractListProvider);

    if (state.isLoading) {
      return Center(
        child: CircularProgressIndicator(
          strokeWidth: 2,
          color: context.colors.accentProject,
        ),
      );
    }

    if (state.error != null && state.items.isEmpty) {
      return Center(
        child: Text('데이터 로드 실패: ${state.error}', style: TextStyle(color: context.colors.error)),
      );
    }

    if (state.items.isEmpty) {
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

    final itemCount = state.items.length + (state.isFetchingNextPage ? 1 : 0);

    return ListView.separated(
      controller: _contractsScrollController,
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      itemCount: itemCount,
      separatorBuilder: (_, __) => const SizedBox(height: 12),
      itemBuilder: (ctx, index) {
        if (index == state.items.length) {
          return const Padding(
            padding: EdgeInsets.symmetric(vertical: 14),
            child: Center(
              child: SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(strokeWidth: 2),
              ),
            ),
          );
        }

        final item = state.items[index];
        return _ContractCard(
          contract: item,
          onMoreTap: () => _showActionBottomSheet(item),
        );
      },
    );
  }

  /// 2. 권리의무 승계 목록 뷰
  Widget _buildSuccessionsView() {
    final state = ref.watch(successionListProvider);

    if (state.isLoading) {
      return Center(
        child: CircularProgressIndicator(
          strokeWidth: 2,
          color: context.colors.accentProject,
        ),
      );
    }

    if (state.error != null && state.items.isEmpty) {
      return Center(
        child: Text('승계 내역 로드 실패: ${state.error}', style: TextStyle(color: context.colors.error)),
      );
    }

    if (state.items.isEmpty) {
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

    final itemCount = state.items.length + (state.isFetchingNextPage ? 1 : 0);

    return ListView.separated(
      controller: _successionsScrollController,
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      itemCount: itemCount,
      separatorBuilder: (_, __) => const SizedBox(height: 12),
      itemBuilder: (ctx, index) {
        if (index == state.items.length) {
          return const Padding(
            padding: EdgeInsets.symmetric(vertical: 14),
            child: Center(
              child: SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(strokeWidth: 2),
              ),
            ),
          );
        }

        final item = state.items[index];
        return _SuccessionCard(
          succession: item,
          onCallBuyer: () => _makePhoneCall(item.buyerCellPhone),
        );
      },
    );
  }

  /// 3. 계약 해약/해지 목록 뷰
  Widget _buildReleasesView() {
    final state = ref.watch(contractorReleaseListProvider);

    if (state.isLoading) {
      return Center(
        child: CircularProgressIndicator(
          strokeWidth: 2,
          color: context.colors.accentProject,
        ),
      );
    }

    if (state.error != null && state.items.isEmpty) {
      return Center(
        child: Text('해약 내역 로드 실패: ${state.error}', style: TextStyle(color: context.colors.error)),
      );
    }

    if (state.items.isEmpty) {
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

    final itemCount = state.items.length + (state.isFetchingNextPage ? 1 : 0);

    return ListView.separated(
      controller: _releasesScrollController,
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      itemCount: itemCount,
      separatorBuilder: (_, __) => const SizedBox(height: 12),
      itemBuilder: (ctx, index) {
        if (index == state.items.length) {
          return const Padding(
            padding: EdgeInsets.symmetric(vertical: 14),
            child: Center(
              child: SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(strokeWidth: 2),
              ),
            ),
          );
        }

        final item = state.items[index];
        return _ReleaseCard(release: item);
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

  const _ContractCard({
    required this.contract,
    required this.onMoreTap,
  });

  @override
  Widget build(BuildContext context) {
    final numFormat = NumberFormat('#,###');
    final contractor = contract.contractor;

    return Container(
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.zero,
        border: Border.all(
          color: context.colors.textDisabled.withAlpha(180),
          width: 1.2,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withAlpha(12),
            offset: const Offset(0, 2),
            blurRadius: 4,
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onMoreTap,
          splashColor: context.colors.accentProject.withAlpha(20),
          highlightColor: context.colors.accentProject.withAlpha(10),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // ── 카드 상단 헤더 (동호수 & 타입 뱃지 & 계약상태 & 더보기 아이콘) ──
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                color: context.colors.bgSurface,
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2.5),
                      decoration: BoxDecoration(
                        color: contract.parsedTypeColor,
                        borderRadius: BorderRadius.circular(2),
                        border: Border.all(
                          color: contract.typeBorderColor,
                          width: 0.8,
                        ),
                      ),
                      child: Text(
                        contract.unitTypeName ?? '타입',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          color: contract.typeTextColor,
                          letterSpacing: 0.2,
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
                    const SizedBox(width: 4),
                    Icon(
                      Icons.more_vert_rounded,
                      size: 18,
                      color: context.colors.textMuted,
                    ),
                  ],
                ),
              ),
              Divider(color: context.colors.border, height: 1),

              // ── 카드 본문 (계약자명, 시리얼, 계약일, 분양가/납부액) ──
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
            ],
          ),
        ),
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
        border: Border.all(
          color: context.colors.textDisabled.withAlpha(180),
          width: 1.2,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withAlpha(12),
            offset: const Offset(0, 2),
            blurRadius: 4,
          ),
        ],
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
        border: Border.all(
          color: context.colors.textDisabled.withAlpha(180),
          width: 1.2,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withAlpha(12),
            offset: const Offset(0, 2),
            blurRadius: 4,
          ),
        ],
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

/// 📝 계약자 민원 및 상담 이력 시트
class ContractorConsultationBottomSheet extends ConsumerWidget {
  final ContractItemModel contract;

  const ContractorConsultationBottomSheet({super.key, required this.contract});

  void _showAddConsultationDialog(BuildContext context, WidgetRef ref) {
    final contractor = contract.contractor;
    if (contractor == null) return;

    showDialog(
      context: context,
      builder: (ctx) => _NewConsultationDialog(
        contractorId: contractor.pk,
        contractorName: contractor.name,
        unitStr: contract.displayUnit,
        onSuccess: () {
          ref.invalidate(contractorConsultationLogsProvider(contractor.pk));
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final contractor = contract.contractor;
    if (contractor == null) {
      return const SizedBox(
        height: 200,
        child: Center(child: Text('계약자 정보가 없습니다.')),
      );
    }

    final logsAsync = ref.watch(contractorConsultationLogsProvider(contractor.pk));

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
                  const Icon(Icons.edit_calendar_outlined, size: 20, color: Color(0xFFF59E0B)),
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
                          '민원 및 상담 이력 관리',
                          style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                        ),
                      ],
                    ),
                  ),
                  ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFFF59E0B),
                      foregroundColor: Colors.white,
                      elevation: 0,
                      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                    ),
                    onPressed: () => _showAddConsultationDialog(context, ref),
                    icon: const Icon(Icons.add, size: 16),
                    label: const Text('상담 등록', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                  ),
                ],
              ),
            ),
            Divider(color: context.colors.border, height: 1),

            // ── 2. 상담 이력 타임라인 리스트 ───────────────────────
            Expanded(
              child: logsAsync.when(
                loading: () => const Center(
                  child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFFF59E0B)),
                ),
                error: (err, _) => Center(
                  child: Text('상담 이력 로드 실패: $err', style: TextStyle(color: context.colors.error)),
                ),
                data: (logs) {
                  if (logs.isEmpty) {
                    return Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.speaker_notes_off_outlined, size: 44, color: context.colors.textDisabled),
                          const SizedBox(height: 12),
                          Text(
                            '등록된 상담/민원 이력이 없습니다.',
                            style: AppTextStyles.bodySecond.copyWith(color: context.colors.textMuted),
                          ),
                          const SizedBox(height: 8),
                          TextButton.icon(
                            onPressed: () => _showAddConsultationDialog(context, ref),
                            icon: const Icon(Icons.add, size: 16, color: Color(0xFFF59E0B)),
                            label: const Text('첫 상담 기록 작성하기', style: TextStyle(color: Color(0xFFF59E0B))),
                          ),
                        ],
                      ),
                    );
                  }

                  return ListView.separated(
                    padding: const EdgeInsets.all(16),
                    itemCount: logs.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 12),
                    itemBuilder: (ctx, index) {
                      final item = logs[index];
                      return _ConsultationLogCard(log: item);
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

/// 🗂️ 개별 상담 이력 카드 위젯
class _ConsultationLogCard extends StatelessWidget {
  final ContractorConsultationLogModel log;

  const _ConsultationLogCard({required this.log});

  Color _getChannelColor(String channel) {
    switch (channel) {
      case 'phone':
        return const Color(0xFF0D9488);
      case 'visit':
        return const Color(0xFF38BDF8);
      case 'kakao':
        return const Color(0xFFFACC15);
      case 'sms':
        return const Color(0xFF8B5CF6);
      default:
        return const Color(0xFF94A3B8);
    }
  }

  @override
  Widget build(BuildContext context) {
    final channelColor = _getChannelColor(log.channel);

    return Container(
      decoration: BoxDecoration(
        color: context.colors.bgSurface,
        borderRadius: BorderRadius.zero,
        border: Border.all(
          color: log.isImportant ? const Color(0xFFF59E0B) : context.colors.border,
          width: log.isImportant ? 1.2 : 0.8,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 카드 상단 헤더
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            color: context.colors.bgCard,
            child: Row(
              children: [
                // 채널 뱃지
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: channelColor.withAlpha(25),
                    borderRadius: BorderRadius.zero,
                    border: Border.all(color: channelColor.withAlpha(120), width: 0.6),
                  ),
                  child: Text(
                    log.channelKorean,
                    style: TextStyle(
                      fontSize: 10.5,
                      fontWeight: FontWeight.bold,
                      color: channelColor,
                    ),
                  ),
                ),
                const SizedBox(width: 6),
                // 카테고리 뱃지
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: context.colors.accentProject.withAlpha(20),
                    borderRadius: BorderRadius.zero,
                  ),
                  child: Text(
                    log.categoryKorean,
                    style: TextStyle(
                      fontSize: 10.5,
                      fontWeight: FontWeight.bold,
                      color: context.colors.accentProject,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Text(
                  log.consultationDate,
                  style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                ),
                const Spacer(),
                if (log.consultantName != null)
                  Text(
                    '상담: ${log.consultantName}',
                    style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 11),
                  ),
              ],
            ),
          ),
          Divider(color: context.colors.border, height: 1),

          // 카드 본문
          Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (log.title.isNotEmpty) ...[
                  Text(
                    log.title,
                    style: AppTextStyles.titleSm.copyWith(
                      color: context.colors.textPrimary,
                      fontWeight: FontWeight.bold,
                      fontSize: 13.5,
                    ),
                  ),
                  const SizedBox(height: 6),
                ],
                Text(
                  log.content.isNotEmpty ? log.content : '(상세 내용 없음)',
                  style: AppTextStyles.bodySm.copyWith(
                    color: context.colors.textSecond,
                    height: 1.4,
                  ),
                ),
                if (log.followUpRequired && log.followUpNote != null && log.followUpNote!.isNotEmpty) ...[
                  const SizedBox(height: 10),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(8),
                    color: const Color(0xFFF59E0B).withAlpha(15),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Icon(Icons.assignment_late_outlined, size: 14, color: Color(0xFFF59E0B)),
                        const SizedBox(width: 6),
                        Expanded(
                          child: Text(
                            '후속조치: ${log.followUpNote}',
                            style: AppTextStyles.caption.copyWith(
                              color: const Color(0xFFB45309),
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// ➕ 신규 민원/상담 기록 등록 다이얼로그
class _NewConsultationDialog extends ConsumerStatefulWidget {
  final int contractorId;
  final String contractorName;
  final String unitStr;
  final VoidCallback onSuccess;

  const _NewConsultationDialog({
    required this.contractorId,
    required this.contractorName,
    required this.unitStr,
    required this.onSuccess,
  });

  @override
  ConsumerState<_NewConsultationDialog> createState() => _NewConsultationDialogState();
}

class _NewConsultationDialogState extends ConsumerState<_NewConsultationDialog> {
  final _titleController = TextEditingController();
  final _contentController = TextEditingController();
  final _followUpController = TextEditingController();

  DateTime _selectedDate = DateTime.now();
  String _channel = 'phone';
  String _category = 'payment';
  String _priority = 'normal';
  bool _followUpRequired = false;
  bool _isImportant = false;
  bool _isLoading = false;

  @override
  void dispose() {
    _titleController.dispose();
    _contentController.dispose();
    _followUpController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_contentController.text.trim().isEmpty && _titleController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('상담 제목 또는 내용을 입력하세요.'), behavior: SnackBarBehavior.floating),
      );
      return;
    }

    setState(() => _isLoading = true);

    final repository = ref.read(contractRepositoryProvider);
    final dateStr = DateFormat('yyyy-MM-dd').format(_selectedDate);

    final success = await repository.createConsultationLog(
      contractorId: widget.contractorId,
      consultationDate: dateStr,
      channel: _channel,
      category: _category,
      title: _titleController.text.trim(),
      content: _contentController.text.trim(),
      priority: _priority,
      followUpRequired: _followUpRequired,
      followUpNote: _followUpController.text.trim(),
      isImportant: _isImportant,
    );

    setState(() => _isLoading = false);

    if (mounted) {
      if (success) {
        widget.onSuccess();
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('상담 기록이 성공적으로 등록되었습니다.'), behavior: SnackBarBehavior.floating),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('상담 기록 등록에 실패했습니다.'), behavior: SnackBarBehavior.floating),
        );
      }
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
          const Icon(Icons.edit_note_rounded, size: 22, color: Color(0xFFF59E0B)),
          const SizedBox(width: 8),
          Text(
            '상담일지 작성',
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
        width: MediaQuery.of(context).size.width * 0.9,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Divider(color: context.colors.border, height: 1),
              const SizedBox(height: 12),

              // 1. 상담채널 & 상담유형
              Row(
                children: [
                  Expanded(
                    child: DropdownButtonFormField<String>(
                      initialValue: _channel,
                      decoration: const InputDecoration(
                        labelText: '상담채널',
                        isDense: true,
                        border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                      ),
                      items: const [
                        DropdownMenuItem(value: 'phone', child: Text('전화')),
                        DropdownMenuItem(value: 'visit', child: Text('방문')),
                        DropdownMenuItem(value: 'kakao', child: Text('카카오톡')),
                        DropdownMenuItem(value: 'sms', child: Text('문자')),
                        DropdownMenuItem(value: 'email', child: Text('이메일')),
                        DropdownMenuItem(value: 'other', child: Text('기타')),
                      ],
                      onChanged: (val) => setState(() => _channel = val ?? 'phone'),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: DropdownButtonFormField<String>(
                      initialValue: _category,
                      decoration: const InputDecoration(
                        labelText: '상담유형',
                        isDense: true,
                        border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                      ),
                      items: const [
                        DropdownMenuItem(value: 'payment', child: Text('납부상담')),
                        DropdownMenuItem(value: 'contract', child: Text('계약상담')),
                        DropdownMenuItem(value: 'complaint', child: Text('민원/불만')),
                        DropdownMenuItem(value: 'succession', child: Text('승계상담')),
                        DropdownMenuItem(value: 'release', child: Text('해지상담')),
                        DropdownMenuItem(value: 'change', child: Text('변경상담')),
                        DropdownMenuItem(value: 'document', child: Text('서류관련')),
                        DropdownMenuItem(value: 'question', child: Text('단순문의')),
                        DropdownMenuItem(value: 'etc', child: Text('기타')),
                      ],
                      onChanged: (val) => setState(() => _category = val ?? 'payment'),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),

              // 2. 제목
              TextField(
                controller: _titleController,
                style: const TextStyle(fontSize: 13),
                decoration: const InputDecoration(
                  labelText: '상담 제목 (요약)',
                  hintText: '예: 2차 중도금 납부 일정 및 연체 문의',
                  isDense: true,
                  border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                ),
              ),
              const SizedBox(height: 12),

              // 3. 내용
              TextField(
                controller: _contentController,
                maxLines: 4,
                style: const TextStyle(fontSize: 13),
                decoration: const InputDecoration(
                  labelText: '상세 상담 및 통화 내용',
                  hintText: '계약자와의 통화/면담 세부 내용을 입력하세요.',
                  isDense: true,
                  border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                ),
              ),
              const SizedBox(height: 10),

              // 4. 후속조치 및 중요도 체크
              Row(
                children: [
                  Expanded(
                    child: CheckboxListTile(
                      contentPadding: EdgeInsets.zero,
                      controlAffinity: ListTileControlAffinity.leading,
                      dense: true,
                      title: const Text('후속 조치 필요', style: TextStyle(fontSize: 12)),
                      value: _followUpRequired,
                      onChanged: (val) => setState(() => _followUpRequired = val ?? false),
                    ),
                  ),
                  Expanded(
                    child: CheckboxListTile(
                      contentPadding: EdgeInsets.zero,
                      controlAffinity: ListTileControlAffinity.leading,
                      dense: true,
                      title: const Text('중요 민원 표시', style: TextStyle(fontSize: 12, color: Color(0xFFF59E0B))),
                      value: _isImportant,
                      onChanged: (val) => setState(() => _isImportant = val ?? false),
                    ),
                  ),
                ],
              ),
              if (_followUpRequired)
                Padding(
                  padding: const EdgeInsets.only(top: 6),
                  child: TextField(
                    controller: _followUpController,
                    style: const TextStyle(fontSize: 12.5),
                    decoration: const InputDecoration(
                      labelText: '후속조치 메모',
                      hintText: '예: 08/28 수납 확인 후 유선 회신 예정',
                      isDense: true,
                      border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: _isLoading ? null : () => Navigator.pop(context),
          child: Text('취소', style: TextStyle(color: context.colors.textMuted)),
        ),
        ElevatedButton(
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFFF59E0B),
            foregroundColor: Colors.white,
            shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
          ),
          onPressed: _isLoading ? null : _submit,
          child: _isLoading
              ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
              : const Text('등록 완료', style: TextStyle(fontWeight: FontWeight.bold)),
        ),
      ],
    );
  }
}

/// 🏠 계약자 주소 변경 이력 및 신규 등록 시트
class ContractorAddressBottomSheet extends ConsumerWidget {
  final ContractItemModel contract;

  const ContractorAddressBottomSheet({super.key, required this.contract});

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
      return const SizedBox(
        height: 200,
        child: Center(child: Text('계약자 정보가 없습니다.')),
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
                      child: const Text('우편', style: TextStyle(fontSize: 10, color: Color(0xFF0284C7), fontWeight: FontWeight.bold)),
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

    setState(() => _isLoading = false);

    if (mounted) {
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
