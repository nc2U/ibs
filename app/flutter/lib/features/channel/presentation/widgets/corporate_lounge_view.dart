import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';

/// 전사 라운지 & 온보딩 단일 허브 뷰 (Corporate Lounge & Onboarding Hub)
/// ── 상단 중첩 탭을 100% 제거하고 브랜드 북 & 온보딩 가이드를 단일 스크롤로 제공
class CorporateLoungeView extends ConsumerStatefulWidget {
  const CorporateLoungeView({super.key});

  @override
  ConsumerState<CorporateLoungeView> createState() =>
      _CorporateLoungeViewState();
}

class _CorporateLoungeViewState extends ConsumerState<CorporateLoungeView> {
  // FAQ 카테고리 필터
  int _faqCategoryIndex = 0;
  final _faqCategories = ['전체 FAQ', '인사·근태', '전산·계정', '경비·복지'];

  final _faqList = [
    {
      'cat': '인사·근태',
      'q': '연차 및 반차 신청은 언제까지 어떻게 해야 하나요?',
      'a': '연차 및 반차는 사용 예정일 최소 1일 전까지 IBS [전자결재 > 근태신청서]를 통해 기안 후 부서장 승인을 받으시면 됩니다. 긴급한 병가 시에는 유선 보고 후 사후 상신이 가능합니다.',
    },
    {
      'cat': '인사·근태',
      'q': '출퇴근 체크 및 외근/출장 등록 방법이 궁금합니다.',
      'a': '모바일 IBS 앱 메인 화면에서 [출퇴근 체크]를 누르시거나, 사내 Wi-Fi 연결 시 자동 인식됩니다. 외근 및 현장 출장 시에는 사전 구두 보고 후 업무 일정에 등록해 주시면 됩니다.',
    },
    {
      'cat': '전산·계정',
      'q': '특정 워크스페이스(프로젝트) 접근 권한이 없다고 나와요.',
      'a': '새로 배속된 현장이나 프로젝트는 해당 워크스페이스의 [업무관리자] 또는 [경영지원본부 전산담당자]에게 권한 승인 요청을 남겨주시면 즉시 추가됩니다.',
    },
    {
      'cat': '전산·계정',
      'q': '비밀번호를 분실했거나 계정이 잠겼을 때는 어떻게 하나요?',
      'a': '로그인 화면의 [비밀번호 찾기]를 통해 등록된 사내 이메일로 임시 링크를 수신하시거나, 전산 관리자에게 초기화를 요청하세요.',
    },
    {
      'cat': '경비·복지',
      'q': '식대 및 야근 교통비 영수증 정산 기한은 언제인가요?',
      'a': '매월 1일부터 말일까지 사용한 법인카드 및 개인 경비는 익월 5일까지 [지출결의서]를 작성하고 법인카드 영수증 또는 전자세금계산서를 첨부하여 결재를 올려주셔야 당월 급여일에 지급됩니다.',
    },
    {
      'cat': '경비·복지',
      'q': '명절 귀향비 및 경조사비 지급 기준은 어디서 보나요?',
      'a': '[사내 규정집] 내 [경조사 및 복리후생 지원 기준] 문서를 참고하시거나 담당 총무팀으로 문의하시면 됩니다.',
    },
  ];

  @override
  Widget build(BuildContext context) {
    final filteredFaqs = _faqCategoryIndex == 0
        ? _faqList
        : _faqList
            .where((f) => f['cat'] == _faqCategories[_faqCategoryIndex])
            .toList();

    return Scaffold(
      backgroundColor: context.colors.bgPrimary,
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(20, 20, 20, 56),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── 1. 기업 철학 (목적 & 사명) ──────────────────────────────
            _buildSectionHeader(
              context: context,
              categoryEn: 'PHILOSOPHY',
              titleKo: '기업 철학',
            ),
            _buildPurposeSection(context),
            const SizedBox(height: 12),
            _buildMissionSection(context),
            const SizedBox(height: 36),

            // ── 2. 5대 핵심 가치관 (Core Values) ─────────────────────────
            _buildSectionHeader(
              context: context,
              categoryEn: 'CORE VALUES & BELIEFS',
              titleKo: '핵심 가치관',
              badgeText: '5대 행동양식',
            ),
            _buildCoreValuesSection(context),
            const SizedBox(height: 36),

            // ── 3. 조직도 (Organization) ─────────────────────────────────
            _buildSectionHeader(
              context: context,
              categoryEn: 'ORGANIZATION',
              titleKo: '조직도',
              badgeText: '5개 본부·부서',
            ),
            _buildOrganizationSection(context),
            const SizedBox(height: 36),

            // ── 4. 사내 공식 규정집 (Regulations) ────────────────────────
            _buildSectionHeader(
              context: context,
              categoryEn: 'REGULATIONS',
              titleKo: '사내 규정집',
              badgeText: '공용문서 연동',
            ),
            _buildRegulationsSection(context),
            const SizedBox(height: 36),

            // ── 5. 신입사원 온보딩 & 업무 가이드 (Onboarding) ───────────
            _buildSectionHeader(
              context: context,
              categoryEn: 'ONBOARDING & GUIDE',
              titleKo: '온보딩 & 업무 가이드',
            ),
            _buildOnboardingSection(context),
            const SizedBox(height: 36),

            // ── 6. 자주 묻는 질문 (FAQ) & 기술지원 ──────────────────────
            _buildSectionHeader(
              context: context,
              categoryEn: 'FAQ & SUPPORT',
              titleKo: 'FAQ & 기술지원',
            ),
            _buildFaqSection(context, filteredFaqs),
          ],
        ),
      ),
    );
  }

  // ── 섹션 공통 헤더 타이틀 ───────────────────────────────────────────────
  Widget _buildSectionHeader({
    required BuildContext context,
    required String categoryEn,
    required String titleKo,
    String? badgeText,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.baseline,
        textBaseline: TextBaseline.alphabetic,
        children: [
          Text(
            titleKo,
            style: AppTextStyles.titleMd.copyWith(
              fontWeight: FontWeight.bold,
              color: context.colors.textPrimary,
              letterSpacing: -0.3,
            ),
          ),
          const SizedBox(width: 8),
          Text(
            categoryEn,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              letterSpacing: 0.8,
              color: context.colors.textMuted,
            ),
          ),
          const Spacer(),
          if (badgeText != null)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
              decoration: BoxDecoration(
                color: context.colors.bgCard,
                borderRadius: BorderRadius.circular(4),
                border: Border.all(color: context.colors.border, width: 0.8),
              ),
              child: Text(
                badgeText,
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  color: context.colors.textSecond,
                ),
              ),
            ),
        ],
      ),
    );
  }

  // ── 1-1. 목적 (Purpose) ────────────────────────────────────────────────
  Widget _buildPurposeSection(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: context.colors.border, width: 0.8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 3,
                height: 14,
                decoration: BoxDecoration(
                  color: context.colors.accentWork,
                  borderRadius: BorderRadius.circular(1.5),
                ),
              ),
              const SizedBox(width: 8),
              Text(
                'PURPOSE · 목적',
                style: TextStyle(
                  fontSize: 11.5,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 1.0,
                  color: context.colors.accentWork,
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Text(
            '우리는 삶을 깊이 이해하고,\n사람이 머물고 일하고 쉬는 모든 순간에\n감성과 품격을 담은 공간으로\n사람과 도시의 가치를 높인다.',
            style: AppTextStyles.titleMd.copyWith(
              fontWeight: FontWeight.w600,
              color: context.colors.textPrimary,
              height: 1.65,
              letterSpacing: -0.3,
            ),
          ),
        ],
      ),
    );
  }

  // ── 1-2. 사명 (Mission 2035) ───────────────────────────────────────────
  Widget _buildMissionSection(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: context.colors.border, width: 0.8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 3,
                height: 14,
                decoration: BoxDecoration(
                  color: context.colors.accentCorp,
                  borderRadius: BorderRadius.circular(1.5),
                ),
              ),
              const SizedBox(width: 8),
              Text(
                'MISSION (BHAG) · 사명',
                style: TextStyle(
                  fontSize: 11.5,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 1.0,
                  color: context.colors.accentCorp,
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Text(
            '2035년,\n고객과 파트너가 가장 먼저 찾는 이름이 된다.',
            style: AppTextStyles.titleMd.copyWith(
              fontWeight: FontWeight.w700,
              color: context.colors.textPrimary,
              height: 1.5,
              letterSpacing: -0.3,
            ),
          ),
        ],
      ),
    );
  }

  // ── 2. 핵심 가치관 (Core Values & Beliefs) ───────────────────────────
  Widget _buildCoreValuesSection(BuildContext context) {
    final values = [
      {
        'no': '01',
        'title': '존중',
        'sub': 'Human Experience First',
        'headline': '인간의 삶이 모든 판단의 기준이다.',
        'desc':
            '공간은 삶을 담는 그릇이다.\n우리는 설계의 첫 줄부터 입주 후 일상까지, 고객, 파트너, 구성원의 경험과 존엄을 모든 결정의 출발점으로 삼는다.',
        'quote': null,
      },
      {
        'no': '02',
        'title': '혁신',
        'sub': 'Challenge & Innovation',
        'headline': '우리는 익숙한 기준에 끊임없이 질문한다.',
        'desc':
            '좋은 공간은 시대마다 다시 정의되어야 한다.\n공간뿐 아니라, 일하는 방식과 의사결정 과정도 고객에게 전달되는 가치다.\n\n우리는 공간과 일하는 방식을 지속적으로 검토하며, 더 나은 기준을 직접 만든다.',
        'quote': '더 나은 방식으로 일하는 조직이 더 좋은 공간을 만든다.',
      },
      {
        'no': '03',
        'title': '미래가치',
        'sub': 'Legacy & Sustainability',
        'headline': '우리는 오늘을 짓지만, 내일을 생각한다.',
        'desc':
            '완공은 끝이 아니라 시작이다.\n우리는 시간이 흘러도 다음 세대에게 가치 있는 커뮤니티와 도시를 남긴다.\n눈앞의 성과보다 시간이 증명하는 가치를 택한다.',
        'quote': null,
      },
      {
        'no': '04',
        'title': '신뢰',
        'sub': 'Trust & Accountability',
        'headline': '신뢰는 말이 아니라 결과로 증명된다.',
        'desc':
            '우리는 계약서의 문장 하나, 준공일 하루도 가볍게 여기지 않는다.\n고객과 사회에 한 약속은 어떤 상황에서도 끝까지 책임지고 이행한다.',
        'quote': null,
      },
      {
        'no': '05',
        'title': '품격',
        'sub': 'Design Excellence',
        'headline': '아름다움은 선택이 아니라 기준이다.',
        'desc':
            '기능을 갖추는 것은 최소한이다.\n우리는 설계, 시공, 디테일의 모든 과정에서 타협하지 않는 원칙을 적용한다.\n설명하지 않아도 차이가 느껴지는 수준을 완성도의 척도로 삼는다.',
        'quote': null,
      },
    ];

    return Container(
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: context.colors.border, width: 0.8),
      ),
      child: Column(
        children: List.generate(values.length, (idx) {
          final v = values[idx];
          final isLast = idx == values.length - 1;
          final quote = v['quote'];

          return Column(
            children: [
              Padding(
                padding: const EdgeInsets.all(22),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.baseline,
                      textBaseline: TextBaseline.alphabetic,
                      children: [
                        Text(
                          v['no']!,
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w800,
                            color: context.colors.accentWork,
                            letterSpacing: 0.8,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          v['title']!,
                          style: AppTextStyles.titleSm.copyWith(
                            fontWeight: FontWeight.bold,
                            color: context.colors.textPrimary,
                          ),
                        ),
                        const SizedBox(width: 6),
                        Text(
                          '· ${v['sub']!}',
                          style: TextStyle(
                            fontSize: 11.5,
                            fontWeight: FontWeight.w500,
                            color: context.colors.textMuted,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Text(
                      v['headline']!,
                      style: AppTextStyles.bodyMd.copyWith(
                        fontWeight: FontWeight.bold,
                        color: context.colors.textPrimary,
                        height: 1.35,
                      ),
                    ),
                    const SizedBox(height: 10),
                    Text(
                      v['desc']!,
                      style: AppTextStyles.bodySecond.copyWith(
                        color: context.colors.textSecond,
                        height: 1.6,
                        letterSpacing: -0.1,
                      ),
                    ),
                    if (quote != null) ...[
                      const SizedBox(height: 14),
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.symmetric(
                            horizontal: 14, vertical: 10),
                        decoration: BoxDecoration(
                          color: context.colors.bgSurface,
                          border: Border(
                            left: BorderSide(
                              color: context.colors.textDisabled,
                              width: 2.5,
                            ),
                          ),
                        ),
                        child: Text(
                          '“$quote”',
                          style: TextStyle(
                            fontSize: 12.5,
                            color: context.colors.textSecond,
                            fontStyle: FontStyle.italic,
                            height: 1.4,
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              if (!isLast) Divider(color: context.colors.border, height: 1),
            ],
          );
        }),
      ),
    );
  }

  // ── 3. 조직도 및 주요 부서 ──────────────────────────────────────────
  Widget _buildOrganizationSection(BuildContext context) {
    final depts = [
      {'name': '대표이사실', 'role': '총괄 경영, 비전 수립 및 미래 전략 지휘', 'badge': '경영총괄'},
      {'name': '부동산개발사업본부', 'role': '신규 사업지 발굴, 사업 타당성 검토, 시행 인허가', 'badge': '시행/개발'},
      {'name': '건설사업본부', 'role': '현장 시공 관리, 공정·품질·안전 총괄 관리', 'badge': '현장/기술'},
      {'name': '분양·마케팅팀', 'role': '분양 계약, 고객 수납, 계약자 관리 및 마케팅', 'badge': '영업/수납'},
      {'name': '경영지원본부', 'role': '자금 조달, 세무회계, 인사·총무 및 사내 복지', 'badge': '본사관리'},
    ];

    return Container(
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: context.colors.border, width: 0.8),
      ),
      child: Column(
        children: List.generate(depts.length, (idx) {
          final d = depts[idx];
          final isLast = idx == depts.length - 1;

          return Column(
            children: [
              Padding(
                padding:
                    const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
                child: Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            d['name']!,
                            style: AppTextStyles.bodyMd.copyWith(
                              fontWeight: FontWeight.w600,
                              color: context.colors.textPrimary,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            d['role']!,
                            style: AppTextStyles.caption.copyWith(
                              color: context.colors.textMuted,
                            ),
                          ),
                        ],
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: context.colors.bgSurface,
                        borderRadius: BorderRadius.circular(4),
                        border:
                            Border.all(color: context.colors.border, width: 0.6),
                      ),
                      child: Text(
                        d['badge']!,
                        style: AppTextStyles.caption.copyWith(
                          color: context.colors.textSecond,
                          fontSize: 11,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              if (!isLast) Divider(color: context.colors.border, height: 1),
            ],
          );
        }),
      ),
    );
  }

  // ── 4. 사내 공식 규정집 ──────────────────────────────────────────────
  Widget _buildRegulationsSection(BuildContext context) {
    final rules = [
      {'title': '취업규칙 및 복무규정', 'date': '2026.01.01 개정', 'ver': 'v3.2'},
      {'title': '인사관리 및 평가 지침', 'date': '2025.12.15 개정', 'ver': 'v2.1'},
      {'title': '여비교통비 및 경비정산 규정', 'date': '2026.02.01 개정', 'ver': 'v4.0'},
      {'title': '경조사 및 복리후생 지원 기준', 'date': '2025.07.01 개정', 'ver': 'v2.0'},
      {'title': '정보보안 및 영업비밀 관리수칙', 'date': '2026.03.10 개정', 'ver': 'v1.5'},
    ];

    return Container(
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: context.colors.border, width: 0.8),
      ),
      child: Column(
        children: List.generate(rules.length, (idx) {
          final r = rules[idx];
          final isLast = idx == rules.length - 1;

          return Column(
            children: [
              ListTile(
                contentPadding:
                    const EdgeInsets.symmetric(horizontal: 18, vertical: 2),
                title: Text(
                  r['title']!,
                  style: AppTextStyles.bodyMd.copyWith(
                    fontWeight: FontWeight.w500,
                    color: context.colors.textPrimary,
                  ),
                ),
                subtitle: Text(
                  '${r['date']} · ${r['ver']}',
                  style: AppTextStyles.caption
                      .copyWith(color: context.colors.textMuted),
                ),
                trailing: const Icon(Icons.chevron_right_rounded,
                    size: 18, color: Colors.grey),
                onTap: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content:
                          Text('${r['title']} 규정 문서를 불러옵니다 (공용문서 연동)'),
                      duration: const Duration(seconds: 1),
                    ),
                  );
                },
              ),
              if (!isLast) Divider(color: context.colors.border, height: 1),
            ],
          );
        }),
      ),
    );
  }

  // ── 5. 온보딩 & 업무 가이드 ──────────────────────────────────────────
  Widget _buildOnboardingSection(BuildContext context) {
    final guides = [
      {
        'title': '🏢 워크스페이스 선택 및 공간 전환',
        'desc': '본사관리, 프로젝트, 현장 등 원하는 공간으로 1초 만에 전환하는 방법',
      },
      {
        'title': '📅 회의록 작성 및 액션아이템 자동 업무 연동',
        'desc': '의제·결정사항 기록 후 담당자에게 업무(Issue)를 즉시 할당하는 방법',
      },
      {
        'title': '📋 내 업무 진척률(0~100%) 관리 및 댓글 피드백',
        'desc': '할당된 업무의 상태를 실시간 변경하고 사진 및 첨부파일 등록하기',
      },
    ];

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: context.colors.border, width: 0.8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.flight_takeoff_rounded,
                  color: context.colors.accentProject, size: 20),
              const SizedBox(width: 8),
              Text(
                '신입사원 온보딩 4단계 로드맵',
                style: AppTextStyles.bodyMd.copyWith(
                  fontWeight: FontWeight.bold,
                  color: context.colors.textPrimary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            '1일차(계정세팅) ➔ 1주차(동료인사) ➔ 2주차(시스템학습) ➔ 1개월(실전투입)',
            style: AppTextStyles.caption.copyWith(
              color: context.colors.textMuted,
              height: 1.4,
            ),
          ),
          const SizedBox(height: 16),
          Divider(color: context.colors.border, height: 1),
          const SizedBox(height: 14),
          Text(
            '💻 IBS 핵심 시스템 가이드',
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.bold,
              color: context.colors.accentWork,
            ),
          ),
          const SizedBox(height: 8),
          ...guides.map((g) => Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(Icons.check_circle_outline_rounded,
                        size: 16, color: Colors.teal),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        '${g['title']!}\n${g['desc']!}',
                        style: AppTextStyles.caption.copyWith(
                          color: context.colors.textSecond,
                          height: 1.35,
                        ),
                      ),
                    ),
                  ],
                ),
              )),
        ],
      ),
    );
  }

  // ── 6. 자주 묻는 질문 (FAQ) ─────────────────────────────────────────
  Widget _buildFaqSection(
      BuildContext context, List<Map<String, String>> filteredFaqs) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // 카테고리 필터
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Row(
            children: List.generate(_faqCategories.length, (idx) {
              final isSelected = _faqCategoryIndex == idx;
              return Padding(
                padding: const EdgeInsets.only(right: 6, bottom: 10),
                child: ChoiceChip(
                  label: Text(_faqCategories[idx]),
                  selected: isSelected,
                  onSelected: (_) => setState(() => _faqCategoryIndex = idx),
                  selectedColor: context.colors.textPrimary,
                  backgroundColor: context.colors.bgSurface,
                  labelStyle: TextStyle(
                    color: isSelected
                        ? context.colors.bgPrimary
                        : context.colors.textSecond,
                    fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                    fontSize: 12,
                  ),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                    side: BorderSide(
                      color: isSelected
                          ? context.colors.textPrimary
                          : context.colors.border,
                      width: 0.8,
                    ),
                  ),
                  showCheckmark: false,
                  padding:
                      const EdgeInsets.symmetric(horizontal: 6, vertical: 0),
                ),
              );
            }),
          ),
        ),

        // 아코디언 목록
        ...filteredFaqs.map((faq) => Container(
              margin: const EdgeInsets.only(bottom: 8),
              decoration: BoxDecoration(
                color: context.colors.bgCard,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: context.colors.border, width: 0.8),
              ),
              child: Theme(
                data: Theme.of(context)
                    .copyWith(dividerColor: Colors.transparent),
                child: ExpansionTile(
                  tilePadding:
                      const EdgeInsets.symmetric(horizontal: 14, vertical: 2),
                  childrenPadding: const EdgeInsets.fromLTRB(14, 0, 14, 14),
                  leading: Text(
                    'Q',
                    style: TextStyle(
                      color: context.colors.accentApproval,
                      fontWeight: FontWeight.bold,
                      fontSize: 14,
                    ),
                  ),
                  title: Text(
                    faq['q']!,
                    style: AppTextStyles.bodyMd.copyWith(
                      fontWeight: FontWeight.w600,
                      color: context.colors.textPrimary,
                    ),
                  ),
                  children: [
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: context.colors.bgSurface,
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        faq['a']!,
                        style: AppTextStyles.bodySecond.copyWith(
                          color: context.colors.textSecond,
                          height: 1.45,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            )),
      ],
    );
  }
}
