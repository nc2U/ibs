import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/providers/project_provider.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/models/payment_models.dart';
import '../../data/payment_repository.dart';
import '../../providers/payment_provider.dart';

/// 🔗 계약 & 회차 실시간 검색 및 매칭 바텀시트
class ContractMatchBottomSheet extends ConsumerStatefulWidget {
  final PaymentTransactionItemModel paymentItem;

  const ContractMatchBottomSheet({super.key, required this.paymentItem});

  @override
  ConsumerState<ContractMatchBottomSheet> createState() =>
      _ContractMatchBottomSheetState();
}

class _ContractMatchBottomSheetState
    extends ConsumerState<ContractMatchBottomSheet> {
  final TextEditingController _searchController = TextEditingController();
  Timer? _debounceTimer;
  int _searchRequestId = 0;
  bool _isSearching = false;
  bool _isSaving = false;
  bool _showContractSearch = false;
  List<Map<String, dynamic>> _searchResults = [];
  Map<String, dynamic>? _selectedContract;
  int? _selectedInstallmentOrderId;

  @override
  void initState() {
    super.initState();
    // 기존에 회차가 지정되어 있는 경우 초기값 세팅
    _selectedInstallmentOrderId = widget.paymentItem.installmentOrderId;

    // 계약이 아직 매칭되지 않은 경우에만 계약 검색을 기본 열어둠
    _showContractSearch = widget.paymentItem.contractId == null;

    if (_showContractSearch) {
      // 입금자명 또는 거래처가 있으면 초기 검색어 자동 입력 및 1회 자동 검색
      final initialQuery =
          widget.paymentItem.contractorName ?? widget.paymentItem.trader ?? '';
      if (initialQuery.isNotEmpty) {
        _searchController.text = initialQuery;
        WidgetsBinding.instance.addPostFrameCallback((_) {
          _performSearch(initialQuery);
        });
      }
    }
  }

  @override
  void dispose() {
    _debounceTimer?.cancel();
    _searchController.dispose();
    super.dispose();
  }

  void _onSearchChanged(String query) {
    _debounceTimer?.cancel();
    _debounceTimer = Timer(const Duration(milliseconds: 300), () {
      _performSearch(query);
    });
  }

  Future<void> _performSearch(String query) async {
    if (!mounted) return;
    final requestId = ++_searchRequestId;
    final selectedProject = ref.read(selectedRealEstateProjectProvider);
    if (selectedProject == null || query.trim().isEmpty) {
      setState(() {
        _searchResults = [];
        _isSearching = false;
      });
      return;
    }

    setState(() => _isSearching = true);

    List<Map<String, dynamic>> results = [];
    try {
      final repository = ref.read(paymentRepositoryProvider);
      results = await repository.searchContracts(
        projectId: selectedProject.realProjectId,
        query: query,
        limit: 20,
      );
    } catch (_) {
      results = [];
    }

    // 더 최신 검색 요청이 있거나 화면이 닫혔다면 결과를 버린다.
    if (!mounted || requestId != _searchRequestId) return;
    setState(() {
      _searchResults = results;
      _isSearching = false;
    });
  }

  Future<void> _submitMatch() async {
    if (_selectedContract == null && widget.paymentItem.contractId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('매칭할 계약 건을 선택해 주세요.'),
          behavior: SnackBarBehavior.floating,
        ),
      );
      return;
    }

    setState(() => _isSaving = true);

    final targetContractId = _selectedContract != null
        ? int.tryParse(
            (_selectedContract!['pk'] ?? _selectedContract!['id'])?.toString() ??
                '',
          )
        : widget.paymentItem.contractId;

    final success = await ref
        .read(paymentTransactionsProvider.notifier)
        .matchPayment(
          paymentPk: widget.paymentItem.pk,
          contractId: targetContractId,
          installmentOrderId: _selectedInstallmentOrderId,
          bankTransactionId: widget.paymentItem.bankTransactionId,
          accountingEntryId: widget.paymentItem.accountingEntryId,
        );

    if (mounted) {
      setState(() => _isSaving = false);
      if (success) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              _selectedContract != null
                  ? '[${_selectedContract!['contractor']?['name'] ?? '계약자'}] 계약 건과 매칭되었습니다.'
                  : '납부 회차가 성공적으로 변경되었습니다.',
            ),
            backgroundColor: context.colors.success,
            behavior: SnackBarBehavior.floating,
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Text('회차 변경 저장에 실패했습니다. 다시 시도해 주세요.'),
            backgroundColor: context.colors.error,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final numFormat = NumberFormat('#,###');
    final installmentOrdersAsync = ref.watch(installmentStatusListProvider);
    final isAlreadyContractMatched = widget.paymentItem.contractId != null;

    return Container(
      constraints: BoxConstraints(
        maxHeight: MediaQuery.of(context).size.height * 0.88,
      ),
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── 1. 모달 헤더 ─────────────────────────────────────────────
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            color: context.colors.bgSurface,
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(6),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0D9488).withAlpha(25),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Icon(
                    isAlreadyContractMatched
                        ? Icons.edit_calendar_outlined
                        : Icons.link_rounded,
                    size: 18,
                    color: const Color(0xFF0D9488),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        isAlreadyContractMatched
                            ? '납부 회차 변경 / 지정'
                            : '수납 건 - 계약 매칭',
                        style: AppTextStyles.titleSm.copyWith(
                          color: context.colors.textPrimary,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 1),
                      Text(
                        isAlreadyContractMatched
                            ? '해당 수납 건의 약정 납부 회차를 선택하여 변경합니다.'
                            : '입금 내역을 해당하는 유효 계약 및 납부 회차에 연결합니다.',
                        style: AppTextStyles.caption.copyWith(
                          color: context.colors.textMuted,
                          fontSize: 11,
                        ),
                      ),
                    ],
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.close, size: 20),
                  onPressed: () => Navigator.pop(context),
                  color: context.colors.textSecond,
                ),
              ],
            ),
          ),
          Divider(color: context.colors.border, height: 1),

          // ── 2. 매칭 대상 수납 건 요약 ─────────────────────────────────
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            color: context.colors.bgCard,
            child: Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: context.colors.bgSurface,
                borderRadius: BorderRadius.circular(6),
                border: Border.all(color: context.colors.border, width: 0.8),
              ),
              child: Column(
                children: [
                  Row(
                    children: [
                      Text(
                        '입금 거래 정보',
                        style: AppTextStyles.caption.copyWith(
                          color: context.colors.textMuted,
                          fontSize: 11,
                        ),
                      ),
                      const Spacer(),
                      Text(
                        '입금일: ${widget.paymentItem.dealDate}',
                        style: AppTextStyles.caption.copyWith(
                          color: context.colors.textMuted,
                          fontSize: 11,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              widget.paymentItem.contractorName ??
                                  (widget.paymentItem.trader ?? '입금자 미상'),
                              style: AppTextStyles.bodyMd.copyWith(
                                color: context.colors.textPrimary,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            if (widget.paymentItem.trader != null &&
                                widget.paymentItem.trader!.isNotEmpty) ...[
                              const SizedBox(height: 2),
                              Text(
                                '통장표시: ${widget.paymentItem.trader}',
                                style: AppTextStyles.caption.copyWith(
                                  color: context.colors.warning,
                                  fontSize: 11,
                                ),
                              ),
                            ],
                          ],
                        ),
                      ),
                      Text(
                        '${numFormat.format(widget.paymentItem.amount)}원',
                        style: AppTextStyles.titleSm.copyWith(
                          color: context.colors.success,
                          fontWeight: FontWeight.bold,
                          fontSize: 15,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          Divider(color: context.colors.border, height: 1),

          // ── 3. 본문 스크롤 영역 (실시간 계약 검색 & 회차 선택) ──────────
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // ── A. 계약 정보 표시 (이미 매칭된 경우) ──────────────────
                  if (isAlreadyContractMatched) ...[
                    Row(
                      children: [
                        Text(
                          '매칭된 계약 정보',
                          style: AppTextStyles.bodySecond.copyWith(
                            color: context.colors.textPrimary,
                            fontWeight: FontWeight.bold,
                            fontSize: 13,
                          ),
                        ),
                        const Spacer(),
                        InkWell(
                          onTap: () {
                            setState(() {
                              _showContractSearch = !_showContractSearch;
                            });
                          },
                          child: Text(
                            _showContractSearch ? '계약 변경 닫기 ▲' : '다른 계약으로 변경 ▼',
                            style: TextStyle(
                              fontSize: 11.5,
                              color: context.colors.info,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 8,
                      ),
                      decoration: BoxDecoration(
                        color: context.colors.success.withAlpha(15),
                        borderRadius: BorderRadius.circular(6),
                        border: Border.all(
                          color: context.colors.success.withAlpha(80),
                          width: 0.8,
                        ),
                      ),
                      child: Row(
                        children: [
                          Icon(
                            Icons.check_circle,
                            size: 16,
                            color: context.colors.success,
                          ),
                          const SizedBox(width: 8),
                          Text(
                            '${widget.paymentItem.contractorName ?? '계약자'} (${widget.paymentItem.unitStr})',
                            style: AppTextStyles.bodySecond.copyWith(
                              color: context.colors.textPrimary,
                              fontWeight: FontWeight.bold,
                              fontSize: 13,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 14),
                  ],

                  // ── B. 계약 검색 섹션 ──────────────────────────────────
                  if (_showContractSearch) ...[
                    Text(
                      '1. 계약 건 검색 및 선택',
                      style: AppTextStyles.bodySecond.copyWith(
                        color: context.colors.textPrimary,
                        fontWeight: FontWeight.bold,
                        fontSize: 13,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Container(
                      height: 38,
                      decoration: BoxDecoration(
                        color: context.colors.bgSurface,
                        borderRadius: BorderRadius.circular(6),
                        border: Border.all(
                          color: context.colors.border,
                          width: 0.8,
                        ),
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
                          hintText: '계약자명, 동·호수, 연락처, 일련번호 검색...',
                          hintStyle: AppTextStyles.bodySecond.copyWith(
                            color: context.colors.textMuted,
                            fontSize: 12,
                          ),
                          prefixIcon: const Icon(
                            Icons.search_rounded,
                            size: 18,
                          ),
                          suffixIcon: _isSearching
                              ? const Padding(
                                  padding: EdgeInsets.all(10),
                                  child: SizedBox(
                                    width: 14,
                                    height: 14,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                    ),
                                  ),
                                )
                              : (_searchController.text.isNotEmpty
                                    ? IconButton(
                                        icon: const Icon(Icons.clear, size: 16),
                                        onPressed: () {
                                          _searchController.clear();
                                          _performSearch('');
                                        },
                                      )
                                    : null),
                          border: InputBorder.none,
                          contentPadding: const EdgeInsets.symmetric(
                            vertical: 9,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 8),

                    // 검색 결과 목록
                    if (_searchResults.isNotEmpty) ...[
                      ListView.separated(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        itemCount: _searchResults.length,
                        separatorBuilder: (_, __) => const SizedBox(height: 6),
                        itemBuilder: (ctx, idx) {
                          final cont = _searchResults[idx];
                          final isSelected =
                              _selectedContract?['pk'] == cont['pk'] ||
                              _selectedContract?['id'] == cont['id'];
                          final contractor = cont['contractor'] is Map
                              ? cont['contractor']
                              : null;
                          final unitType = cont['unit_type'] is Map
                              ? cont['unit_type']
                              : null;
                          final keyUnit = cont['key_unit'] is Map
                              ? cont['key_unit']
                              : null;
                          final houseunit =
                              keyUnit != null && keyUnit['houseunit'] is Map
                              ? keyUnit['houseunit']
                              : null;

                          String unitDisplay =
                              cont['serial_number']?.toString() ?? '-';
                          if (houseunit != null) {
                            final name = houseunit['name']?.toString() ?? '';
                            final bldg =
                                houseunit['building_unit']?.toString() ?? '';
                            unitDisplay = bldg.isNotEmpty
                                ? '$bldg동 $name호'
                                : name;
                          }

                          final price = int.tryParse(
                            (cont['contractprice']?['price'] ??
                                    cont['price'] ??
                                    0)
                                .toString()
                                .split('.')
                                .first,
                          ) ?? 0;

                          return InkWell(
                            onTap: () {
                              setState(() {
                                _selectedContract = cont;
                              });
                            },
                            borderRadius: BorderRadius.circular(6),
                            child: Container(
                              padding: const EdgeInsets.all(10),
                              decoration: BoxDecoration(
                                color: isSelected
                                    ? context.colors.accentProject.withAlpha(20)
                                    : context.colors.bgSurface,
                                borderRadius: BorderRadius.circular(6),
                                border: Border.all(
                                  color: isSelected
                                      ? context.colors.accentProject
                                      : context.colors.border,
                                  width: isSelected ? 1.4 : 0.8,
                                ),
                              ),
                              child: Row(
                                children: [
                                  Icon(
                                    isSelected
                                        ? Icons.check_circle_rounded
                                        : Icons.radio_button_unchecked_rounded,
                                    size: 18,
                                    color: isSelected
                                        ? context.colors.accentProject
                                        : context.colors.textMuted,
                                  ),
                                  const SizedBox(width: 10),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        Row(
                                          children: [
                                            Text(
                                              contractor?['name']?.toString() ??
                                                  '계약자',
                                              style: AppTextStyles.bodySecond
                                                  .copyWith(
                                                    color: context
                                                        .colors
                                                        .textPrimary,
                                                    fontWeight: FontWeight.bold,
                                                    fontSize: 13.5,
                                                  ),
                                            ),
                                            const SizedBox(width: 6),
                                            Text(
                                              '($unitDisplay)',
                                              style: AppTextStyles.caption
                                                  .copyWith(
                                                    color: context
                                                        .colors
                                                        .textSecond,
                                                    fontSize: 12,
                                                  ),
                                            ),
                                            if (unitType != null) ...[
                                              const SizedBox(width: 6),
                                              Container(
                                                padding:
                                                    const EdgeInsets.symmetric(
                                                      horizontal: 5,
                                                      vertical: 1,
                                                    ),
                                                decoration: BoxDecoration(
                                                  color:
                                                      context.colors.bgPrimary,
                                                  borderRadius:
                                                      BorderRadius.circular(3),
                                                  border: Border.all(
                                                    color:
                                                        context.colors.border,
                                                    width: 0.6,
                                                  ),
                                                ),
                                                child: Text(
                                                  unitType['name']
                                                          ?.toString() ??
                                                      '',
                                                  style: TextStyle(
                                                    fontSize: 10,
                                                    color: context
                                                        .colors
                                                        .textSecond,
                                                  ),
                                                ),
                                              ),
                                            ],
                                          ],
                                        ),
                                        if (price > 0) ...[
                                          const SizedBox(height: 2),
                                          Text(
                                            '분양가: ${numFormat.format(price)}원',
                                            style: AppTextStyles.caption
                                                .copyWith(
                                                  color:
                                                      context.colors.textMuted,
                                                  fontSize: 11,
                                                ),
                                          ),
                                        ],
                                      ],
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),
                    ] else if (_searchController.text.isNotEmpty &&
                        !_isSearching) ...[
                      Container(
                        padding: const EdgeInsets.all(14),
                        alignment: Alignment.center,
                        child: Text(
                          '검색된 유효 계약 정보가 없습니다.',
                          style: AppTextStyles.caption.copyWith(
                            color: context.colors.textMuted,
                          ),
                        ),
                      ),
                    ],
                    const SizedBox(height: 18),
                    Divider(color: context.colors.border, height: 1),
                    const SizedBox(height: 14),
                  ],

                  // ── C. 납부 회차 선택 섹션 ────────────────────────────────
                  Row(
                    children: [
                      Text(
                        isAlreadyContractMatched && !_showContractSearch
                            ? '납부 회차 선택'
                            : '2. 납부 회차 지정',
                        style: AppTextStyles.bodySecond.copyWith(
                          color: context.colors.textPrimary,
                          fontWeight: FontWeight.bold,
                          fontSize: 13,
                        ),
                      ),
                      const Spacer(),
                      if (_selectedInstallmentOrderId != null)
                        InkWell(
                          onTap: () {
                            setState(() {
                              _selectedInstallmentOrderId = null;
                            });
                          },
                          child: Text(
                            '회차 미지정으로 변경',
                            style: TextStyle(
                              fontSize: 11,
                              color: context.colors.error,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                    ],
                  ),
                  const SizedBox(height: 8),

                  installmentOrdersAsync.when(
                    loading: () => const Center(
                      child: Padding(
                        padding: EdgeInsets.all(8),
                        child: SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        ),
                      ),
                    ),
                    error: (_, __) => Text(
                      '회차 정보를 불러오지 못했습니다.',
                      style: TextStyle(
                        color: context.colors.error,
                        fontSize: 12,
                      ),
                    ),
                    data: (orders) {
                      if (orders.isEmpty) {
                        return Padding(
                          padding: const EdgeInsets.all(8.0),
                          child: Text(
                            '등록된 납부 회차가 없습니다.',
                            style: AppTextStyles.caption.copyWith(
                              color: context.colors.textMuted,
                            ),
                          ),
                        );
                      }

                      return Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: orders.map((order) {
                          final isSelected =
                              _selectedInstallmentOrderId == order.orderId;
                          return ChoiceChip(
                            label: Text(
                              order.aliasName != null &&
                                      order.aliasName!.isNotEmpty
                                  ? '${order.payName} (${order.aliasName})'
                                  : order.payName,
                              style: TextStyle(
                                fontSize: 12,
                                fontWeight: isSelected
                                    ? FontWeight.bold
                                    : FontWeight.normal,
                                color: isSelected
                                    ? Colors.white
                                    : context.colors.textPrimary,
                              ),
                            ),
                            selected: isSelected,
                            selectedColor: const Color(0xFF0D9488),
                            backgroundColor: context.colors.bgSurface,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(6),
                            ),
                            side: BorderSide(
                              color: isSelected
                                  ? const Color(0xFF0D9488)
                                  : context.colors.border,
                              width: isSelected ? 1.2 : 0.8,
                            ),
                            onSelected: (selected) {
                              setState(() {
                                _selectedInstallmentOrderId = selected
                                    ? order.orderId
                                    : null;
                              });
                            },
                          );
                        }).toList(),
                      );
                    },
                  ),
                ],
              ),
            ),
          ),

          // ── 4. 하단 저장 버튼 ─────────────────────────────────────────
          Divider(color: context.colors.border, height: 1),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            color: context.colors.bgSurface,
            child: Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    style: OutlinedButton.styleFrom(
                      foregroundColor: context.colors.textMuted,
                      side: BorderSide(color: context.colors.border),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(6),
                      ),
                      padding: const EdgeInsets.symmetric(vertical: 11),
                    ),
                    onPressed: () => Navigator.pop(context),
                    child: const Text('취소'),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  flex: 2,
                  child: ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF0D9488),
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(6),
                      ),
                      padding: const EdgeInsets.symmetric(vertical: 11),
                    ),
                    onPressed: _isSaving ? null : _submitMatch,
                    icon: _isSaving
                        ? const SizedBox(
                            width: 14,
                            height: 14,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : const Icon(Icons.check_rounded, size: 18),
                    label: Text(
                      _isSaving ? '저장 중...' : '계약 매칭 완료',
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 13.5,
                      ),
                    ),
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
