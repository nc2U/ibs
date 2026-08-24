import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';

/// 신입사원 FAQ (아코디언) & 기술지원 탭 뷰 (목데이터)
class FaqSupportTabView extends ConsumerStatefulWidget {
  const FaqSupportTabView({super.key});

  @override
  ConsumerState<FaqSupportTabView> createState() => _FaqSupportTabViewState();
}

class _FaqSupportTabViewState extends ConsumerState<FaqSupportTabView> {
  int _selectedCategory = 0;
  final _categories = ['전체 FAQ', '인사·근태', '전산·계정', '경비·복지', '🛠️ 기술지원'];

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
      'a': '새로 배속된 현장이나 프로젝트는 해당 워크스페이스의 [업무관리자] 또는 [경영지원본부 전산담당자]에게 권한 승인 요청(사내 메신저 또는 하단 IT 기술지원 문의)을 남겨주시면 즉시 추가됩니다.',
    },
    {
      'cat': '전산·계정',
      'q': '비밀번호를 분실했거나 계정이 잠겼을 때는 어떻게 하나요?',
      'a': '로그인 화면의 [비밀번호 찾기]를 통해 등록된 사내 이메일로 임시 링크를 수신하시거나, 전산 관리자(내선 104번)에게 초기화를 요청하세요.',
    },
    {
      'cat': '경비·복지',
      'q': '식대 및 야근 교통비 영수증 정산 기한은 언제인가요?',
      'a': '매월 1일부터 말일까지 사용한 법인카드 및 개인 경비는 익월 5일까지 [지출결의서]를 작성하고 법인카드 영수증 또는 전자세금계산서를 첨부하여 결재를 올려주셔야 당월 급여일에 지급됩니다.',
    },
    {
      'cat': '경비·복지',
      'q': '명절 귀향비 및 경조사비 지급 기준은 어디서 보나요?',
      'a': '[회사소개 > 사내규정집] 내 [경조사 및 복리후생 지원 기준] 문서를 참고하시거나 담당 총무팀으로 문의하시면 됩니다.',
    },
  ];

  @override
  Widget build(BuildContext context) {
    final filteredFaqs = _selectedCategory == 0
        ? _faqList
        : _selectedCategory == 4
            ? <Map<String, String>>[]
            : _faqList
                .where((f) => f['cat'] == _categories[_selectedCategory])
                .toList();

    return Scaffold(
      backgroundColor: context.colors.bgPrimary,
      body: CustomScrollView(
        slivers: [
          // ── 1. 상단 카테고리 필터 칩 ──────────────────────────────────
          SliverToBoxAdapter(
            child: Container(
              color: context.colors.bgCard,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              child: SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: List.generate(_categories.length, (idx) {
                    final isSelected = _selectedCategory == idx;
                    return Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: ChoiceChip(
                        label: Text(_categories[idx]),
                        selected: isSelected,
                        onSelected: (_) =>
                            setState(() => _selectedCategory = idx),
                        selectedColor: context.colors.accentTech,
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
                                ? context.colors.accentTech
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
                if (_selectedCategory == 4) ...[
                  // 🛠️ 기술지원 / IT 헬프데스크 전용 폼 & 안내
                  _buildTechSupportSection(context),
                ] else ...[
                  // ❓ FAQ 아코디언 리스트
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        '신입사원 자주 묻는 질문 (FAQ)',
                        style: AppTextStyles.titleMd.copyWith(
                          fontWeight: FontWeight.bold,
                          color: context.colors.textPrimary,
                        ),
                      ),
                      Text(
                        '총 ${filteredFaqs.length}건',
                        style: AppTextStyles.caption
                            .copyWith(color: context.colors.textMuted),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  ...filteredFaqs.map((faq) => Container(
                        margin: const EdgeInsets.only(bottom: 8),
                        decoration: BoxDecoration(
                          color: context.colors.bgCard,
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(
                              color: context.colors.border, width: 0.8),
                        ),
                        child: Theme(
                          data: Theme.of(context)
                              .copyWith(dividerColor: Colors.transparent),
                          child: ExpansionTile(
                            tilePadding: const EdgeInsets.symmetric(
                                horizontal: 14, vertical: 2),
                            childrenPadding: const EdgeInsets.fromLTRB(14, 0, 14, 14),
                            leading: Container(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(
                                color: context.colors.accentTech
                                    .withAlpha(30),
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: Text(
                                'Q',
                                style: TextStyle(
                                  color: context.colors.accentTech,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 13,
                                ),
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
                  const SizedBox(height: 24),
                  // 하단 헬프데스크 바로가기 배너
                  _buildHelpBanner(context),
                  const SizedBox(height: 32),
                ],
              ]),
            ),
          ),
        ],
      ),
    );
  }

  // 🛠️ 기술지원 / IT 헬프데스크
  Widget _buildTechSupportSection(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: context.colors.bgCard,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: context.colors.border, width: 0.8),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Icon(Icons.support_agent_rounded,
                      color: Colors.deepOrangeAccent, size: 24),
                  const SizedBox(width: 8),
                  Text(
                    'IT 기술지원 & 전산 문의 접수',
                    style: AppTextStyles.titleSm.copyWith(
                      fontWeight: FontWeight.bold,
                      color: context.colors.textPrimary,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                'IBS 시스템 오류, 권한 요청, 사내 네트워크 및 PC 장비 관련 문의를 남겨주시면 전산팀에서 신속하게 처리해 드립니다.',
                style: AppTextStyles.caption.copyWith(
                  color: context.colors.textMuted,
                  height: 1.35,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        Text(
          '문의 작성하기 (게시판 연동)',
          style: AppTextStyles.titleMd.copyWith(
            fontWeight: FontWeight.bold,
            color: context.colors.textPrimary,
          ),
        ),
        const SizedBox(height: 10),
        TextField(
          decoration: InputDecoration(
            hintText: '문의 제목을 입력하세요 (예: 00현장 워크스페이스 권한 요청)',
            filled: true,
            fillColor: context.colors.bgCard,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: BorderSide(color: context.colors.border),
            ),
            contentPadding:
                const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          ),
        ),
        const SizedBox(height: 10),
        TextField(
          maxLines: 4,
          decoration: InputDecoration(
            hintText: '상세 문의 내용 및 발생 화면을 구체적으로 적어주세요.',
            filled: true,
            fillColor: context.colors.bgCard,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: BorderSide(color: context.colors.border),
            ),
            contentPadding: const EdgeInsets.all(14),
          ),
        ),
        const SizedBox(height: 12),
        SizedBox(
          width: double.infinity,
          height: 44,
          child: ElevatedButton.icon(
            style: ElevatedButton.styleFrom(
              backgroundColor: context.colors.accentTech,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(8)),
            ),
            onPressed: () {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('기술지원 문의가 등록되었습니다 (전산팀 접수 완료).'),
                  duration: Duration(seconds: 2),
                ),
              );
            },
            icon: const Icon(Icons.send_rounded, size: 18),
            label: const Text('문의 등록하기',
                style: TextStyle(fontWeight: FontWeight.bold)),
          ),
        ),
        const SizedBox(height: 32),
      ],
    );
  }

  // 💬 하단 배너
  Widget _buildHelpBanner(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: context.colors.border, width: 0.8),
      ),
      child: Row(
        children: [
          const Icon(Icons.help_center_outlined,
              color: Colors.amber, size: 22),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '원하는 답변을 찾지 못하셨나요?',
                  style: AppTextStyles.bodyMd.copyWith(
                    fontWeight: FontWeight.w600,
                    color: context.colors.textPrimary,
                  ),
                ),
                Text(
                  'IT 기술지원 탭에서 직접 문의를 남기실 수 있습니다.',
                  style: AppTextStyles.caption
                      .copyWith(color: context.colors.textMuted),
                ),
              ],
            ),
          ),
          OutlinedButton(
            style: OutlinedButton.styleFrom(
              side: BorderSide(color: context.colors.accentTech),
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(6)),
            ),
            onPressed: () => setState(() => _selectedCategory = 4),
            child: Text('문의하기',
                style: TextStyle(
                    color: context.colors.accentTech,
                    fontWeight: FontWeight.bold,
                    fontSize: 12)),
          ),
        ],
      ),
    );
  }
}
