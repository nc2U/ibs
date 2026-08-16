import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';

/// 온보딩 & 주요 업무 가이드 탭 뷰 (목데이터)
class OnboardingTabView extends ConsumerStatefulWidget {
  const OnboardingTabView({super.key});

  @override
  ConsumerState<OnboardingTabView> createState() => _OnboardingTabViewState();
}

class _OnboardingTabViewState extends ConsumerState<OnboardingTabView> {
  int _selectedFilter = 0;
  final _filters = ['전체 가이드', '신규입사 안내', '시스템 사용법', '업무 프로세스'];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: context.colors.bgPrimary,
      body: CustomScrollView(
        slivers: [
          // ── 1. 상단 필터 칩 바 ──────────────────────────────────────
          SliverToBoxAdapter(
            child: Container(
              color: context.colors.bgCard,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              child: SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: List.generate(_filters.length, (idx) {
                    final isSelected = _selectedFilter == idx;
                    return Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: ChoiceChip(
                        label: Text(_filters[idx]),
                        selected: isSelected,
                        onSelected: (_) => setState(() => _selectedFilter = idx),
                        selectedColor: context.colors.accentProject,
                        backgroundColor: context.colors.bgSurface,
                        labelStyle: TextStyle(
                          color: isSelected
                              ? Colors.white
                              : context.colors.textSecond,
                          fontWeight: isSelected
                              ? FontWeight.bold
                              : FontWeight.normal,
                          fontSize: 13,
                        ),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(20),
                          side: BorderSide(
                            color: isSelected
                                ? context.colors.accentProject
                                : context.colors.border,
                            width: 0.8,
                          ),
                        ),
                        showCheckmark: false,
                        padding: const EdgeInsets.symmetric(
                            horizontal: 10, vertical: 4),
                      ),
                    );
                  }),
                ),
              ),
            ),
          ),

          // ── 2. 본문 섹션 ────────────────────────────────────────────────
          SliverPadding(
            padding: const EdgeInsets.all(16),
            sliver: SliverList(
              delegate: SliverChildListDelegate([
                if (_selectedFilter == 0 || _selectedFilter == 1) ...[
                  // 🚀 신입사원 온보딩 로드맵 배너
                  _buildOnboardingProgressCard(context),
                  const SizedBox(height: 16),

                  // 🔰 신규 입사자 첫걸음 체크리스트
                  _buildFirstWeekChecklist(context),
                  const SizedBox(height: 20),
                ],

                if (_selectedFilter == 0 || _selectedFilter == 2) ...[
                  // 💻 IBS 시스템 핵심 사용법 카드
                  _buildSystemGuidesSection(context),
                  const SizedBox(height: 20),
                ],

                if (_selectedFilter == 0 || _selectedFilter == 3) ...[
                  // 📋 핵심 업무 프로세스 가이드
                  _buildWorkProcessSection(context),
                  const SizedBox(height: 40),
                ],
              ]),
            ),
          ),
        ],
      ),
    );
  }

  // 🚀 온보딩 로드맵 카드
  Widget _buildOnboardingProgressCard(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: context.colors.accentProject.withAlpha(100)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.flight_takeoff_rounded,
                  color: Colors.teal, size: 22),
              const SizedBox(width: 8),
              Text(
                '신입사원 온보딩 4단계 로드맵',
                style: AppTextStyles.titleSm.copyWith(
                  fontWeight: FontWeight.bold,
                  color: context.colors.textPrimary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            '입사 1일차부터 1개월까지, 회사와 시스템에 빠르게 적응할 수 있도록 지원합니다.',
            style: AppTextStyles.caption.copyWith(
              color: context.colors.textMuted,
              height: 1.35,
            ),
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              _buildStepItem(context, '1일차', '계정/자리 세팅', true),
              _buildStepDivider(),
              _buildStepItem(context, '1주차', '조직/동료 인사', true),
              _buildStepDivider(),
              _buildStepItem(context, '2주차', 'IBS 시스템 학습', false),
              _buildStepDivider(),
              _buildStepItem(context, '1개월', '실전 업무 투입', false),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStepItem(
      BuildContext context, String step, String title, bool isDone) {
    return Expanded(
      child: Column(
        children: [
          CircleAvatar(
            radius: 12,
            backgroundColor: isDone
                ? context.colors.accentProject
                : context.colors.bgSurface,
            child: Icon(
              isDone ? Icons.check : Icons.circle_outlined,
              size: 14,
              color: isDone ? Colors.white : context.colors.textDisabled,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            step,
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.bold,
              color: isDone
                  ? context.colors.accentProject
                  : context.colors.textMuted,
            ),
          ),
          Text(
            title,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 10,
              color: context.colors.textSecond,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStepDivider() {
    return Container(
      width: 16,
      height: 1.5,
      color: Colors.grey.withAlpha(100),
      margin: const EdgeInsets.only(bottom: 28),
    );
  }

  // 🔰 1주차 체크리스트
  Widget _buildFirstWeekChecklist(BuildContext context) {
    final tasks = [
      {'title': '사내 그룹웨어 및 IBS 워크스페이스 계정 발급 확인', 'done': true},
      {'title': '사내 메신저 설치 및 소속 본부 대화방 참여', 'done': true},
      {'title': '사내 복무규정 및 정보보안 서약서 확인', 'done': false},
      {'title': '본사관리 및 담당 프로젝트 워크스페이스 권한 부여 요청', 'done': false},
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '첫걸음 필수 체크리스트',
          style: AppTextStyles.titleMd.copyWith(
            fontWeight: FontWeight.bold,
            color: context.colors.textPrimary,
          ),
        ),
        const SizedBox(height: 10),
        ...tasks.map((t) => Container(
              margin: const EdgeInsets.only(bottom: 6),
              decoration: BoxDecoration(
                color: context.colors.bgCard,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: context.colors.border, width: 0.8),
              ),
              child: CheckboxListTile(
                value: t['done'] as bool,
                onChanged: (_) {},
                activeColor: context.colors.accentProject,
                dense: true,
                title: Text(
                  t['title'] as String,
                  style: AppTextStyles.bodyMd.copyWith(
                    color: (t['done'] as bool)
                        ? context.colors.textMuted
                        : context.colors.textPrimary,
                    decoration: (t['done'] as bool)
                        ? TextDecoration.lineThrough
                        : null,
                  ),
                ),
              ),
            )),
      ],
    );
  }

  // 💻 IBS 시스템 사용법 섹션
  Widget _buildSystemGuidesSection(BuildContext context) {
    final guides = [
      {
        'title': '🏢 워크스페이스 선택 및 이동',
        'desc': '본사관리, 분양 프로젝트, 현장 등 원하는 공간으로 1초 만에 전환하는 방법',
        'badge': '기초',
      },
      {
        'title': '📅 회의록 작성 및 액션아이템 연동',
        'desc': '회의 의제, 결정사항 기록 후 관련 담당자에게 업무(Issue)를 즉시 할당하는 방법',
        'badge': '업무',
      },
      {
        'title': '📋 내 업무 진척률 관리 및 댓글 피드백',
        'desc': '할당된 업무의 상태/진척률(0~100%)을 실시간 수정하고 사진·파일 첨부하기',
        'badge': '업무',
      },
      {
        'title': '🏗️ 프로젝트 분양계약 및 수납 현황 조회',
        'desc': '부동산 개발 사업지의 동호수별 계약 현황, 차수별 납부 내역 및 미납금 실시간 확인',
        'badge': '사업',
      },
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              '💻 IBS 시스템 사용 가이드',
              style: AppTextStyles.titleMd.copyWith(
                fontWeight: FontWeight.bold,
                color: context.colors.textPrimary,
              ),
            ),
            Text(
              '동영상/매뉴얼',
              style: AppTextStyles.caption
                  .copyWith(color: context.colors.accentWork),
            ),
          ],
        ),
        const SizedBox(height: 10),
        ...guides.map((g) => Container(
              margin: const EdgeInsets.only(bottom: 8),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: context.colors.bgCard,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: context.colors.border, width: 0.8),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          g['title']!,
                          style: AppTextStyles.bodyMd.copyWith(
                            fontWeight: FontWeight.w600,
                            color: context.colors.textPrimary,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          g['desc']!,
                          style: AppTextStyles.caption.copyWith(
                            color: context.colors.textMuted,
                            height: 1.3,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 8),
                  const Icon(Icons.play_circle_outline_rounded,
                      color: Colors.blueAccent, size: 24),
                ],
              ),
            )),
      ],
    );
  }

  // 📋 업무 프로세스 섹션
  Widget _buildWorkProcessSection(BuildContext context) {
    final processes = [
      {'title': '지출결의 및 자금 집행 프로세스', 'dept': '재무회계', 'time': '3단계'},
      {'title': '시행 부지 인허가 및 심의 보고 절차', 'dept': '개발사업', 'time': '5단계'},
      {'title': '현장 공정률 및 안전점검 등록 절차', 'dept': '건설사업', 'time': '4단계'},
      {'title': '분양 계약 해지 및 명의변경 승계 절차', 'dept': '분양마케팅', 'time': '3단계'},
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '📋 주요 부서별 업무 프로세스',
          style: AppTextStyles.titleMd.copyWith(
            fontWeight: FontWeight.bold,
            color: context.colors.textPrimary,
          ),
        ),
        const SizedBox(height: 10),
        ...processes.map((p) => ListTile(
              contentPadding:
                  const EdgeInsets.symmetric(horizontal: 14, vertical: 2),
              tileColor: context.colors.bgCard,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
                side: BorderSide(color: context.colors.border, width: 0.8),
              ),
              leading: const Icon(Icons.account_tree_outlined,
                  color: Colors.teal, size: 22),
              title: Text(
                p['title']!,
                style: AppTextStyles.bodyMd.copyWith(
                  fontWeight: FontWeight.w500,
                  color: context.colors.textPrimary,
                ),
              ),
              subtitle: Text(
                '담당부서: ${p['dept']} · 소요단계: ${p['time']}',
                style: AppTextStyles.caption
                    .copyWith(color: context.colors.textMuted),
              ),
              trailing: const Icon(Icons.arrow_forward_ios_rounded,
                  size: 14, color: Colors.grey),
              onTap: () {},
            )),
      ],
    );
  }
}
