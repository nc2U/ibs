import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/providers/project_provider.dart';
import '../../../../core/theme/app_colors_extension.dart';

/// 🤝 분양 대행 관리 (Sales Agency) 서브 탭 구분
enum SalesSubTab {
  performance, // 계약 실적 관리
  settlement,  // 수수료 정산 관리
  payout,      // 수수료 지급 관리
  organization,// 영업 조직 관리
  policy,      // 수수료 정책 관리
}

/// 🤝 분양 대행 관리 (Sales) 메인 화면
class SalesScreen extends ConsumerStatefulWidget {
  final VoidCallback onBackToMain;

  const SalesScreen({
    super.key,
    required this.onBackToMain,
  });

  @override
  ConsumerState<SalesScreen> createState() => _SalesScreenState();
}

class _SalesScreenState extends ConsumerState<SalesScreen> {
  SalesSubTab _currentTab = SalesSubTab.performance;

  @override
  Widget build(BuildContext context) {
    final selectedProject = ref.watch(selectedRealEstateProjectProvider);

    return Scaffold(
      backgroundColor: context.colors.bgPrimary,
      body: Column(
        children: [
          // ── 상단 서브 탭 바 (IBS Global Flat radius=0) ─────────────────
          Container(
            width: double.infinity,
            decoration: BoxDecoration(
              color: context.colors.bgSurface,
              border: Border(
                bottom: BorderSide(color: context.colors.border, width: 1),
              ),
            ),
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              child: Row(
                children: [
                  _buildSubTabButton(
                    tab: SalesSubTab.performance,
                    label: '계약 실적',
                    icon: Icons.assignment_turned_in_outlined,
                  ),
                  const SizedBox(width: 8),
                  _buildSubTabButton(
                    tab: SalesSubTab.settlement,
                    label: '수수료 정산',
                    icon: Icons.calculate_outlined,
                  ),
                  const SizedBox(width: 8),
                  _buildSubTabButton(
                    tab: SalesSubTab.payout,
                    label: '수수료 지급',
                    icon: Icons.account_balance_outlined,
                  ),
                  const SizedBox(width: 8),
                  _buildSubTabButton(
                    tab: SalesSubTab.organization,
                    label: '영업 조직',
                    icon: Icons.groups_outlined,
                  ),
                  const SizedBox(width: 8),
                  _buildSubTabButton(
                    tab: SalesSubTab.policy,
                    label: '수수료 정책',
                    icon: Icons.rule_folder_outlined,
                  ),
                ],
              ),
            ),
          ),

          // ── 본문 영역 ──────────────────────────────────────────
          Expanded(
            child: selectedProject == null
                ? Center(
                    child: Text(
                      '프로젝트를 먼저 선택해 주세요.',
                      style: AppTextStyles.bodySecond.copyWith(
                        color: context.colors.textMuted,
                      ),
                    ),
                  )
                : _buildTabContent(selectedProject.name),
          ),
        ],
      ),
    );
  }

  Widget _buildSubTabButton({
    required SalesSubTab tab,
    required String label,
    required IconData icon,
  }) {
    final isSelected = _currentTab == tab;
    const primaryColor = Color(0xFF8B5CF6); // Violet

    return Material(
      color: isSelected ? primaryColor : context.colors.bgCard,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.zero,
        side: BorderSide(
          color: isSelected ? primaryColor : context.colors.border,
          width: 0.8,
        ),
      ),
      child: InkWell(
        onTap: () => setState(() => _currentTab = tab),
        borderRadius: BorderRadius.zero,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                icon,
                size: 14,
                color: isSelected ? Colors.white : context.colors.textSecond,
              ),
              const SizedBox(width: 6),
              Text(
                label,
                style: AppTextStyles.label.copyWith(
                  color: isSelected ? Colors.white : context.colors.textSecond,
                  fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
                  fontSize: 12,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTabContent(String projectName) {
    switch (_currentTab) {
      case SalesSubTab.performance:
        return _buildPerformanceView(projectName);
      case SalesSubTab.settlement:
        return _buildSettlementView(projectName);
      case SalesSubTab.payout:
        return _buildPayoutView(projectName);
      case SalesSubTab.organization:
        return _buildOrganizationView(projectName);
      case SalesSubTab.policy:
        return _buildPolicyView(projectName);
    }
  }

  /// 1. 계약 실적 관리 뷰
  Widget _buildPerformanceView(String projectName) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _buildInfoBanner(
          title: '계약 실적 & 영업 담당자 매핑',
          subtitle: '체결된 분양 계약에 영업 상담사 및 MGM 중개사를 배정하고 실적을 집계합니다.',
          icon: Icons.assignment_turned_in_outlined,
          color: const Color(0xFF8B5CF6),
        ),
        const SizedBox(height: 16),
        _buildKpiCard(
          title: '영업 배정 KPI 요약',
          items: const [
            {'label': '분양 계약', 'value': '진행 중', 'color': 0xFF38BDF8},
            {'label': '영업 배정률', 'value': '실시간 집계', 'color': 0xFF34D399},
            {'label': 'MGM 연계', 'value': '공인중개사', 'color': 0xFFFBBF24},
          ],
        ),
        const SizedBox(height: 16),
        _buildFeatureCard(
          title: '모바일 실적 조회 안내',
          description:
              '웹에서 등록된 상담사별 계약 실적과 MGM 매핑 정보를 프로젝트 기준으로 실시간 연동합니다. 계약 배정 변경 및 상세 수정은 IBS 웹 시스템을 통해 지원됩니다.',
          tags: const ['계약자 매핑', '소속 팀 연동', '성과 인정일', 'MGM 정보'],
        ),
      ],
    );
  }

  /// 2. 수수료 정산 관리 뷰
  Widget _buildSettlementView(String projectName) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _buildInfoBanner(
          title: '수수료 정산 관리',
          subtitle: '정산 주기 회차별 계약 실적 집계, 3.3% 원천세 계산 및 환수금 상계를 관리합니다.',
          icon: Icons.calculate_outlined,
          color: const Color(0xFF06B6D4),
        ),
        const SizedBox(height: 16),
        _buildKpiCard(
          title: '정산 프로세스 안내',
          items: const [
            {'label': '원천세율', 'value': '3.3%', 'color': 0xFFEF4444},
            {'label': '환수 상계', 'value': '자동 차감', 'color': 0xFFF59E0B},
            {'label': '정산 엔진', 'value': '실시간 연동', 'color': 0xFF10B981},
          ],
        ),
        const SizedBox(height: 16),
        _buildFeatureCard(
          title: '회차별 수수료 정산 현황',
          description:
              '정산 회차(월별/주기별)에 따라 사업소득세(3%) 및 지방소득세(0.3%)가 자동 절사 계산되며, 해약 환수금 상계 내역이 반영된 세후 실지급액을 열람할 수 있습니다.',
          tags: ['정산 회차', '건당 인센티브', '기본급/일비', '세후 실지급액'],
        ),
      ],
    );
  }

  /// 3. 수수료 지급 관리 뷰
  Widget _buildPayoutView(String projectName) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _buildInfoBanner(
          title: '수수료 지급 대장 & 이체',
          subtitle: '지급 승인 내역 조회, 대량 이체 파일 연계 및 지급 완료 상태를 관리합니다.',
          icon: Icons.account_balance_outlined,
          color: const Color(0xFF10B981),
        ),
        const SizedBox(height: 16),
        _buildKpiCard(
          title: '지급 진행 요약 지표',
          items: const [
            {'label': '지급 승인', 'value': '대기/승인', 'color': 0xFF3B82F6},
            {'label': '이체 상태', 'value': '실시간 모니터링', 'color': 0xFF10B981},
            {'label': '원천세 예수금', 'value': '익월 10일 납부', 'color': 0xFFEF4444},
          ],
        ),
        const SizedBox(height: 16),
        _buildFeatureCard(
          title: '기업 뱅킹 이체 관리 안내',
          description:
              '개인별 지급 상태(지급대기, 승인, 완료, 보류)와 계좌 정보를 확인하고, 웹 시스템을 통해 은행 대량 이체 표준 CSV 파일을 다운로드하여 뱅킹 사이트에 일괄 전송할 수 있습니다.',
          tags: ['지급 상태', '은행 계좌 확인', '예금주 검증', '지급일자 추적'],
        ),
      ],
    );
  }

  /// 4. 영업 조직 관리 뷰
  Widget _buildOrganizationView(String projectName) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _buildInfoBanner(
          title: '영업 조직 & 인력 명부',
          subtitle: '분양 대행사 ➔ 영업 본부/팀 ➔ 상담사 3단계 계층 구조를 관리합니다.',
          icon: Icons.groups_outlined,
          color: const Color(0xFF6366F1),
        ),
        const SizedBox(height: 16),
        _buildFeatureCard(
          title: '영업 조직 체계',
          description:
              '프로젝트에 투입된 직영/외주 분양 대행사, 산하 영업 팀, 상담사 인력 명부와 금융 입금 계좌 정보를 조회합니다. 3.3% 프리랜서 사업소득 원천징수 여부 및 재직 상태(위촉/해촉)가 통합 관리됩니다.',
          tags: ['대행사 관리', '영업팀 계층', '상담사 인력', '3.3% 프리랜서'],
        ),
      ],
    );
  }

  /// 5. 수수료 정책 관리 뷰
  Widget _buildPolicyView(String projectName) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _buildInfoBanner(
          title: '수수료 정책 (R값 기준표)',
          subtitle: '차수 및 유니트 타입별 직책별 수수료(상담사, 팀장, 본부장) 기준표를 관리합니다.',
          icon: Icons.rule_folder_outlined,
          color: const Color(0xFFEC4899),
        ),
        const SizedBox(height: 16),
        _buildFeatureCard(
          title: '차수/타입별 인센티브 기준',
          description:
              '유니트 타입(평형) 및 공급 차수별로 책정된 건당 수수료 기준표입니다. 담당 상담사 fee, 팀장 및 본부장 오버라이딩 fee, 외부 공인중개사 MGM 소개료가 정의되어 계약 실적에 자동 매핑됩니다.',
          tags: ['타입별 R값', '직책별 차등', 'MGM 소개료', '지급 조건'],
        ),
      ],
    );
  }

  Widget _buildInfoBanner({
    required String title,
    required String subtitle,
    required IconData icon,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.zero,
        border: Border.all(color: color.withAlpha(70), width: 1),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: color.withAlpha(25),
              borderRadius: BorderRadius.zero,
              border: Border.all(color: color.withAlpha(70), width: 0.8),
            ),
            child: Icon(icon, size: 20, color: color),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: AppTextStyles.titleSm.copyWith(
                    color: context.colors.textPrimary,
                    fontWeight: FontWeight.bold,
                    fontSize: 15,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  subtitle,
                  style: AppTextStyles.bodySecond.copyWith(
                    color: context.colors.textSecond,
                    fontSize: 12,
                    height: 1.35,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildKpiCard({
    required String title,
    required List<Map<String, dynamic>> items,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.zero,
        border: Border.all(color: context.colors.border, width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: AppTextStyles.label.copyWith(
              color: context.colors.textMuted,
              fontWeight: FontWeight.bold,
              fontSize: 12,
            ),
          ),
          const SizedBox(height: 12),
          Row(
            children: items.map((item) {
              final color = Color(item['color'] as int);
              return Expanded(
                child: Container(
                  margin: const EdgeInsets.symmetric(horizontal: 4),
                  padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 8),
                  decoration: BoxDecoration(
                    color: color.withAlpha(15),
                    borderRadius: BorderRadius.zero,
                    border: Border.all(color: color.withAlpha(50), width: 0.8),
                  ),
                  child: Column(
                    children: [
                      Text(
                        item['label'] as String,
                        style: AppTextStyles.caption.copyWith(
                          color: context.colors.textMuted,
                          fontSize: 11,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        item['value'] as String,
                        style: AppTextStyles.titleSm.copyWith(
                          color: color,
                          fontWeight: FontWeight.bold,
                          fontSize: 13,
                        ),
                      ),
                    ],
                  ),
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }

  Widget _buildFeatureCard({
    required String title,
    required String description,
    required List<String> tags,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.zero,
        border: Border.all(color: context.colors.border, width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: AppTextStyles.titleSm.copyWith(
              color: context.colors.textPrimary,
              fontWeight: FontWeight.bold,
              fontSize: 14,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            description,
            style: AppTextStyles.bodySecond.copyWith(
              color: context.colors.textSecond,
              fontSize: 12.5,
              height: 1.4,
            ),
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: tags.map((t) {
              return Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: context.colors.bgSurface,
                  borderRadius: BorderRadius.zero,
                  border: Border.all(color: context.colors.border, width: 0.8),
                ),
                child: Text(
                  t,
                  style: AppTextStyles.caption.copyWith(
                    color: context.colors.textMuted,
                    fontSize: 11,
                  ),
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }
}
