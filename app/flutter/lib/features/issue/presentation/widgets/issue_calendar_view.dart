import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/models/issue_model.dart';
import 'issue_card.dart';

/// 업무 월간 캘린더 뷰 위젯
/// - 상단 월 이동 네비게이터 (이전달, 이번달, 다음달)
/// - 월간 달력 그리드에 시작일~마감일 기준 업무 도트 및 인디케이터 표시
/// - 선택한 날짜의 업무 목록 하단 리스트로 즉시 표출 및 상세 화면 연결
class IssueCalendarView extends StatefulWidget {
  final List<IssueModel> issues;
  final ValueChanged<IssueModel> onIssueTap;
  final ValueChanged<IssueModel> onDoneRatioTap;

  const IssueCalendarView({
    super.key,
    required this.issues,
    required this.onIssueTap,
    required this.onDoneRatioTap,
  });

  @override
  State<IssueCalendarView> createState() => _IssueCalendarViewState();
}

class _IssueCalendarViewState extends State<IssueCalendarView> {
  late DateTime _focusedMonth;
  late DateTime _selectedDay;

  @override
  void initState() {
    super.initState();
    final now = DateTime.now();
    _focusedMonth = DateTime(now.year, now.month, 1);
    _selectedDay = DateTime(now.year, now.month, now.day);
  }

  void _prevMonth() {
    setState(() {
      _focusedMonth = DateTime(_focusedMonth.year, _focusedMonth.month - 1, 1);
    });
  }

  void _nextMonth() {
    setState(() {
      _focusedMonth = DateTime(_focusedMonth.year, _focusedMonth.month + 1, 1);
    });
  }

  void _goToday() {
    final now = DateTime.now();
    setState(() {
      _focusedMonth = DateTime(now.year, now.month, 1);
      _selectedDay = DateTime(now.year, now.month, now.day);
    });
  }

  /// 특정 일자에 걸쳐있는(시작일 <= targetDay <= 마감일) 업무 목록 추출
  List<IssueModel> _getIssuesForDay(DateTime day) {
    return widget.issues.where((issue) {
      final start = DateTime.tryParse(issue.startDate);
      final due = issue.dueDate != null ? DateTime.tryParse(issue.dueDate!) : null;

      if (start == null) return false;

      final sDay = DateTime(start.year, start.month, start.day);
      final eDay = due != null
          ? DateTime(due.year, due.month, due.day)
          : sDay;

      final tDay = DateTime(day.year, day.month, day.day);

      return (tDay.isAtSameMomentAs(sDay) || tDay.isAfter(sDay)) &&
          (tDay.isAtSameMomentAs(eDay) || tDay.isBefore(eDay));
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    final selectedIssues = _getIssuesForDay(_selectedDay);

    return Column(
      children: [
        // ── 상단 월 선택 헤더 ────────────────────────────────────────────────
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          decoration: BoxDecoration(
            color: context.colors.bgSurface,
            border: Border(
              bottom: BorderSide(color: context.colors.border, width: 0.8),
            ),
          ),
          child: Row(
            children: [
              IconButton(
                icon: const Icon(Icons.chevron_left_rounded, size: 22),
                color: context.colors.textPrimary,
                onPressed: _prevMonth,
                splashRadius: 18,
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
              ),
              const SizedBox(width: 4),
              Text(
                DateFormat('yyyy년 M월').format(_focusedMonth),
                style: AppTextStyles.titleSm.copyWith(
                  color: context.colors.textPrimary,
                  fontWeight: FontWeight.bold,
                  fontSize: 15,
                ),
              ),
              const SizedBox(width: 4),
              IconButton(
                icon: const Icon(Icons.chevron_right_rounded, size: 22),
                color: context.colors.textPrimary,
                onPressed: _nextMonth,
                splashRadius: 18,
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
              ),
              const Spacer(),
              InkWell(
                onTap: _goToday,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: context.colors.bgCard,
                    border: Border.all(color: context.colors.border, width: 0.8),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    '오늘',
                    style: AppTextStyles.caption.copyWith(
                      color: context.colors.accentWork,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),

        // ── 캘린더 그리드 ────────────────────────────────────────────────────
        Container(
          color: context.colors.bgCard,
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
          child: Column(
            children: [
              // 요일 행
              _buildWeekDaysHeader(context),
              const SizedBox(height: 4),
              // 일자 그리드
              _buildMonthGrid(context),
            ],
          ),
        ),

        Divider(color: context.colors.border, height: 1),

        // ── 선택된 날짜의 업무 목록 ───────────────────────────────────────────
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          color: context.colors.bgSurface,
          child: Row(
            children: [
              Icon(Icons.event_note_rounded, size: 14, color: context.colors.accentWork),
              const SizedBox(width: 6),
              Text(
                '${DateFormat('M월 d일 (E)', 'ko_KR').format(_selectedDay)} 업무 (${selectedIssues.length}건)',
                style: AppTextStyles.caption.copyWith(
                  color: context.colors.textPrimary,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
        ),
        Divider(color: context.colors.border, height: 1),

        Expanded(
          child: selectedIssues.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.event_available_outlined,
                          size: 36, color: context.colors.textMuted.withAlpha(120)),
                      const SizedBox(height: 8),
                      Text(
                        '해당 일자에 예정된 업무가 없습니다.',
                        style: AppTextStyles.bodySm.copyWith(
                          color: context.colors.textMuted,
                        ),
                      ),
                    ],
                  ),
                )
              : ListView.separated(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                  itemCount: selectedIssues.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 8),
                  itemBuilder: (context, index) {
                    final issue = selectedIssues[index];
                    return IssueCard(
                      issue: issue,
                      onTap: () => widget.onIssueTap(issue),
                      onDoneRatioTap: () => widget.onDoneRatioTap(issue),
                    );
                  },
                ),
        ),
      ],
    );
  }

  Widget _buildWeekDaysHeader(BuildContext context) {
    const weekDays = ['일', '월', '화', '수', '목', '금', '토'];
    return Row(
      children: List.generate(7, (i) {
        final isSun = i == 0;
        final isSat = i == 6;
        final color = isSun
            ? Colors.redAccent
            : (isSat ? Colors.blueAccent : context.colors.textMuted);

        return Expanded(
          child: Center(
            child: Text(
              weekDays[i],
              style: AppTextStyles.caption.copyWith(
                color: color,
                fontWeight: FontWeight.bold,
                fontSize: 11,
              ),
            ),
          ),
        );
      }),
    );
  }

  Widget _buildMonthGrid(BuildContext context) {
    final firstDayOfMonth = _focusedMonth;
    final startWeekday = firstDayOfMonth.weekday % 7; // 일요일=0
    final lastDayOfMonth = DateTime(_focusedMonth.year, _focusedMonth.month + 1, 0);
    final daysInMonth = lastDayOfMonth.day;

    final totalCells = ((startWeekday + daysInMonth) / 7).ceil() * 7;
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);

    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 7,
        childAspectRatio: 1.15,
      ),
      itemCount: totalCells,
      itemBuilder: (context, index) {
        final dayOffset = index - startWeekday + 1;
        if (dayOffset < 1 || dayOffset > daysInMonth) {
          return const SizedBox.shrink();
        }

        final currentDay = DateTime(_focusedMonth.year, _focusedMonth.month, dayOffset);
        final isSelected = currentDay.year == _selectedDay.year &&
            currentDay.month == _selectedDay.month &&
            currentDay.day == _selectedDay.day;
        final isToday = currentDay.year == today.year &&
            currentDay.month == today.month &&
            currentDay.day == today.day;

        final dayIssues = _getIssuesForDay(currentDay);
        final isSun = index % 7 == 0;
        final isSat = index % 7 == 6;

        return InkWell(
          onTap: () {
            setState(() {
              _selectedDay = currentDay;
            });
          },
          child: Container(
            margin: const EdgeInsets.all(2),
            decoration: BoxDecoration(
              color: isSelected
                  ? context.colors.accentWork.withAlpha(40)
                  : (isToday
                      ? context.colors.bgSurface
                      : Colors.transparent),
              border: Border.all(
                color: isSelected
                    ? context.colors.accentWork
                    : (isToday ? context.colors.border : Colors.transparent),
                width: isSelected ? 1.5 : 0.8,
              ),
              borderRadius: BorderRadius.circular(4),
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  '$dayOffset',
                  style: AppTextStyles.caption.copyWith(
                    fontWeight: isSelected || isToday ? FontWeight.bold : FontWeight.normal,
                    color: isSelected
                        ? context.colors.accentWork
                        : (isSun
                            ? Colors.redAccent
                            : (isSat ? Colors.blueAccent : context.colors.textPrimary)),
                    fontSize: 12,
                  ),
                ),
                const SizedBox(height: 2),
                if (dayIssues.isNotEmpty)
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Container(
                        width: 5,
                        height: 5,
                        decoration: BoxDecoration(
                          color: dayIssues.any((i) => !i.status.closed)
                              ? context.colors.accentWork
                              : context.colors.textMuted,
                          shape: BoxShape.circle,
                        ),
                      ),
                      if (dayIssues.length > 1) ...[
                        const SizedBox(width: 2),
                        Text(
                          '${dayIssues.length}',
                          style: TextStyle(
                            fontSize: 8,
                            fontWeight: FontWeight.bold,
                            color: context.colors.textMuted,
                          ),
                        ),
                      ],
                    ],
                  )
                else
                  const SizedBox(height: 5),
              ],
            ),
          ),
        );
      },
    );
  }
}
