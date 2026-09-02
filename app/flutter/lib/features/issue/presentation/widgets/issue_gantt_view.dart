import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/models/issue_model.dart';

/// 간이 모바일 간트차트 / 타임라인 뷰 위젯
/// - 날짜 타임라인(가로 스크롤)과 업무 목록(세로 스크롤) 연동
/// - 각 업무의 시작일 ~ 마감일 및 진척률(done_ratio) 시각화 바 제공
/// - 업무 탭 시 상세 화면 연결, 진척률 뱃지 연동
class IssueGanttView extends StatefulWidget {
  final List<IssueModel> issues;
  final ValueChanged<IssueModel> onIssueTap;
  final ValueChanged<IssueModel> onDoneRatioTap;

  const IssueGanttView({
    super.key,
    required this.issues,
    required this.onIssueTap,
    required this.onDoneRatioTap,
  });

  @override
  State<IssueGanttView> createState() => _IssueGanttViewState();
}

class _IssueGanttViewState extends State<IssueGanttView> {
  final ScrollController _horizontalHeaderController = ScrollController();
  final ScrollController _horizontalBodyController = ScrollController();
  final ScrollController _verticalController = ScrollController();

  late DateTime _rangeStart;
  late DateTime _rangeEnd;
  late int _totalDays;

  static const double _colWidth = 36.0;
  static const double _rowHeight = 54.0;
  static const double _titleWidth = 140.0;

  @override
  void initState() {
    super.initState();
    _calculateDateRange();

    // 헤더와 바디의 가로 스크롤 동기화
    _horizontalBodyController.addListener(() {
      if (_horizontalHeaderController.hasClients &&
          _horizontalHeaderController.offset != _horizontalBodyController.offset) {
        _horizontalHeaderController.jumpTo(_horizontalBodyController.offset);
      }
    });

    WidgetsBinding.instance.addPostFrameCallback((_) {
      _scrollToCurrentDay();
    });
  }

  @override
  void didUpdateWidget(covariant IssueGanttView oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.issues != widget.issues) {
      _calculateDateRange();
    }
  }

  @override
  void dispose() {
    _horizontalHeaderController.dispose();
    _horizontalBodyController.dispose();
    _verticalController.dispose();
    super.dispose();
  }

  void _calculateDateRange() {
    final now = DateTime.now();
    DateTime minDate = now.subtract(const Duration(days: 7));
    DateTime maxDate = now.add(const Duration(days: 21));

    for (final issue in widget.issues) {
      final start = DateTime.tryParse(issue.startDate);
      final due = issue.dueDate != null ? DateTime.tryParse(issue.dueDate!) : null;

      if (start != null && start.isBefore(minDate)) {
        minDate = start;
      }
      if (due != null && due.isAfter(maxDate)) {
        maxDate = due;
      }
    }

    _rangeStart = DateTime(minDate.year, minDate.month, minDate.day);
    _rangeEnd = DateTime(maxDate.year, maxDate.month, maxDate.day).add(const Duration(days: 5));
    _totalDays = _rangeEnd.difference(_rangeStart).inDays + 1;
  }

  void _scrollToCurrentDay() {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final daysFromStart = today.difference(_rangeStart).inDays;

    if (daysFromStart > 2 && _horizontalBodyController.hasClients) {
      final targetOffset = (daysFromStart - 2) * _colWidth;
      _horizontalBodyController.animateTo(
        targetOffset.clamp(0.0, _horizontalBodyController.position.maxScrollExtent),
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    }
  }

  Color _getTrackerColor(String trackerName, BuildContext context) {
    switch (trackerName) {
      case '버그':
      case '결함':
        return Colors.redAccent;
      case '기능개선':
      case '개선':
        return Colors.amber;
      case '기획':
      case '설계':
        return Colors.purpleAccent;
      case '회의안건':
      case '보고':
        return context.colors.accentApproval;
      default:
        return context.colors.accentWork;
    }
  }

  @override
  Widget build(BuildContext context) {
    if (widget.issues.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.waterfall_chart_rounded,
                size: 40, color: context.colors.textMuted.withAlpha(120)),
            const SizedBox(height: 8),
            Text(
              '타임라인에 표시할 업무가 없습니다.',
              style: AppTextStyles.bodySm.copyWith(color: context.colors.textMuted),
            ),
          ],
        ),
      );
    }

    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);

    return Container(
      color: context.colors.bgPrimary,
      child: Column(
        children: [
          // ── 상단 툴바 (오늘로 이동 버튼 및 범례) ───────────────────────────
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
            decoration: BoxDecoration(
              color: context.colors.bgSurface,
              border: Border(
                bottom: BorderSide(color: context.colors.border, width: 0.8),
              ),
            ),
            child: Row(
              children: [
                Icon(Icons.timeline_rounded, size: 14, color: context.colors.accentWork),
                const SizedBox(width: 6),
                Text(
                  '업무 타임라인 (간트 뷰)',
                  style: AppTextStyles.caption.copyWith(
                    color: context.colors.textPrimary,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const Spacer(),
                InkWell(
                  onTap: _scrollToCurrentDay,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: context.colors.bgCard,
                      border: Border.all(color: context.colors.border, width: 0.8),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      '오늘로 이동',
                      style: AppTextStyles.caption.copyWith(
                        color: context.colors.accentWork,
                        fontWeight: FontWeight.bold,
                        fontSize: 11,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),

          // ── 타임라인 메인 헤더 & 바디 ──────────────────────────────────────
          Expanded(
            child: Row(
              children: [
                // 1) 고정 좌측 컬럼 (업무 제목 / 담당자)
                Container(
                  width: _titleWidth,
                  decoration: BoxDecoration(
                    color: context.colors.bgCard,
                    border: Border(
                      right: BorderSide(color: context.colors.border, width: 1.0),
                    ),
                  ),
                  child: Column(
                    children: [
                      // 좌상단 코너 헤더
                      Container(
                        height: 48,
                        alignment: Alignment.centerLeft,
                        padding: const EdgeInsets.symmetric(horizontal: 12),
                        decoration: BoxDecoration(
                          color: context.colors.bgSurface,
                          border: Border(
                            bottom: BorderSide(color: context.colors.border, width: 0.8),
                          ),
                        ),
                        child: Text(
                          '업무명 / 담당자',
                          style: AppTextStyles.caption.copyWith(
                            color: context.colors.textMuted,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                      // 업무 제목 세로 리스트
                      Expanded(
                        child: ListView.builder(
                          controller: _verticalController,
                          itemCount: widget.issues.length,
                          itemBuilder: (context, index) {
                            final issue = widget.issues[index];
                            return InkWell(
                              onTap: () => widget.onIssueTap(issue),
                              child: Container(
                                height: _rowHeight,
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 10, vertical: 6),
                                decoration: BoxDecoration(
                                  border: Border(
                                    bottom: BorderSide(
                                        color: context.colors.border.withAlpha(120),
                                        width: 0.5),
                                  ),
                                ),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    Row(
                                      children: [
                                        Container(
                                          width: 6,
                                          height: 6,
                                          decoration: BoxDecoration(
                                            color: _getTrackerColor(
                                                issue.tracker.name, context),
                                            shape: BoxShape.circle,
                                          ),
                                        ),
                                        const SizedBox(width: 4),
                                        Expanded(
                                          child: Text(
                                            issue.subject,
                                            style: AppTextStyles.caption.copyWith(
                                              color: context.colors.textPrimary,
                                              fontWeight: FontWeight.w600,
                                            ),
                                            maxLines: 1,
                                            overflow: TextOverflow.ellipsis,
                                          ),
                                        ),
                                      ],
                                    ),
                                    const SizedBox(height: 2),
                                    Row(
                                      children: [
                                        Text(
                                          issue.assignedTo?.username ?? '미배정',
                                          style: AppTextStyles.caption.copyWith(
                                            color: context.colors.textMuted,
                                            fontSize: 10,
                                          ),
                                        ),
                                        const Spacer(),
                                        InkWell(
                                          onTap: () => widget.onDoneRatioTap(issue),
                                          child: Text(
                                            '${issue.doneRatio}%',
                                            style: TextStyle(
                                              fontSize: 10,
                                              fontWeight: FontWeight.bold,
                                              color: issue.doneRatio == 100
                                                  ? Colors.green
                                                  : context.colors.accentWork,
                                            ),
                                          ),
                                        ),
                                      ],
                                    ),
                                  ],
                                ),
                              ),
                            );
                          },
                        ),
                      ),
                    ],
                  ),
                ),

                // 2) 가로 스크롤 간트 타임라인 영역
                Expanded(
                  child: SingleChildScrollView(
                    controller: _horizontalBodyController,
                    scrollDirection: Axis.horizontal,
                    child: SizedBox(
                      width: _totalDays * _colWidth,
                      child: Column(
                        children: [
                          // 타임라인 날짜 헤더 (월/일/요일)
                          Container(
                            height: 48,
                            decoration: BoxDecoration(
                              color: context.colors.bgSurface,
                              border: Border(
                                bottom: BorderSide(
                                    color: context.colors.border, width: 0.8),
                              ),
                            ),
                            child: Row(
                              children: List.generate(_totalDays, (i) {
                                final date = _rangeStart.add(Duration(days: i));
                                final isToday = date.year == today.year &&
                                    date.month == today.month &&
                                    date.day == today.day;
                                final isSun = date.weekday == DateTime.sunday;
                                final isSat = date.weekday == DateTime.saturday;

                                return Container(
                                  width: _colWidth,
                                  alignment: Alignment.center,
                                  decoration: BoxDecoration(
                                    color: isToday
                                        ? context.colors.accentWork.withAlpha(35)
                                        : Colors.transparent,
                                    border: Border(
                                      right: BorderSide(
                                          color: context.colors.border.withAlpha(80),
                                          width: 0.5),
                                    ),
                                  ),
                                  child: Column(
                                    mainAxisAlignment: MainAxisAlignment.center,
                                    children: [
                                      Text(
                                        '${date.month}/${date.day}',
                                        style: TextStyle(
                                          fontSize: 10,
                                          fontWeight: isToday ? FontWeight.bold : FontWeight.normal,
                                          color: isToday
                                              ? context.colors.accentWork
                                              : (isSun
                                                  ? Colors.redAccent
                                                  : (isSat
                                                      ? Colors.blueAccent
                                                      : context.colors.textPrimary)),
                                        ),
                                      ),
                                      Text(
                                        DateFormat('E', 'ko_KR').format(date),
                                        style: TextStyle(
                                          fontSize: 9,
                                          color: isToday
                                              ? context.colors.accentWork
                                              : context.colors.textMuted,
                                        ),
                                      ),
                                    ],
                                  ),
                                );
                              }),
                            ),
                          ),

                          // 타임라인 바디 그리드 + 업무 바
                          Expanded(
                            child: ListView.builder(
                              physics: const ClampingScrollPhysics(),
                              itemCount: widget.issues.length,
                              itemBuilder: (context, index) {
                                final issue = widget.issues[index];
                                return Container(
                                  height: _rowHeight,
                                  decoration: BoxDecoration(
                                    border: Border(
                                      bottom: BorderSide(
                                          color: context.colors.border.withAlpha(120),
                                          width: 0.5),
                                    ),
                                  ),
                                  child: Stack(
                                    alignment: Alignment.centerLeft,
                                    children: [
                                      // 세로 격자선 및 오늘 하이라이트 배경
                                      Row(
                                        children: List.generate(_totalDays, (i) {
                                          final date = _rangeStart.add(Duration(days: i));
                                          final isToday = date.year == today.year &&
                                              date.month == today.month &&
                                              date.day == today.day;
                                          return Container(
                                            width: _colWidth,
                                            decoration: BoxDecoration(
                                              color: isToday
                                                  ? context.colors.accentWork.withAlpha(15)
                                                  : Colors.transparent,
                                              border: Border(
                                                right: BorderSide(
                                                    color: context.colors.border
                                                        .withAlpha(40),
                                                    width: 0.5),
                                              ),
                                            ),
                                          );
                                        }),
                                      ),

                                      // 간트 바 (Gantt Progress Bar)
                                      _buildGanttBar(issue, context),
                                    ],
                                  ),
                                );
                              },
                            ),
                          ),
                        ],
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

  Widget _buildGanttBar(IssueModel issue, BuildContext context) {
    final start = DateTime.tryParse(issue.startDate);
    final due = issue.dueDate != null ? DateTime.tryParse(issue.dueDate!) : null;

    if (start == null) return const SizedBox.shrink();

    final sDay = DateTime(start.year, start.month, start.day);
    final eDay = due != null
        ? DateTime(due.year, due.month, due.day)
        : sDay;

    final startOffsetDays = sDay.difference(_rangeStart).inDays;
    final durationDays = eDay.difference(sDay).inDays + 1;

    final left = startOffsetDays * _colWidth + 2;
    final width = (durationDays * _colWidth - 4).clamp(_colWidth - 4, double.infinity);

    final trackerColor = _getTrackerColor(issue.tracker.name, context);

    return Positioned(
      left: left,
      width: width,
      child: GestureDetector(
        onTap: () => widget.onIssueTap(issue),
        child: Container(
          height: 28,
          decoration: BoxDecoration(
            color: trackerColor.withAlpha(40),
            borderRadius: BorderRadius.circular(4),
            border: Border.all(color: trackerColor, width: 1.0),
          ),
          child: Stack(
            children: [
              // 진척률 채움 영역
              if (issue.doneRatio > 0)
                FractionallySizedBox(
                  widthFactor: (issue.doneRatio / 100.0).clamp(0.0, 1.0),
                  child: Container(
                    decoration: BoxDecoration(
                      color: trackerColor.withAlpha(140),
                      borderRadius: BorderRadius.circular(3),
                    ),
                  ),
                ),
              // 바 내부 텍스트
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 6),
                child: Row(
                  children: [
                    Expanded(
                      child: Text(
                        issue.subject,
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          color: context.colors.textPrimary,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    Text(
                      '${issue.doneRatio}%',
                      style: TextStyle(
                        fontSize: 9,
                        fontWeight: FontWeight.bold,
                        color: context.colors.textPrimary,
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
