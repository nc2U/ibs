import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:open_filex/open_filex.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/providers/project_provider.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/contract_repository.dart';
import '../../data/models/contract_models.dart';
import '../../providers/contract_provider.dart';

/// 🏢 동호수 배치도 (배치 매트릭스) 시각화 컴포넌트
/// - 상단 동(Building) 선택 탭
/// - **동(Building) 단위로 완벽히 격리된 층(Floor) × 라인(Line) 매트릭스 렌더링**
/// - 웹 IBS의 ContractBoard/Building 구조와 100% 동일하게 동별 피로티/라인/층수 반영
/// - 분양 상태별 컬러 코딩 (계약완료 / 청약 / 미분양 / 홀딩)
/// - 유닛 터치 시 상세 정보 바텀시트 팝업
/// - **동호수 현황표 엑셀 다운로드 및 모바일 공유 (계약자 표기 / 계약자 미표기)**
class UnitMatrixView extends ConsumerWidget {
  final VoidCallback? onRefresh;

  const UnitMatrixView({
    super.key,
    this.onRefresh,
  });

  Color _parseHexColor(String? hexString, Color defaultColor) {
    if (hexString == null || hexString.isEmpty) return defaultColor;
    try {
      final cleanHex = hexString.replaceAll('#', '');
      if (cleanHex.length == 6) {
        return Color(int.parse('FF$cleanHex', radix: 16));
      } else if (cleanHex.length == 8) {
        return Color(int.parse(cleanHex, radix: 16));
      }
    } catch (_) {}
    return defaultColor;
  }

  Future<void> _downloadAndShareExcel(
    BuildContext context,
    WidgetRef ref, {
    required bool isContractor,
  }) async {
    final selectedProject = ref.read(selectedRealEstateProjectProvider);
    if (selectedProject == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('선택된 프로젝트가 없습니다.'),
          behavior: SnackBarBehavior.floating,
        ),
      );
      return;
    }

    BuildContext? progressDialogContext;

    // 로딩 인디케이터 표시
    showDialog(
      context: context,
      barrierDismissible: false,
      barrierColor: Colors.black45,
      useRootNavigator: true,
      builder: (ctx) {
        progressDialogContext = ctx;
        return Center(
          child: Material(
            color: Colors.transparent,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
              decoration: BoxDecoration(
                color: context.colors.bgCard,
                borderRadius: BorderRadius.circular(4),
                border: Border.all(color: context.colors.border, width: 0.8),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withAlpha(50),
                    blurRadius: 16,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const SizedBox(
                    width: 22,
                    height: 22,
                    child: CircularProgressIndicator(
                      strokeWidth: 2.5,
                      color: Color(0xFF10B981),
                    ),
                  ),
                  const SizedBox(width: 16),
                  Text(
                    isContractor ? '계약자 포함 엑셀 생성 중...' : '계약자 미포함 엑셀 생성 중...',
                    style: AppTextStyles.bodyMd.copyWith(
                      color: context.colors.textPrimary,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );

    try {
      final repository = ref.read(contractRepositoryProvider);
      final excelBytes = await repository.downloadUnitStatusExcel(
        projectId: selectedProject.realProjectId,
        isContractor: isContractor,
      );

      // 로딩 닫기
      if (progressDialogContext != null && progressDialogContext!.mounted) {
        Navigator.of(progressDialogContext!).pop();
        progressDialogContext = null;
      }

      if (excelBytes == null || excelBytes.isEmpty) {
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('동호수 현황표 엑셀을 생성할 수 없습니다.'),
              behavior: SnackBarBehavior.floating,
            ),
          );
        }
        return;
      }

      // 임시 디렉토리에 파일 저장
      final tempDir = await getTemporaryDirectory();
      final nowStr = DateFormat('yyyyMMdd_HHmmss').format(DateTime.now());
      final typeLabel = isContractor ? '계약자포함' : '계약자미포함';
      final cleanProjName = selectedProject.name.replaceAll(RegExp(r'[^a-zA-Z0-9가-힣]'), '_');
      final fileName = '동호수현황표_${cleanProjName}_${typeLabel}_$nowStr.xlsx';
      final file = File('${tempDir.path}/$fileName');
      await file.writeAsBytes(excelBytes);

      if (!context.mounted) return;

      // 액션 선택 다이얼로그 (바로 열람 vs 공유)
      showModalBottomSheet(
        context: context,
        backgroundColor: context.colors.bgCard,
        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
        builder: (dialogCtx) => SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.table_view_rounded, size: 22, color: Color(0xFF10B981)),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        '동호수 현황표 ($typeLabel) 준비 완료',
                        style: AppTextStyles.titleSm.copyWith(
                          color: context.colors.textPrimary,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                Text(
                  fileName,
                  style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                ),
                const SizedBox(height: 12),
                Divider(color: context.colors.border, height: 1),
                ListTile(
                  leading: const Icon(Icons.open_in_new_rounded, color: Color(0xFF38BDF8)),
                  title: const Text('엑셀 바로 열기 (뷰어 확인)'),
                  subtitle: const Text('스마트폰 스프레드시트 앱으로 확인', style: TextStyle(fontSize: 11.5)),
                  onTap: () async {
                    Navigator.pop(dialogCtx);
                    await OpenFilex.open(file.path);
                  },
                ),
                ListTile(
                  leading: const Icon(Icons.share_outlined, color: Color(0xFF34D399)),
                  title: const Text('모바일 전송 / 공유 (카카오톡, 문자, 메일)'),
                  subtitle: const Text('본사 보고 또는 관계자에게 파일 전송', style: TextStyle(fontSize: 11.5)),
                  onTap: () async {
                    Navigator.pop(dialogCtx);
                    // ignore: deprecated_member_use
                    await Share.shareXFiles(
                      [XFile(file.path, mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')],
                      text: '${selectedProject.name} 동호수 현황표 ($typeLabel) 파일입니다.',
                      subject: '${selectedProject.name} 동호수 현황표 ($typeLabel)',
                    );
                  },
                ),
              ],
            ),
          ),
        ),
      );
    } catch (e) {
      if (progressDialogContext != null && progressDialogContext!.mounted) {
        Navigator.of(progressDialogContext!).pop();
        progressDialogContext = null;
      }
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('동호수 현황표 엑셀 다운로드 중 오류가 발생했습니다: $e'),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }

  void _showExcelOptionDialog(BuildContext context, WidgetRef ref) {
    showModalBottomSheet(
      context: context,
      backgroundColor: context.colors.bgCard,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
      builder: (ctx) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Icon(Icons.table_chart_rounded, size: 20, color: Color(0xFF10B981)),
                  const SizedBox(width: 8),
                  Text(
                    '동호수 현황표 엑셀 다운로드 / 공유',
                    style: AppTextStyles.titleSm.copyWith(
                      color: context.colors.textPrimary,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              Text(
                '다운로드 및 공유할 현황표 형식을 선택하세요.',
                style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
              ),
              const SizedBox(height: 12),
              Divider(color: context.colors.border, height: 1),
              ListTile(
                contentPadding: const EdgeInsets.symmetric(horizontal: 8),
                leading: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: const Color(0xFF10B981).withAlpha(30),
                    border: Border.all(color: const Color(0xFF10B981), width: 0.8),
                  ),
                  child: const Icon(Icons.person_rounded, size: 18, color: Color(0xFF10B981)),
                ),
                title: const Text('계약자 표시 버전', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13.5)),
                subtitle: const Text('각 호수별 계약자 성명이 표기된 현황표', style: TextStyle(fontSize: 11.5)),
                trailing: const Icon(Icons.chevron_right_rounded),
                onTap: () {
                  Navigator.pop(ctx);
                  _downloadAndShareExcel(context, ref, isContractor: true);
                },
              ),
              Divider(color: context.colors.border, height: 1),
              ListTile(
                contentPadding: const EdgeInsets.symmetric(horizontal: 8),
                leading: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: const Color(0xFF38BDF8).withAlpha(30),
                    border: Border.all(color: const Color(0xFF38BDF8), width: 0.8),
                  ),
                  child: const Icon(Icons.grid_on_rounded, size: 18, color: Color(0xFF38BDF8)),
                ),
                title: const Text('계약자 미표시 버전 (대외 배포용)', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13.5)),
                subtitle: const Text('계약자 성명 없이 분양/미분양 상태만 표기된 현황표', style: TextStyle(fontSize: 11.5)),
                trailing: const Icon(Icons.chevron_right_rounded),
                onTap: () {
                  Navigator.pop(ctx);
                  _downloadAndShareExcel(context, ref, isContractor: false);
                },
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showUnitDetailBottomSheet(
    BuildContext context,
    WidgetRef ref,
    LayoutHouseUnitModel unit,
    Map<int, UnitTypeItemModel> unitTypeMap,
    Map<int, BuildingUnitModel> buildingMap,
  ) {
    final uType = unit.unitTypeId != null ? unitTypeMap[unit.unitTypeId] : null;
    final bldg = buildingMap[unit.buildingUnitId];

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.zero,
      ),
      backgroundColor: context.colors.bgCard,
      builder: (ctx) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ── 1. 헤더: 동·호수 및 상태 배지 ──
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: unit.isHold
                            ? Colors.redAccent.withAlpha(30)
                            : (unit.isContracted
                                ? const Color(0xFF10B981).withAlpha(30)
                                : context.colors.accentProject.withAlpha(30)),
                        border: Border.all(
                          color: unit.isHold
                              ? Colors.redAccent
                              : (unit.isContracted
                                  ? const Color(0xFF10B981)
                                  : context.colors.accentProject),
                          width: 0.8,
                        ),
                      ),
                      child: Text(
                        unit.isHold
                            ? '홀딩/보류'
                            : (unit.isContracted ? '계약 완료' : '분양 가능 (미분양)'),
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          color: unit.isHold
                              ? Colors.redAccent
                              : (unit.isContracted
                                  ? const Color(0xFF10B981)
                                  : context.colors.accentProject),
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      '${bldg != null ? (bldg.name.endsWith('동') ? bldg.name : '${bldg.name}동') : ''} ${unit.name}호',
                      style: AppTextStyles.titleSm.copyWith(
                        color: context.colors.textPrimary,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const Spacer(),
                    IconButton(
                      icon: const Icon(Icons.close_rounded, size: 20),
                      color: context.colors.textMuted,
                      onPressed: () => Navigator.pop(ctx),
                      padding: EdgeInsets.zero,
                      constraints: const BoxConstraints(),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Divider(color: context.colors.border, height: 1),
                const SizedBox(height: 12),

                // ── 2. 유닛 상세 스펙 그리드 ──
                _buildInfoRow(
                  context,
                  '소속 동',
                  bldg != null ? (bldg.name.endsWith('동') ? bldg.name : '${bldg.name}동') : '-',
                ),
                _buildInfoRow(context, '층 / 라인', '${unit.floorNo}층 / ${unit.bldgLine}호 라인'),
                _buildInfoRow(
                  context,
                  '타입',
                  uType?.name ?? '타입 미지정',
                  color: uType != null ? _parseHexColor(uType.color, context.colors.textPrimary) : null,
                ),
                if (uType?.actualArea != null)
                  _buildInfoRow(context, '전용 / 공급면적', '${uType!.actualArea}㎡ / ${uType.supplyArea ?? '-'}㎡'),

                // ── 3. 미분양(분양 가능)인 경우: 기준/평균 분양가 표시 ──
                if (!unit.isContracted && uType?.averagePrice != null)
                  _buildInfoRow(
                    context,
                    '기준 분양가',
                    '${(uType!.averagePrice! / 100000000).toStringAsFixed(2)} 억원 (${NumberFormat('#,###').format(uType.averagePrice)}원)',
                    color: const Color(0xFF38BDF8),
                    isBold: true,
                  ),

                // ── 4. 계약 정보 (계약된 경우): 계약자명, 공급가액, 계약번호 표시 ──
                if (unit.isContracted) ...[
                  const SizedBox(height: 8),
                  Divider(color: context.colors.border, height: 1),
                  const SizedBox(height: 8),
                  _buildInfoRow(context, '계약자명', unit.contractorName ?? '계약자 정보 없음', isBold: true),
                  if (unit.contractTotalPrice != null)
                    _buildInfoRow(
                      context,
                      '계약 공급가액',
                      '${NumberFormat('#,###').format(unit.contractTotalPrice)} 원 (${(unit.contractTotalPrice! / 100000000).toStringAsFixed(2)}억원)',
                      color: const Color(0xFF10B981),
                      isBold: true,
                    )
                  else if (uType?.averagePrice != null)
                    _buildInfoRow(
                      context,
                      '타입 기준 분양가',
                      '${(uType!.averagePrice! / 100000000).toStringAsFixed(2)} 억원',
                      color: context.colors.textSecond,
                    ),
                  _buildInfoRow(
                    context,
                    '계약 일련번호',
                    (unit.contractSerialNumber != null && unit.contractSerialNumber!.isNotEmpty)
                        ? unit.contractSerialNumber!
                        : '-',
                  ),
                ],

                // ── 5. 홀딩 사유 (홀딩된 경우) ──
                if (unit.isHold && unit.holdReason != null && unit.holdReason!.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Divider(color: context.colors.border, height: 1),
                  const SizedBox(height: 8),
                  _buildInfoRow(context, '홀딩 사유', unit.holdReason!, color: Colors.redAccent),
                ],

                const SizedBox(height: 16),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildInfoRow(BuildContext context, String label, String value,
      {Color? color, bool isBold = false}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
          ),
          Text(
            value,
            style: AppTextStyles.bodySecond.copyWith(
              color: color ?? context.colors.textPrimary,
              fontWeight: isBold ? FontWeight.bold : FontWeight.w500,
              fontSize: 12.5,
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final buildingUnitsAsync = ref.watch(buildingUnitsProvider);
    final unitTypesAsync = ref.watch(unitTypesProvider);
    final houseUnitsAsync = ref.watch(allHouseUnitsProvider);
    final selectedBuildingId = ref.watch(selectedBuildingUnitIdProvider);

    return Column(
      children: [
        // ── 1. 동(Building) 필터 선택 바 ─────────────────────────────────
        Container(
          color: context.colors.bgSurface,
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
          child: buildingUnitsAsync.when(
            loading: () => const SizedBox(height: 32),
            error: (_, __) => const SizedBox(height: 32),
            data: (buildings) {
              return SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: [
                    _BuildingChip(
                      label: '전체 동 펼쳐보기',
                      selected: selectedBuildingId == null,
                      onTap: () {
                        ref.read(selectedBuildingUnitIdProvider.notifier).state = null;
                      },
                    ),
                    ...buildings.map((b) => Padding(
                          padding: const EdgeInsets.only(left: 6),
                          child: _BuildingChip(
                            label: b.name.endsWith('동') ? b.name : '${b.name}동',
                            selected: selectedBuildingId == b.pk,
                            onTap: () {
                              ref.read(selectedBuildingUnitIdProvider.notifier).state = b.pk;
                            },
                          ),
                        )),
                  ],
                ),
              );
            },
          ),
        ),
        Divider(color: context.colors.border, height: 1),

        // ── 2. 상태 범례 및 엑셀 내보내기 액션 바 ──────────────────────────────
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 5),
          color: context.colors.bgCard,
          child: Row(
            children: [
              // 엑셀 다운로드 / 공유 버튼
              InkWell(
                onTap: () => _showExcelOptionDialog(context, ref),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: const Color(0xFF10B981).withAlpha(20),
                    border: Border.all(color: const Color(0xFF10B981).withAlpha(120), width: 0.8),
                  ),
                  child: const Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.file_download_outlined, size: 14, color: Color(0xFF10B981)),
                      SizedBox(width: 4),
                      Text(
                        '엑셀 다운로드 / 공유',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF10B981),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const Spacer(),
              const _LegendItem(color: Color(0xFF10B981), label: '계약완료'),
              const SizedBox(width: 8),
              _LegendItem(color: context.colors.border, label: '미분양(분양가능)', isBorder: true),
              const SizedBox(width: 8),
              const _LegendItem(color: Colors.redAccent, label: '홀딩'),
            ],
          ),
        ),
        Divider(color: context.colors.border, height: 1),

        // ── 3. 동 단위(Building-Wise) 동호수 배치 매트릭스 그리드 ──────────────
        Expanded(
          child: houseUnitsAsync.when(
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (e, _) => Center(
              child: Text(
                '동호수 배치도를 불러오는 중 오류가 발생했습니다: $e',
                style: AppTextStyles.bodySm.copyWith(color: context.colors.textMuted),
              ),
            ),
            data: (houseUnits) {
              if (houseUnits.isEmpty) {
                return Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.grid_view_rounded,
                          size: 40, color: context.colors.textMuted.withAlpha(120)),
                      const SizedBox(height: 8),
                      Text(
                        '등록된 동호수 유닛 정보가 없습니다.',
                        style: AppTextStyles.bodySm.copyWith(color: context.colors.textMuted),
                      ),
                    ],
                  ),
                );
              }

              // 유닛 타입 맵 & 동 맵 생성
              final unitTypeMap = <int, UnitTypeItemModel>{};
              unitTypesAsync.whenData((types) {
                for (final t in types) {
                  unitTypeMap[t.pk] = t;
                }
              });

              final buildingMap = <int, BuildingUnitModel>{};
              final buildingList = buildingUnitsAsync.valueOrNull ?? [];
              for (final b in buildingList) {
                buildingMap[b.pk] = b;
              }

              // ── 핵심: 전체 유닛을 먼저 [동(buildingUnitId)]별로 그룹화 ──
              final Map<int, List<LayoutHouseUnitModel>> buildingGroups = {};
              for (final u in houseUnits) {
                buildingGroups.putIfAbsent(u.buildingUnitId, () => []).add(u);
              }

              // 표시할 동 목록 결정 (특정 동 필터링 또는 전체 동)
              final List<int> targetBuildingIds;
              if (selectedBuildingId != null) {
                targetBuildingIds = [selectedBuildingId];
              } else {
                // 프로젝트의 등록된 동 목록 순서 또는 PK 순서대로 정렬
                targetBuildingIds = buildingList.isNotEmpty
                    ? buildingList.map((b) => b.pk).where((pk) => buildingGroups.containsKey(pk)).toList()
                    : (buildingGroups.keys.toList()..sort());
              }

              return RefreshIndicator(
                onRefresh: () async {
                  ref.invalidate(allHouseUnitsProvider);
                  ref.invalidate(buildingUnitsProvider);
                  ref.invalidate(unitTypesProvider);
                },
                color: const Color(0xFF38BDF8),
                child: SingleChildScrollView(
                  physics: const AlwaysScrollableScrollPhysics(),
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                  child: SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: targetBuildingIds.map((bldgId) {
                      final bldgUnits = buildingGroups[bldgId] ?? [];
                      if (bldgUnits.isEmpty) return const SizedBox.shrink();

                      final bldgName = buildingMap[bldgId]?.name ?? '$bldgId';

                      return Padding(
                        padding: const EdgeInsets.only(right: 20),
                        child: _BuildingMatrixCard(
                          bldgName: bldgName,
                          bldgUnits: bldgUnits,
                          unitTypeMap: unitTypeMap,
                          buildingMap: buildingMap,
                          parseHexColor: _parseHexColor,
                          onUnitTap: (unit) => _showUnitDetailBottomSheet(
                            context,
                            ref,
                            unit,
                            unitTypeMap,
                            buildingMap,
                          ),
                        ),
                      );
                    }).toList(),
                  ),
                ),
              ),
            );
            },
          ),
        ),
      ],
    );
  }
}

/// 🏢 개별 동(Building) 독립 매트릭스 카드 컴포넌트
class _BuildingMatrixCard extends StatelessWidget {
  final String bldgName;
  final List<LayoutHouseUnitModel> bldgUnits;
  final Map<int, UnitTypeItemModel> unitTypeMap;
  final Map<int, BuildingUnitModel> buildingMap;
  final Color Function(String?, Color) parseHexColor;
  final void Function(LayoutHouseUnitModel) onUnitTap;

  const _BuildingMatrixCard({
    required this.bldgName,
    required this.bldgUnits,
    required this.unitTypeMap,
    required this.buildingMap,
    required this.parseHexColor,
    required this.onUnitTap,
  });

  @override
  Widget build(BuildContext context) {
    // 1. 해당 동의 라인(bldgLine) 및 층수(floorNo) 추출 및 정렬
    final lineList = bldgUnits.map((u) => u.bldgLine).toSet().toList()..sort();
    final floorList = bldgUnits.map((u) => u.floorNo).toSet().toList()..sort((a, b) => b.compareTo(a)); // 고층 -> 저층

    // 2. (floor, line) -> LayoutHouseUnitModel 빠른 조회를 위한 맵 구성
    final Map<String, LayoutHouseUnitModel> unitMap = {};
    for (final u in bldgUnits) {
      unitMap['${u.floorNo}_${u.bldgLine}'] = u;
    }

    // 통계: 동별 총 세대수 & 계약 세대수
    final totalUnitsCount = bldgUnits.length;
    final contractedCount = bldgUnits.where((u) => u.isContracted).length;
    final rate = totalUnitsCount > 0 ? (contractedCount / totalUnitsCount * 100).toStringAsFixed(0) : '0';

    return Container(
      decoration: BoxDecoration(
        color: context.colors.bgSurface,
        border: Border.all(color: context.colors.border, width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── 동 상단 헤더 배너 ──
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
            color: context.colors.bgCard,
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.apartment_rounded, size: 15, color: context.colors.accentProject),
                const SizedBox(width: 6),
                Text(
                  bldgName.endsWith('동') ? bldgName : '$bldgName 동',
                  style: AppTextStyles.titleSm.copyWith(
                    fontWeight: FontWeight.bold,
                    color: context.colors.textPrimary,
                    fontSize: 13,
                  ),
                ),
                const SizedBox(width: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
                  decoration: BoxDecoration(
                    color: const Color(0xFF10B981).withAlpha(20),
                    border: Border.all(color: const Color(0xFF10B981).withAlpha(100), width: 0.6),
                  ),
                  child: Text(
                    '$contractedCount / $totalUnitsCount세대 ($rate%)',
                    style: const TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF10B981),
                    ),
                  ),
                ),
              ],
            ),
          ),
          Divider(color: context.colors.border, height: 1),

          // ── 층 × 라인 매트릭스 그리드 ──
          Padding(
            padding: const EdgeInsets.all(8),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: floorList.map((floor) {
                return Padding(
                  padding: const EdgeInsets.only(bottom: 4),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      // 층수 표시 라벨
                      Container(
                        width: 32,
                        height: 36,
                        alignment: Alignment.center,
                        decoration: BoxDecoration(
                          color: context.colors.bgCard,
                          border: Border.all(color: context.colors.border, width: 0.8),
                        ),
                        child: Text(
                          '${floor}F',
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            color: context.colors.textMuted,
                            fontSize: 10,
                          ),
                        ),
                      ),
                      const SizedBox(width: 4),

                      // 해당 층의 각 라인 호수 셀
                      ...lineList.map((line) {
                        final unit = unitMap['${floor}_$line'];

                        // 해당 위치에 유닛이 없는 경우(피로티 또는 비어있는 라인)
                        if (unit == null) {
                          return Padding(
                            padding: const EdgeInsets.only(right: 4),
                            child: Container(
                              width: 54,
                              height: 36,
                              decoration: BoxDecoration(
                                color: context.colors.bgCard.withAlpha(50),
                                border: Border.all(color: context.colors.border.withAlpha(60), width: 0.5),
                              ),
                              alignment: Alignment.center,
                              child: Text(
                                floor <= 2 ? 'PILOTI' : '-',
                                style: TextStyle(
                                  fontSize: 8.5,
                                  color: context.colors.textDisabled,
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                            ),
                          );
                        }

                        final uType = unit.unitTypeId != null ? unitTypeMap[unit.unitTypeId] : null;
                        final typeColor = parseHexColor(uType?.color, context.colors.accentProject);

                        return Padding(
                          padding: const EdgeInsets.only(right: 4),
                          child: InkWell(
                            onTap: () => onUnitTap(unit),
                            child: Container(
                              width: 54,
                              height: 36,
                              decoration: BoxDecoration(
                                color: unit.isHold
                                    ? Colors.redAccent.withAlpha(30)
                                    : (unit.isContracted
                                        ? const Color(0xFF10B981).withAlpha(35)
                                        : context.colors.bgCard),
                                border: Border.all(
                                  color: unit.isHold
                                      ? Colors.redAccent
                                      : (unit.isContracted
                                          ? const Color(0xFF10B981)
                                          : context.colors.border),
                                  width: unit.isContracted || unit.isHold ? 1.2 : 0.8,
                                ),
                              ),
                              child: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  // 호수
                                  Text(
                                    unit.name,
                                    style: TextStyle(
                                      fontSize: 10.5,
                                      fontWeight: FontWeight.bold,
                                      color: unit.isHold
                                          ? Colors.redAccent
                                          : (unit.isContracted
                                              ? const Color(0xFF10B981)
                                              : context.colors.textPrimary),
                                    ),
                                    maxLines: 1,
                                  ),
                                  // 타입명 또는 계약자명
                                  Text(
                                    unit.isContracted
                                        ? (unit.contractorName ?? '계약')
                                        : (uType?.name ?? '-'),
                                    style: TextStyle(
                                      fontSize: 8.5,
                                      color: unit.isContracted
                                          ? context.colors.textPrimary
                                          : typeColor,
                                      fontWeight: FontWeight.w500,
                                    ),
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ],
                              ),
                            ),
                          ),
                        );
                      }),
                    ],
                  ),
                );
              }).toList(),
            ),
          ),

          // ── 하단 동 라벨 받침대 (Building Base) ──
          Container(
            padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 12),
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: context.colors.accentProject.withAlpha(30),
              border: Border(top: BorderSide(color: context.colors.border, width: 0.8)),
            ),
            child: Text(
              bldgName.endsWith('동') ? '$bldgName 건물 기반' : '$bldgName 동 건물 기반',
              style: TextStyle(
                fontSize: 10.5,
                fontWeight: FontWeight.bold,
                color: context.colors.accentProject,
                letterSpacing: 0.5,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _BuildingChip extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onTap;

  const _BuildingChip({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
          decoration: BoxDecoration(
            color: selected ? const Color(0xFF38BDF8).withAlpha(40) : context.colors.bgCard,
            borderRadius: BorderRadius.zero,
            border: Border.all(
              color: selected ? const Color(0xFF38BDF8) : context.colors.border,
              width: selected ? 1.4 : 0.8,
            ),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (selected) ...[
                const Icon(
                  Icons.check,
                  size: 12,
                  color: Color(0xFF38BDF8),
                ),
                const SizedBox(width: 4),
              ],
              Text(
                label,
                style: TextStyle(
                  fontSize: 11.5,
                  fontWeight: selected ? FontWeight.bold : FontWeight.normal,
                  color: selected ? const Color(0xFF38BDF8) : context.colors.textSecond,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _LegendItem extends StatelessWidget {
  final Color color;
  final String label;
  final bool isBorder;

  const _LegendItem({
    required this.color,
    required this.label,
    this.isBorder = false,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 9,
          height: 9,
          decoration: BoxDecoration(
            color: isBorder ? Colors.transparent : color,
            border: Border.all(color: color, width: 1.0),
            borderRadius: BorderRadius.zero,
          ),
        ),
        const SizedBox(width: 4),
        Text(
          label,
          style: TextStyle(
            fontSize: 10.5,
            color: context.colors.textMuted,
          ),
        ),
      ],
    );
  }
}
