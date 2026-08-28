import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/providers/project_provider.dart';
import '../../../core/theme/app_colors_extension.dart';
import '../data/models/project_model.dart';
import '../data/project_repository.dart';
import '../providers/project_provider.dart';

/// ⚙️ 프로젝트 설정 화면
class ProjectSettingsScreen extends ConsumerStatefulWidget {
  final VoidCallback onBackToMain;

  const ProjectSettingsScreen({
    super.key,
    required this.onBackToMain,
  });

  @override
  ConsumerState<ProjectSettingsScreen> createState() => _ProjectSettingsScreenState();
}

class _ProjectSettingsScreenState extends ConsumerState<ProjectSettingsScreen> {
  void _showEditBasicInfoModal(RealEstateProjectDetailModel project) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => _EditProjectBasicInfoSheet(
        project: project,
        onSuccess: () {
          ref.invalidate(realEstateProjectDetailProvider);
          ref.invalidate(realEstateProjectsProvider);
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final selectedProject = ref.watch(selectedRealEstateProjectProvider);
    final detailAsync = ref.watch(realEstateProjectDetailProvider);

    return Column(
      children: [
        // ── 1. 프로젝트 설정 모듈 헤더 배너 ──────────────────────────────────
        Container(
          color: context.colors.bgSurface,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          child: Row(
            children: [
              Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                  color: const Color(0xFF00796B).withAlpha(30),
                  borderRadius: BorderRadius.zero,
                ),
                child: const Icon(Icons.settings_outlined,
                    size: 20, color: Color(0xFF00796B)),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text('프로젝트 설정',
                            style: AppTextStyles.titleSm.copyWith(
                              color: context.colors.textPrimary,
                              fontWeight: FontWeight.bold,
                            )),
                        const SizedBox(width: 6),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
                          decoration: BoxDecoration(
                            color: const Color(0xFF00796B).withAlpha(20),
                            border: Border.all(color: const Color(0xFF00796B).withAlpha(120), width: 0.8),
                            borderRadius: BorderRadius.circular(2),
                          ),
                          child: const Text(
                            'SETTINGS',
                            style: TextStyle(
                              fontSize: 9.5,
                              fontWeight: FontWeight.bold,
                              color: Color(0xFF00796B),
                              letterSpacing: 0.6,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 2),
                    Text(
                      selectedProject?.name ?? '부동산 개발 프로젝트',
                      style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
              IconButton(
                onPressed: () => ref.invalidate(realEstateProjectDetailProvider),
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

        // ── 2. 설정 본문 스크롤 영역 ─────────────────────────────────────────
        Expanded(
          child: detailAsync.when(
            loading: () => const Center(
              child: SizedBox(width: 24, height: 24, child: CircularProgressIndicator(strokeWidth: 2)),
            ),
            error: (e, _) => Center(
              child: Text('설정 정보를 불러오지 못했습니다: $e',
                  style: TextStyle(color: context.colors.error, fontSize: 13)),
            ),
            data: (detail) {
              if (detail == null) {
                return const Center(child: Text('선택된 프로젝트 정보가 없습니다.'));
              }

              return ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  // ── [SECTION 1] 프로젝트 개요 및 기본 정보 (상세 카드) ────────────
                  _buildSectionHeader(
                    context: context,
                    title: '프로젝트 개요 및 기본 정보',
                    icon: Icons.info_outline_rounded,
                    accentColor: const Color(0xFF00796B),
                    action: ElevatedButton.icon(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF00796B),
                        foregroundColor: Colors.white,
                        elevation: 0,
                        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                      ),
                      onPressed: () => _showEditBasicInfoModal(detail),
                      icon: const Icon(Icons.edit, size: 14),
                      label: const Text('기본정보 수정', style: TextStyle(fontSize: 11.5, fontWeight: FontWeight.bold)),
                    ),
                  ),
                  const SizedBox(height: 8),
                  _buildBasicInfoCard(context, detail),
                  const SizedBox(height: 22),

                  // ── [SECTION 2] 1. 차수 및 타입, 층별조건 설정 현황 ──────────────
                  _buildSectionHeader(
                    context: context,
                    title: '1. 차수 및 타입, 층별조건',
                    icon: Icons.layers_outlined,
                    accentColor: const Color(0xFF1565C0),
                    action: _buildWebBadge(context),
                  ),
                  const SizedBox(height: 8),
                  _buildOrderTypeFloorCard(context, detail),
                  const SizedBox(height: 20),

                  // ── [SECTION 3] 2. 유닛 정보 설정 (동/호수) ───────────────────
                  _buildSectionHeader(
                    context: context,
                    title: '2. 유닛 정보 설정 (동/호수)',
                    icon: Icons.domain_outlined,
                    accentColor: const Color(0xFF2E7D32),
                    action: _buildWebBadge(context),
                  ),
                  const SizedBox(height: 8),
                  _buildUnitConfigCard(context, detail),
                  const SizedBox(height: 20),

                  // ── [SECTION 4] 3. 예산 정보 설정 (수입/지출) ───────────────────
                  _buildSectionHeader(
                    context: context,
                    title: '3. 예산 정보 설정 (수입/지출)',
                    icon: Icons.account_balance_wallet_outlined,
                    accentColor: const Color(0xFFE65100),
                    action: _buildWebBadge(context),
                  ),
                  const SizedBox(height: 8),
                  _buildBudgetConfigCard(context),
                  const SizedBox(height: 20),

                  // ── [SECTION 5] 4. 분양 조건 설정 (납부회차/계약금/공급가격) ────
                  _buildSectionHeader(
                    context: context,
                    title: '4. 분양 조건 설정 (납부회차/계약금/공급가격)',
                    icon: Icons.payments_outlined,
                    accentColor: const Color(0xFF7C3AED),
                    action: _buildWebBadge(context),
                  ),
                  const SizedBox(height: 8),
                  _buildSalesConditionCard(context, detail),
                  const SizedBox(height: 24),
                ],
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _buildSectionHeader({
    required BuildContext context,
    required String title,
    required IconData icon,
    required Color accentColor,
    required Widget action,
  }) {
    return Row(
      children: [
        Container(
          width: 24,
          height: 24,
          decoration: BoxDecoration(
            color: accentColor.withAlpha(25),
            borderRadius: BorderRadius.zero,
          ),
          child: Icon(icon, size: 14, color: accentColor),
        ),
        const SizedBox(width: 8),
        Text(
          title,
          style: AppTextStyles.titleSm.copyWith(
            color: context.colors.textPrimary,
            fontWeight: FontWeight.bold,
            fontSize: 13.5,
          ),
        ),
        const Spacer(),
        action,
      ],
    );
  }

  Widget _buildWebBadge(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: context.colors.bgSurface,
        border: Border.all(color: context.colors.border, width: 0.8),
      ),
      child: Text(
        '웹 관리',
        style: TextStyle(fontSize: 10, color: context.colors.textMuted, fontWeight: FontWeight.bold),
      ),
    );
  }

  Widget _buildBasicInfoCard(BuildContext context, RealEstateProjectDetailModel detail) {
    final numFormat = NumberFormat('#,###.#');

    return Container(
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        border: Border.all(color: context.colors.border, width: 0.8),
      ),
      child: Column(
        children: [
          // 카드 상단 헤더: 프로젝트명 & 종류
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            color: context.colors.bgSurface,
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    detail.name,
                    style: AppTextStyles.titleSm.copyWith(
                      color: context.colors.textPrimary,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: const Color(0xFF00796B).withAlpha(20),
                    border: Border.all(color: const Color(0xFF00796B).withAlpha(90), width: 0.6),
                  ),
                  child: Text(
                    detail.kindDesc ?? '공동주택',
                    style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Color(0xFF00796B)),
                  ),
                ),
              ],
            ),
          ),
          Divider(color: context.colors.border, height: 1),

          // 세부 속성 그리드 목록
          Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              children: [
                _buildInfoRow('대지 위치(소재지)', detail.location.isNotEmpty ? detail.location : '미등록', context),
                _buildInfoRow('용도지역/지구', detail.areaUsage.isNotEmpty ? detail.areaUsage : '미등록', context),
                _buildInfoRow('건축 규모', detail.buildSize.isNotEmpty ? detail.buildSize : '미등록', context),
                _buildInfoRow(
                  '사업 형태 및 운영',
                  '${detail.isDirectManage ? "본사 직영" : "시행/업무대행"} · ${detail.isReturnedArea ? "환지 방식" : "일반 수용"} · ${detail.isUnitSet ? "동호지정 완료" : "동호 미지정"}',
                  context,
                ),
                Divider(color: context.colors.border, height: 16),

                // 면적 및 규모 지표
                Row(
                  children: [
                    Expanded(
                      child: _buildMetricTile(
                        '총 세대수',
                        detail.numUnit != null ? '${numFormat.format(detail.numUnit)}세대' : '-',
                        const Color(0xFF00796B),
                        context,
                      ),
                    ),
                    Expanded(
                      child: _buildMetricTile(
                        '대지면적',
                        detail.schemeLandExtent != null ? '${numFormat.format(detail.schemeLandExtent)}㎡' : '-',
                        context.colors.textPrimary,
                        context,
                      ),
                    ),
                    Expanded(
                      child: _buildMetricTile(
                        '총 연면적',
                        detail.totalFloorArea != null ? '${numFormat.format(detail.totalFloorArea)}㎡' : '-',
                        context.colors.textPrimary,
                        context,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    Expanded(
                      child: _buildMetricTile(
                        '건폐율 / 용적률',
                        '${detail.buildToLandRatio ?? "-"}% / ${detail.floorAreaRatio ?? "-"}%',
                        context.colors.textSecond,
                        context,
                      ),
                    ),
                    Expanded(
                      child: _buildMetricTile(
                        '계획 주차대수',
                        detail.numPlanedParking != null ? '${detail.numPlanedParking}대' : '-',
                        context.colors.textSecond,
                        context,
                      ),
                    ),
                    Expanded(
                      child: _buildMetricTile(
                        '공사 기간(개월)',
                        '${detail.constructionPeriodMonths}개월',
                        context.colors.textSecond,
                        context,
                      ),
                    ),
                  ],
                ),
                Divider(color: context.colors.border, height: 16),

                // 일정 정보
                _buildInfoRow('월별 집계 시작일', detail.monthlyAggrStartDate.isNotEmpty ? detail.monthlyAggrStartDate : '-', context),
                _buildInfoRow('착공 예정/시작일', detail.constructionStartDate.isNotEmpty ? detail.constructionStartDate : '-', context),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMetricTile(String label, String value, Color valueColor, BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 4),
      decoration: BoxDecoration(
        color: context.colors.bgSurface,
        border: Border.all(color: context.colors.border, width: 0.6),
      ),
      child: Column(
        children: [
          Text(label, style: TextStyle(fontSize: 10, color: context.colors.textMuted)),
          const SizedBox(height: 2),
          Text(
            value,
            style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: valueColor),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
    );
  }

  Widget _buildInfoRow(String label, String value, BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3.5),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 110,
            child: Text(
              label,
              style: TextStyle(fontSize: 11.5, color: context.colors.textMuted),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: TextStyle(fontSize: 12, fontWeight: FontWeight.w500, color: context.colors.textPrimary),
            ),
          ),
        ],
      ),
    );
  }

  // ── [1. 차수 및 타입, 층별조건 설정 현황 카드] ──────────────────────────
  Widget _buildOrderTypeFloorCard(BuildContext context, RealEstateProjectDetailModel detail) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        border: Border.all(color: context.colors.border, width: 0.8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.layers_outlined, size: 16, color: Color(0xFF1565C0)),
              const SizedBox(width: 6),
              Text(
                '차수 그룹 및 전용/공급 타입, 층별 군(단가) 관리',
                style: AppTextStyles.bodySecond.copyWith(
                  fontSize: 13,
                  fontWeight: FontWeight.bold,
                  color: const Color(0xFF1565C0),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            '• 사업 차수 분할(1차 조합원 / 2차 일반분양 등)\n'
            '• 전용면적/공급면적/계약면적별 평형 타입(A/B/C/D) 신설\n'
            '• 저층/중층/로얄층/탑층 등 층별 조건 그룹 및 분양 단가 기준 설정\n\n'
            '💡 PC 웹 IBS 콘솔에서 대량 차수/타입 마스터 테이블을 일괄 등록하고 층별 단가표를 설정할 수 있습니다.',
            style: TextStyle(fontSize: 11.5, color: context.colors.textSecond, height: 1.45),
          ),
        ],
      ),
    );
  }

  // ── [2. 유닛 정보 설정 (동/호수) 카드] ────────────────────────────────────
  Widget _buildUnitConfigCard(BuildContext context, RealEstateProjectDetailModel detail) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        border: Border.all(color: context.colors.border, width: 0.8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.domain_outlined, size: 16, color: Color(0xFF2E7D32)),
              const SizedBox(width: 6),
              Text(
                '동/호수 배치 매트릭스 및 개별 유닛 속성',
                style: AppTextStyles.bodySecond.copyWith(
                  fontSize: 13,
                  fontWeight: FontWeight.bold,
                  color: const Color(0xFF2E7D32),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            '• 총 세대수 규모: ${detail.numUnit != null ? "${detail.numUnit}세대" : "미등록"}\n'
            '• 동/층/라인 매트릭스 생성 및 개별 호수(Unit) 일괄 생성\n'
            '• 호수별 타입 매핑, 전용/공급면적, 층별 특화조건 및 분양 보류지 지정\n\n'
            '💡 동·호수 일괄 생성 및 엑셀 업로드는 웹 관리자 환경에서 스프레드시트 뷰로 최적화되어 제공됩니다.',
            style: TextStyle(fontSize: 11.5, color: context.colors.textSecond, height: 1.45),
          ),
        ],
      ),
    );
  }

  // ── [3. 예산 정보 설정 (수입/지출) 카드] ──────────────────────────────────
  Widget _buildBudgetConfigCard(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        border: Border.all(color: context.colors.border, width: 0.8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.account_balance_wallet_outlined, size: 16, color: Color(0xFFE65100)),
              const SizedBox(width: 6),
              Text(
                '수입/지출 예산안 수립 및 회계 계정과목 매핑',
                style: AppTextStyles.bodySecond.copyWith(
                  fontSize: 13,
                  fontWeight: FontWeight.bold,
                  color: const Color(0xFFE65100),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            '• 수입 예산: 분양 수입금, 대출 차입금, 기타 잡수입 목표액 편성\n'
            '• 지출 예산: 토지매입비, 건축공사비, 금융비용, 판매관리비 등 세부 편성\n'
            '• 세부 회계 계정과목(대분류-중분류-소분류)과 사업비 항목 간 1:1 매핑\n\n'
            '💡 정밀한 예산안 승인 및 회계 계정 과목 매핑은 PC 웹 환경에서 종합 대시보드로 관리됩니다.',
            style: TextStyle(fontSize: 11.5, color: context.colors.textSecond, height: 1.45),
          ),
        ],
      ),
    );
  }

  // ── [4. 분양 조건 설정 (납부회차/계약금/공급가격) 카드] ───────────────────────
  Widget _buildSalesConditionCard(BuildContext context, RealEstateProjectDetailModel detail) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        border: Border.all(color: context.colors.border, width: 0.8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.payments_outlined, size: 16, color: Color(0xFF7C3AED)),
              const SizedBox(width: 6),
              Text(
                '약정 분할 단계, 계약금 비율 및 분양 공급가격표',
                style: AppTextStyles.bodySecond.copyWith(
                  fontSize: 13,
                  fontWeight: FontWeight.bold,
                  color: const Color(0xFF7C3AED),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            '• 납부 회차 정의: 계약금(1차/2차), 중도금(1~6차), 잔금 분할 기준\n'
            '• 회차별 납부 비율(10% - 60% - 30%) 및 납부 기한일 지정\n'
            '• 타입/층별 분양 공급금액(대지가격, 건축가격, 부가세) 확정 단가표 연동\n'
            '• 대표 수납 수탁 계좌 매핑 및 수납 할인/연체 이율 정책 지정\n\n'
            '💡 세부 분양가격표 매트릭스 및 수납 회차 자동 생성은 PC 웹 관리자에서 총괄 설정됩니다.',
            style: TextStyle(fontSize: 11.5, color: context.colors.textSecond, height: 1.45),
          ),
        ],
      ),
    );
  }
}

/// ✏️ 프로젝트 기본 정보 간편 수정 바텀시트
class _EditProjectBasicInfoSheet extends ConsumerStatefulWidget {
  final RealEstateProjectDetailModel project;
  final VoidCallback onSuccess;

  const _EditProjectBasicInfoSheet({
    required this.project,
    required this.onSuccess,
  });

  @override
  ConsumerState<_EditProjectBasicInfoSheet> createState() => _EditProjectBasicInfoSheetState();
}

class _EditProjectBasicInfoSheetState extends ConsumerState<_EditProjectBasicInfoSheet> {
  late TextEditingController _nameController;
  late TextEditingController _locationController;
  late TextEditingController _areaUsageController;
  late TextEditingController _buildSizeController;
  late TextEditingController _numUnitController;
  late TextEditingController _schemeLandController;
  late TextEditingController _totalFloorController;
  late TextEditingController _constructionPeriodController;

  late String _kind;
  late String _monthlyAggrDate;
  late String _constructionStartDate;
  late bool _isDirectManage;
  late bool _isReturnedArea;
  late bool _isUnitSet;

  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    final p = widget.project;
    _nameController = TextEditingController(text: p.name);
    _locationController = TextEditingController(text: p.location);
    _areaUsageController = TextEditingController(text: p.areaUsage);
    _buildSizeController = TextEditingController(text: p.buildSize);
    _numUnitController = TextEditingController(text: p.numUnit?.toString() ?? '');
    _schemeLandController = TextEditingController(text: p.schemeLandExtent?.toString() ?? '');
    _totalFloorController = TextEditingController(text: p.totalFloorArea?.toString() ?? '');
    _constructionPeriodController = TextEditingController(text: p.constructionPeriodMonths.toString());

    _kind = p.kind;
    _monthlyAggrDate = p.monthlyAggrStartDate.isNotEmpty ? p.monthlyAggrStartDate : DateFormat('yyyy-MM-dd').format(DateTime.now());
    _constructionStartDate = p.constructionStartDate.isNotEmpty ? p.constructionStartDate : DateFormat('yyyy-MM-dd').format(DateTime.now());
    _isDirectManage = p.isDirectManage;
    _isReturnedArea = p.isReturnedArea;
    _isUnitSet = p.isUnitSet;
  }

  @override
  void dispose() {
    _nameController.dispose();
    _locationController.dispose();
    _areaUsageController.dispose();
    _buildSizeController.dispose();
    _numUnitController.dispose();
    _schemeLandController.dispose();
    _totalFloorController.dispose();
    _constructionPeriodController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_nameController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('프로젝트명을 입력하세요.'), behavior: SnackBarBehavior.floating),
      );
      return;
    }

    setState(() => _isLoading = true);

    final payload = <String, dynamic>{
      'name': _nameController.text.trim(),
      'kind': _kind,
      'location': _locationController.text.trim(),
      'area_usage': _areaUsageController.text.trim(),
      'build_size': _buildSizeController.text.trim(),
      'is_direct_manage': _isDirectManage,
      'is_returned_area': _isReturnedArea,
      'is_unit_set': _isUnitSet,
      'monthly_aggr_start_date': _monthlyAggrDate,
      'construction_start_date': _constructionStartDate,
    };

    if (_numUnitController.text.trim().isNotEmpty) {
      payload['num_unit'] = int.tryParse(_numUnitController.text.trim());
    }
    if (_schemeLandController.text.trim().isNotEmpty) {
      payload['scheme_land_extent'] = double.tryParse(_schemeLandController.text.trim());
    }
    if (_totalFloorController.text.trim().isNotEmpty) {
      payload['total_floor_area'] = double.tryParse(_totalFloorController.text.trim());
    }
    if (_constructionPeriodController.text.trim().isNotEmpty) {
      payload['construction_period_months'] = int.tryParse(_constructionPeriodController.text.trim()) ?? 0;
    }

    final repo = ref.read(projectRepositoryProvider);
    final errorMsg = await repo.updateRealEstateProject(
      projectId: widget.project.pk,
      payload: payload,
    );

    setState(() => _isLoading = false);

    if (mounted) {
      if (errorMsg == null) {
        widget.onSuccess();
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('프로젝트 기본 정보가 수정되었습니다.'), behavior: SnackBarBehavior.floating),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('수정 실패: $errorMsg'),
            backgroundColor: context.colors.error,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      height: MediaQuery.of(context).size.height * 0.88,
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.zero,
        border: Border(top: BorderSide(color: context.colors.border, width: 0.8)),
      ),
      child: SafeArea(
        child: Column(
          children: [
            // 상단 헤더
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              color: context.colors.bgSurface,
              child: Row(
                children: [
                  Container(
                    width: 32,
                    height: 32,
                    decoration: BoxDecoration(
                      color: const Color(0xFF00796B).withAlpha(20),
                      borderRadius: BorderRadius.zero,
                    ),
                    child: const Icon(Icons.edit_note, size: 18, color: Color(0xFF00796B)),
                  ),
                  const SizedBox(width: 10),
                  Text(
                    '프로젝트 기본 정보 수정',
                    style: AppTextStyles.titleSm.copyWith(
                      color: context.colors.textPrimary,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const Spacer(),
                  IconButton(
                    icon: const Icon(Icons.close, size: 20),
                    onPressed: () => Navigator.pop(context),
                  ),
                ],
              ),
            ),
            Divider(color: context.colors.border, height: 1),

            // 입력 폼 스크롤 본문
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // 프로젝트명 & 종류
                    Row(
                      children: [
                        Expanded(
                          flex: 3,
                          child: TextField(
                            controller: _nameController,
                            style: const TextStyle(fontSize: 13),
                            decoration: const InputDecoration(
                              labelText: '프로젝트명 *',
                              isDense: true,
                              border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                            ),
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          flex: 2,
                          child: DropdownButtonFormField<String>(
                            initialValue: _kind,
                            decoration: const InputDecoration(
                              labelText: '프로젝트 종류',
                              isDense: true,
                              border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                            ),
                            items: const [
                              DropdownMenuItem(value: '1', child: Text('공동주택(아파트)')),
                              DropdownMenuItem(value: '2', child: Text('공동주택(타운하우스)')),
                              DropdownMenuItem(value: '3', child: Text('주상복합(아파트)')),
                              DropdownMenuItem(value: '4', child: Text('주상복합(오피스텔)')),
                              DropdownMenuItem(value: '5', child: Text('근린생활시설')),
                              DropdownMenuItem(value: '6', child: Text('생활형숙박시설')),
                              DropdownMenuItem(value: '7', child: Text('지식산업센터')),
                              DropdownMenuItem(value: '8', child: Text('기타')),
                            ],
                            onChanged: (v) => setState(() => _kind = v ?? '1'),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),

                    // 대지 위치
                    TextField(
                      controller: _locationController,
                      style: const TextStyle(fontSize: 13),
                      decoration: const InputDecoration(
                        labelText: '대지 위치(소재지)',
                        hintText: '예: 경기도 오산시 세교동 123-4 일원',
                        isDense: true,
                        border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                      ),
                    ),
                    const SizedBox(height: 12),

                    // 용도지역 & 건축규모
                    Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: _areaUsageController,
                            style: const TextStyle(fontSize: 13),
                            decoration: const InputDecoration(
                              labelText: '용도지역지구',
                              hintText: '예: 제3종일반주거지역',
                              isDense: true,
                              border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                            ),
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: TextField(
                            controller: _buildSizeController,
                            style: const TextStyle(fontSize: 13),
                            decoration: const InputDecoration(
                              labelText: '건축 규모',
                              hintText: '예: 지하 2층 ~ 지상 29층',
                              isDense: true,
                              border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),

                    // 세대수, 대지면적, 연면적
                    Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: _numUnitController,
                            keyboardType: TextInputType.number,
                            style: const TextStyle(fontSize: 13),
                            decoration: const InputDecoration(
                              labelText: '총 세대수',
                              hintText: '예: 540',
                              isDense: true,
                              border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: TextField(
                            controller: _schemeLandController,
                            keyboardType: const TextInputType.numberWithOptions(decimal: true),
                            style: const TextStyle(fontSize: 13),
                            decoration: const InputDecoration(
                              labelText: '계획대지면적(㎡)',
                              isDense: true,
                              border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: TextField(
                            controller: _totalFloorController,
                            keyboardType: const TextInputType.numberWithOptions(decimal: true),
                            style: const TextStyle(fontSize: 13),
                            decoration: const InputDecoration(
                              labelText: '총 연면적(㎡)',
                              isDense: true,
                              border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 14),

                    // 일정 설정 (집계시작일, 착공월, 공사기간)
                    Row(
                      children: [
                        Expanded(
                          child: InkWell(
                            onTap: () async {
                              final picked = await showDatePicker(
                                context: context,
                                initialDate: DateTime.tryParse(_monthlyAggrDate) ?? DateTime.now(),
                                firstDate: DateTime(2000),
                                lastDate: DateTime(2100),
                              );
                              if (picked != null) {
                                setState(() => _monthlyAggrDate = DateFormat('yyyy-MM-dd').format(picked));
                              }
                            },
                            child: InputDecorator(
                              decoration: const InputDecoration(
                                labelText: '월별집계시작일',
                                isDense: true,
                                border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                              ),
                              child: Text(_monthlyAggrDate, style: const TextStyle(fontSize: 12.5)),
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: InkWell(
                            onTap: () async {
                              final picked = await showDatePicker(
                                context: context,
                                initialDate: DateTime.tryParse(_constructionStartDate) ?? DateTime.now(),
                                firstDate: DateTime(2000),
                                lastDate: DateTime(2100),
                              );
                              if (picked != null) {
                                setState(() => _constructionStartDate = DateFormat('yyyy-MM-dd').format(picked));
                              }
                            },
                            child: InputDecorator(
                              decoration: const InputDecoration(
                                labelText: '착공일(예상)',
                                isDense: true,
                                border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                              ),
                              child: Text(_constructionStartDate, style: const TextStyle(fontSize: 12.5)),
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: TextField(
                            controller: _constructionPeriodController,
                            keyboardType: TextInputType.number,
                            style: const TextStyle(fontSize: 13),
                            decoration: const InputDecoration(
                              labelText: '공사기간(개월)',
                              isDense: true,
                              border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 14),

                    // 체크박스 옵션 3종
                    CheckboxListTile(
                      contentPadding: EdgeInsets.zero,
                      controlAffinity: ListTileControlAffinity.leading,
                      dense: true,
                      title: const Text('본사 직영 운영 여부 (시행/업무대행이 아닌 경우)', style: TextStyle(fontSize: 12)),
                      value: _isDirectManage,
                      onChanged: (v) => setState(() => _isDirectManage = v ?? false),
                    ),
                    CheckboxListTile(
                      contentPadding: EdgeInsets.zero,
                      controlAffinity: ListTileControlAffinity.leading,
                      dense: true,
                      title: const Text('토지 환지 방식 도시개발사업 여부', style: TextStyle(fontSize: 12)),
                      value: _isReturnedArea,
                      onChanged: (v) => setState(() => _isReturnedArea = v ?? false),
                    ),
                    CheckboxListTile(
                      contentPadding: EdgeInsets.zero,
                      controlAffinity: ListTileControlAffinity.leading,
                      dense: true,
                      title: const Text('동·호수 지정 분양 방식 적용 여부', style: TextStyle(fontSize: 12)),
                      value: _isUnitSet,
                      onChanged: (v) => setState(() => _isUnitSet = v ?? false),
                    ),
                  ],
                ),
              ),
            ),
            Divider(color: context.colors.border, height: 1),

            // 하단 저장 액션바
            Padding(
              padding: const EdgeInsets.all(12),
              child: Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      style: OutlinedButton.styleFrom(
                        foregroundColor: context.colors.textPrimary,
                        side: BorderSide(color: context.colors.border),
                        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                        padding: const EdgeInsets.symmetric(vertical: 12),
                      ),
                      onPressed: _isLoading ? null : () => Navigator.pop(context),
                      child: const Text('취소'),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    flex: 2,
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF00796B),
                        foregroundColor: Colors.white,
                        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                        padding: const EdgeInsets.symmetric(vertical: 12),
                      ),
                      onPressed: _isLoading ? null : _submit,
                      child: _isLoading
                          ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                          : const Text('변경사항 저장', style: TextStyle(fontWeight: FontWeight.bold)),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
