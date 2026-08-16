import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/theme/app_colors_extension.dart';

/// 회사 소개 / 기업 철학 / 핵심 가치관 / 조직도 / 사내규정
/// ── 하이엔드 럭셔리 브랜드 캠페인 & 모던 에디토리얼 레이아웃
class CompanyIntroTabView extends ConsumerStatefulWidget {
  const CompanyIntroTabView({super.key});

  @override
  ConsumerState<CompanyIntroTabView> createState() =>
      _CompanyIntroTabViewState();
}

class _CompanyIntroTabViewState extends ConsumerState<CompanyIntroTabView> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: context.colors.bgPrimary,
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 26, vertical: 36),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── 🌟 HERO MANIFESTO (목적) ─────────────────────────────────
            _buildHeroManifesto(context),
            const SizedBox(height: 52),

            // ── 🎯 BHAG 2035 (사명) ──────────────────────────────────────
            _buildMissionHero(context),
            const SizedBox(height: 64),

            // ── 💎 5대 핵심 가치관 캠페인 ──────────────────────────────
            _buildCoreValuesCampaign(context),
            const SizedBox(height: 64),

            // ── 👥 조직도 & 부서 ────────────────────────────────────────
            _buildOrganizationSection(context),
            const SizedBox(height: 56),

            // ── 📜 사내 공식 규정집 ─────────────────────────────────────
            _buildRegulationsSection(context),
            const SizedBox(height: 48),
          ],
        ),
      ),
    );
  }

  // 🌟 [1] HERO MANIFESTO (목적 — 정통 철학 전문과 시각적 클라이맥스)
  Widget _buildHeroManifesto(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Container(
              width: 16,
              height: 2,
              color: context.colors.accentCorp,
            ),
            const SizedBox(width: 8),
            Text(
              'PURPOSE',
              style: TextStyle(
                fontSize: 10.5,
                fontWeight: FontWeight.w800,
                letterSpacing: 2.8,
                color: context.colors.accentCorp,
              ),
            ),
          ],
        ),
        const SizedBox(height: 20),
        Text(
          '우리는 삶을 깊이 이해하고,\n사람이 머물고 일하고 쉬는 모든 순간에\n감성과 품격을 담은 공간으로,',
          style: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w400,
            height: 1.75,
            letterSpacing: -0.3,
            color: context.colors.textSecond,
          ),
        ),
        const SizedBox(height: 10),
        Text(
          '사람과 도시의 가치를 높인다.',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.w800,
            letterSpacing: -0.6,
            height: 1.8,
            color: context.colors.textPrimary,
          ),
        ),
      ],
    );
  }

  // 🎯 [2] BHAG 2035 (사명 — 강렬한 볼드 광고 카피)
  Widget _buildMissionHero(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 22),
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(
          color: context.colors.border.withAlpha(120),
          width: 0.8,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(
                'MISSION 2035',
                style: TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 2.4,
                  color: context.colors.accentCorp,
                ),
              ),
              const Spacer(),
              Text(
                'BHAG',
                style: TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 1.2,
                  color: context.colors.textDisabled,
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Text(
            '2035년,\n고객과 파트너가\n가장 먼저 찾는 이름이 된다.',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w800,
              height: 1.45,
              letterSpacing: -0.5,
              color: context.colors.textPrimary,
            ),
          ),
        ],
      ),
    );
  }

  // 💎 [3] 5대 핵심 가치관 (광고 캠페인 에디토리얼 모노그래프)
  Widget _buildCoreValuesCampaign(BuildContext context) {
    final values = [
      {
        'no': '01',
        'en': 'RESPECT',
        'sub': 'Human Experience First',
        'title': '존중',
        'copy': '인간의 삶이 모든 판단의 기준이다.',
        'desc':
            '공간은 삶을 담는 그릇이다. \n우리는 설계의 첫 줄부터 입주 후 일상까지, \n고객, 파트너, 구성원의 경험과 존엄을 모든 결정의 출발점으로 삼는다.',
        'quote': null,
      },
      {
        'no': '02',
        'en': 'INNOVATION',
        'sub': 'Challenge & Innovation',
        'title': '혁신',
        'copy': '우리는 익숙한 기준에 끊임없이 질문한다.',
        'desc':
            '좋은 공간은 시대마다 다시 정의되어야 한다. \n공간뿐 아니라, 일하는 방식과 의사결정 과정도 고객에게 전달되는 가치다.\n\n우리는 공간과 일하는 방식을 지속적으로 검토하며, 더 나은 기준을 직접 만든다.',
        'quote': '더 나은 방식으로 일하는 조직이 더 좋은 공간을 만든다.',
      },
      {
        'no': '03',
        'en': 'LEGACY',
        'sub': 'Legacy & Sustainability',
        'title': '미래가치',
        'copy': '우리는 오늘을 짓지만, 내일을 생각한다.',
        'desc':
            '완공은 끝이 아니라 시작이다. \n우리는 시간이 흘러도 다음 세대에게 가치 있는 커뮤니티와 도시를 남긴다. \n눈앞의 성과보다 시간이 증명하는 가치를 택한다.',
        'quote': null,
      },
      {
        'no': '04',
        'en': 'TRUST',
        'sub': 'Trust & Accountability',
        'title': '신뢰',
        'copy': '신뢰는 말이 아니라 결과로 증명된다.',
        'desc':
            '우리는 계약서의 문장 하나, 준공일 하루도 가볍게 여기지 않는다. \n고객과 사회에 한 약속은 어떤 상황에서도 끝까지 책임지고 이행한다.',
        'quote': null,
      },
      {
        'no': '05',
        'en': 'EXCELLENCE',
        'sub': 'Design Excellence',
        'title': '품격',
        'copy': '아름다움은 선택이 아니라 기준이다.',
        'desc':
            '기능을 갖추는 것은 최소한이다. \n우리는 설계, 시공, 디테일의 모든 과정에서 타협하지 않는 원칙을 적용한다. \n설명하지 않아도 차이가 느껴지는 수준을 완성도의 척도로 삼는다.',
        'quote': null,
      },
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Container(
              width: 16,
              height: 2,
              color: context.colors.accentCorp,
            ),
            const SizedBox(width: 8),
            Text(
              'CORE VALUES',
              style: TextStyle(
                fontSize: 10.5,
                fontWeight: FontWeight.w800,
                letterSpacing: 2.8,
                color: context.colors.accentCorp,
              ),
            ),
          ],
        ),
        const SizedBox(height: 28),
        ...List.generate(values.length, (idx) {
          final v = values[idx];
          final isLast = idx == values.length - 1;
          final quote = v['quote'];

          return Padding(
            padding: const EdgeInsets.only(bottom: 40),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 1. 넘버링 & 영문 태그 (초극세사 하이엔드 라벨)
                Row(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    Text(
                      v['no']!,
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 1.0,
                        color: context.colors.accentCorp,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      '·  ${v['en']!}  ·  ${v['title']!}',
                      style: TextStyle(
                        fontSize: 11.5,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 1.2,
                        color: context.colors.textMuted,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),

                // 2. 대담한 브랜드 헤드 카피 (Hero Headline)
                Text(
                  v['copy']!,
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w800,
                    height: 1.4,
                    letterSpacing: -0.4,
                    color: context.colors.textPrimary,
                  ),
                ),
                const SizedBox(height: 10),

                // 3. 정제된 서브 카피 본문
                Text(
                  v['desc']!,
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w400,
                    height: 1.7,
                    letterSpacing: -0.15,
                    color: context.colors.textSecond,
                  ),
                ),

                // 4. 인용구 풀쿼트 (Pull-Quote)
                if (quote != null) ...[
                  const SizedBox(height: 14),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(
                        horizontal: 14, vertical: 10),
                    decoration: BoxDecoration(
                      color: context.colors.bgCard,
                      borderRadius: const BorderRadius.only(
                        topRight: Radius.circular(6),
                        bottomRight: Radius.circular(6),
                      ),
                      border: Border(
                        left: BorderSide(
                          color: context.colors.accentCorp,
                          width: 2.0,
                        ),
                      ),
                    ),
                    child: Text(
                      '“$quote”',
                      style: TextStyle(
                        fontSize: 12,
                        color: context.colors.textSecond,
                        fontStyle: FontStyle.italic,
                        height: 1.45,
                      ),
                    ),
                  ),
                ],

                if (!isLast) ...[
                  const SizedBox(height: 36),
                  Divider(
                    color: context.colors.border.withAlpha(80),
                    height: 1,
                  ),
                ],
              ],
            ),
          );
        }),
      ],
    );
  }

  // 👥 [4] 조직도 및 부서
  Widget _buildOrganizationSection(BuildContext context) {
    final depts = [
      {'name': '대표이사실', 'role': '총괄 경영 및 미래 전략 지휘', 'badge': '경영총괄'},
      {'name': '사업개발본부', 'role': '신규 사업지 발굴 및 시행 인허가', 'badge': '기획/전략'},
      {'name': '사업운영본부', 'role': '현장, PMO, 운영·데이터·지원 총괄', 'badge': '시행/운영'},
      {'name': '분양·마케팅팀', 'role': '분양 계약, 고객·상품·프로세스 관리', 'badge': '영업/전략'},
      {'name': '경영지원본부', 'role': '자금, 세무회계, 인사·총무, IT지원', 'badge': '본사관리'},
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Container(
              width: 16,
              height: 2,
              color: context.colors.accentCorp,
            ),
            const SizedBox(width: 8),
            Text(
              'ORGANIZATION',
              style: TextStyle(
                fontSize: 10.5,
                fontWeight: FontWeight.w800,
                letterSpacing: 2.8,
                color: context.colors.accentCorp,
              ),
            ),
          ],
        ),
        const SizedBox(height: 18),
        Container(
          decoration: BoxDecoration(
            color: context.colors.bgCard,
            borderRadius: BorderRadius.circular(10),
            border: Border.all(
              color: context.colors.border.withAlpha(120),
              width: 0.8,
            ),
          ),
          child: Column(
            children: List.generate(depts.length, (idx) {
              final d = depts[idx];
              final isLast = idx == depts.length - 1;

              return Column(
                children: [
                  Padding(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 18, vertical: 14),
                    child: Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                d['name']!,
                                style: TextStyle(
                                  fontSize: 13.5,
                                  fontWeight: FontWeight.w600,
                                  letterSpacing: -0.2,
                                  color: context.colors.textPrimary,
                                ),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                d['role']!,
                                style: TextStyle(
                                  fontSize: 11.5,
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
                            border: Border.all(
                                color: context.colors.border, width: 0.6),
                          ),
                          child: Text(
                            d['badge']!,
                            style: TextStyle(
                              fontSize: 10.5,
                              fontWeight: FontWeight.w600,
                              color: context.colors.textSecond,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  if (!isLast)
                    Divider(
                      color: context.colors.border.withAlpha(80),
                      height: 1,
                    ),
                ],
              );
            }),
          ),
        ),
      ],
    );
  }

  // 📜 [5] 사내 공식 규정집
  Widget _buildRegulationsSection(BuildContext context) {
    final rules = [
      {'title': '취업규칙 및 복무규정', 'date': '2026.01.01 개정', 'ver': 'v3.2'},
      {'title': '인사관리 및 평가 지침', 'date': '2025.12.15 개정', 'ver': 'v2.1'},
      {'title': '여비교통비 및 경비정산 규정', 'date': '2026.02.01 개정', 'ver': 'v4.0'},
      {'title': '경조사 및 복리후생 지원 기준', 'date': '2025.07.01 개정', 'ver': 'v2.0'},
      {'title': '정보보안 및 영업비밀 관리수칙', 'date': '2026.03.10 개정', 'ver': 'v1.5'},
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Container(
              width: 16,
              height: 2,
              color: context.colors.accentCorp,
            ),
            const SizedBox(width: 8),
            Text(
              'REGULATIONS',
              style: TextStyle(
                fontSize: 10.5,
                fontWeight: FontWeight.w800,
                letterSpacing: 2.8,
                color: context.colors.accentCorp,
              ),
            ),
          ],
        ),
        const SizedBox(height: 18),
        Container(
          decoration: BoxDecoration(
            color: context.colors.bgCard,
            borderRadius: BorderRadius.circular(10),
            border: Border.all(
              color: context.colors.border.withAlpha(120),
              width: 0.8,
            ),
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
                      style: TextStyle(
                        fontSize: 13.5,
                        fontWeight: FontWeight.w500,
                        letterSpacing: -0.2,
                        color: context.colors.textPrimary,
                      ),
                    ),
                    subtitle: Text(
                      '${r['date']} · ${r['ver']}',
                      style: TextStyle(
                        fontSize: 11,
                        color: context.colors.textMuted,
                      ),
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
                  if (!isLast)
                    Divider(
                      color: context.colors.border.withAlpha(80),
                      height: 1,
                    ),
                ],
              );
            }),
          ),
        ),
      ],
    );
  }
}
