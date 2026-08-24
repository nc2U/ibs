import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/theme/app_colors_extension.dart';
import 'company_intro_tab_view.dart';
import 'faq_support_tab_view.dart';
import 'onboarding_tab_view.dart';

/// 전사 라운지 & 온보딩 메인 뷰 (Corporate Lounge & Onboarding Hub)
/// ── 상단 경량 캡슐 칩(Pill Chips)으로 회사소개 / 온보딩 가이드 / FAQ 3개 서브 탭을 쾌적하게 전환
class CorporateLoungeView extends ConsumerStatefulWidget {
  final int initialSubIndex;
  const CorporateLoungeView({
    super.key,
    this.initialSubIndex = 0,
  });

  @override
  ConsumerState<CorporateLoungeView> createState() =>
      _CorporateLoungeViewState();
}

class _CorporateLoungeViewState extends ConsumerState<CorporateLoungeView> {
  late int _selectedSubIndex;

  @override
  void initState() {
    super.initState();
    _selectedSubIndex =
        (widget.initialSubIndex >= 0 && widget.initialSubIndex < 3)
            ? widget.initialSubIndex
            : 0;
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // ── 1. 슬림 & 세련된 경량 캡슐 칩 네비게이션 ─────────────────────────
        Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          decoration: BoxDecoration(
            color: context.colors.bgCard,
            border: Border(
              bottom: BorderSide(color: context.colors.border, width: 0.8),
            ),
          ),
          child: SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: [
                _buildChip(
                  index: 0,
                  label: '회사소개',
                  icon: Icons.business_outlined,
                  activeColor: context.colors.accentCorp,
                ),
                const SizedBox(width: 8),
                _buildChip(
                  index: 1,
                  label: '온보딩·가이드',
                  icon: Icons.school_outlined,
                  activeColor: context.colors.accentProject,
                ),
                const SizedBox(width: 8),
                _buildChip(
                  index: 2,
                  label: 'FAQ·기술지원',
                  icon: Icons.help_outline_rounded,
                  activeColor: context.colors.accentTech,
                ),
              ],
            ),
          ),
        ),

        // ── 2. 서브 탭 본문 (IndexedStack으로 스크롤 위치 및 상태 보존) ─────
        Expanded(
          child: IndexedStack(
            index: _selectedSubIndex,
            children: const [
              CompanyIntroTabView(),
              OnboardingTabView(),
              FaqSupportTabView(),
            ],
          ),
        ),
      ],
    );
  }

  // 🎨 경량 캡슐 칩 위젯
  Widget _buildChip({
    required int index,
    required String label,
    required IconData icon,
    required Color activeColor,
  }) {
    final isSelected = _selectedSubIndex == index;
    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTap: () {
        if (_selectedSubIndex != index) {
          setState(() => _selectedSubIndex = index);
        }
      },
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 7),
        decoration: BoxDecoration(
          color: isSelected
              ? activeColor.withAlpha(25)
              : context.colors.bgSurface,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: isSelected ? activeColor : context.colors.border,
            width: isSelected ? 1.4 : 0.8,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              size: 15,
              color: isSelected ? activeColor : context.colors.textMuted,
            ),
            const SizedBox(width: 6),
            Text(
              label,
              style: TextStyle(
                fontSize: 12.5,
                fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
                color: isSelected ? activeColor : context.colors.textMuted,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
