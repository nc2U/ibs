import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:open_filex/open_filex.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/providers/project_provider.dart';
import '../../../core/theme/app_colors_extension.dart';
import '../data/models/site_models.dart';
import '../data/site_repository.dart';
import '../providers/site_provider.dart';

/// 🗺️ 사업 부지 관리 (Site) 메인 화면
class SiteScreen extends ConsumerStatefulWidget {
  final VoidCallback onBackToMain;

  const SiteScreen({
    super.key,
    required this.onBackToMain,
  });

  @override
  ConsumerState<SiteScreen> createState() => _SiteScreenState();
}

class _SiteScreenState extends ConsumerState<SiteScreen> {
  final TextEditingController _searchController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  Timer? _debounceTimer;

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_onScroll);
  }

  @override
  void dispose() {
    _searchController.dispose();
    _scrollController.dispose();
    _debounceTimer?.cancel();
    super.dispose();
  }

  void _onScroll() {
    if (_scrollController.position.pixels >=
        _scrollController.position.maxScrollExtent - 200) {
      final currentTab = ref.read(siteCurrentSubTabProvider);
      switch (currentTab) {
        case SiteSubTab.sites:
          ref.read(siteListProvider.notifier).fetchNextPage();
          break;
        case SiteSubTab.owners:
          ref.read(siteOwnerListProvider.notifier).fetchNextPage();
          break;
        case SiteSubTab.contracts:
          ref.read(siteContractListProvider.notifier).fetchNextPage();
          break;
      }
    }
  }

  void _onSearchChanged(String value) {
    _debounceTimer?.cancel();
    _debounceTimer = Timer(const Duration(milliseconds: 350), () {
      ref.read(siteSearchQueryProvider.notifier).state = value.trim();
      _fetchCurrentTabInitial();
    });
  }

  void _onClearSearch() {
    _searchController.clear();
    ref.read(siteSearchQueryProvider.notifier).state = '';
    _fetchCurrentTabInitial();
  }

  void _fetchCurrentTabInitial() {
    final currentTab = ref.read(siteCurrentSubTabProvider);
    switch (currentTab) {
      case SiteSubTab.sites:
        ref.read(siteListProvider.notifier).fetchInitial();
        break;
      case SiteSubTab.owners:
        ref.read(siteOwnerListProvider.notifier).fetchInitial();
        break;
      case SiteSubTab.contracts:
        ref.read(siteContractListProvider.notifier).fetchInitial();
        break;
    }
  }

  void _makePhoneCall(String phone, {String? ownerName}) async {
    final cleanPhone = phone.replaceAll(RegExp(r'[^0-9]'), '');
    if (cleanPhone.isEmpty) return;

    final shouldCall = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: context.colors.bgCard,
        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
        titlePadding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        actionsPadding: const EdgeInsets.all(12),
        title: Row(
          children: [
            const Icon(Icons.phone_in_talk, size: 20, color: Color(0xFF10B981)),
            const SizedBox(width: 8),
            Text(
              '통화 연결 확인',
              style: AppTextStyles.titleSm.copyWith(
                color: context.colors.textPrimary,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '${ownerName != null ? "소유자 [$ownerName] 님께" : "해당 연락처로"} 전화를 연결하시겠습니까?',
              style: AppTextStyles.bodySm.copyWith(color: context.colors.textPrimary),
            ),
            const SizedBox(height: 10),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(10),
              color: context.colors.bgSurface,
              child: Row(
                children: [
                  const Icon(Icons.phone, size: 16, color: Color(0xFF10B981)),
                  const SizedBox(width: 8),
                  Text(
                    phone,
                    style: const TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 0.5,
                      color: Color(0xFF10B981),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: Text('취소', style: TextStyle(color: context.colors.textMuted)),
          ),
          ElevatedButton.icon(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF10B981),
              foregroundColor: Colors.white,
              shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            ),
            onPressed: () => Navigator.pop(ctx, true),
            icon: const Icon(Icons.phone, size: 16),
            label: const Text('통화 연결', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );

    if (shouldCall == true) {
      final uri = Uri.parse('tel:$cleanPhone');
      if (await canLaunchUrl(uri)) {
        await launchUrl(uri);
      }
    }
  }

  void _sendSms(String phone) async {
    final cleanPhone = phone.replaceAll(RegExp(r'[^0-9]'), '');
    if (cleanPhone.isEmpty) return;
    final uri = Uri.parse('sms:$cleanPhone');
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri);
    }
  }

  /// 📊 현재 탭별 Excel 다운로드 및 모바일 공유 (지번별, 소유자별, 매입계약)
  Future<void> _downloadAndShareCurrentTabExcel() async {
    final selectedProject = ref.read(selectedRealEstateProjectProvider);
    if (selectedProject == null) return;

    final projectName = selectedProject.name;
    final currentTab = ref.read(siteCurrentSubTabProvider);
    final searchQuery = ref.read(siteSearchQueryProvider);
    final ownSortFilter = ref.read(siteOwnSortFilterProvider);

    String docTitle = '토지조서';
    String filePrefix = '토지조서';
    Color themeColor = const Color(0xFF0D9488);

    if (currentTab == SiteSubTab.owners) {
      docTitle = '소유자별 토지목록';
      filePrefix = '소유자조서';
      themeColor = const Color(0xFF38BDF8);
    } else if (currentTab == SiteSubTab.contracts) {
      docTitle = '사업부지 매입계약 현황';
      filePrefix = '부지매입계약';
      themeColor = const Color(0xFFF59E0B);
    }

    BuildContext? progressDialogContext;

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
                borderRadius: BorderRadius.zero,
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
                  SizedBox(
                    width: 22,
                    height: 22,
                    child: CircularProgressIndicator(
                      strokeWidth: 2.5,
                      color: themeColor,
                    ),
                  ),
                  const SizedBox(width: 16),
                  Text(
                    '$docTitle Excel 생성 중...',
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
      final repository = ref.read(siteRepositoryProvider);
      List<int>? excelBytes;

      if (currentTab == SiteSubTab.sites) {
        excelBytes = await repository.downloadSitesExcel(
          projectId: selectedProject.realProjectId,
          search: searchQuery,
        );
      } else if (currentTab == SiteSubTab.owners) {
        excelBytes = await repository.downloadOwnersExcel(
          projectId: selectedProject.realProjectId,
          search: searchQuery,
          ownSort: ownSortFilter,
        );
      } else if (currentTab == SiteSubTab.contracts) {
        excelBytes = await repository.downloadContractsExcel(
          projectId: selectedProject.realProjectId,
          search: searchQuery,
          ownSort: ownSortFilter,
        );
      }

      if (progressDialogContext != null && progressDialogContext!.mounted) {
        Navigator.of(progressDialogContext!).pop();
        progressDialogContext = null;
      }

      if (excelBytes == null || excelBytes.isEmpty) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('$docTitle Excel을 다운로드할 수 없습니다.'),
              behavior: SnackBarBehavior.floating,
            ),
          );
        }
        return;
      }

      // 임시 디렉토리에 파일 저장
      final tempDir = await getTemporaryDirectory();
      final nowStr = DateFormat('yyyyMMdd_HHmm').format(DateTime.now());
      final cleanProjectName = projectName.replaceAll(RegExp(r'[^a-zA-Z0-9가-힣]'), '_');
      final fileName = '${filePrefix}_${cleanProjectName}_$nowStr.xlsx';
      final file = File('${tempDir.path}/$fileName');
      await file.writeAsBytes(excelBytes);

      if (!mounted) return;

      // 모달 바텀시트로 바로 열기 vs 공유하기 제공
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
                    Container(
                      padding: const EdgeInsets.all(6),
                      decoration: BoxDecoration(
                        color: themeColor.withAlpha(25),
                        shape: BoxShape.circle,
                      ),
                      child: Icon(Icons.table_chart_rounded, size: 20, color: themeColor),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            '$docTitle Excel 준비 완료',
                            style: AppTextStyles.titleSm.copyWith(
                              color: context.colors.textPrimary,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          Text(
                            fileName,
                            style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Divider(color: context.colors.border, height: 1),
                ListTile(
                  leading: Icon(Icons.file_open_outlined, color: themeColor),
                  title: const Text('Excel 바로 열기 (스프레드시트 뷰어)'),
                  subtitle: Text('기기 내 오피스 앱으로 $docTitle 직접 열람', style: const TextStyle(fontSize: 11.5)),
                  onTap: () async {
                    Navigator.pop(dialogCtx);
                    await OpenFilex.open(file.path);
                  },
                ),
                ListTile(
                  leading: const Icon(Icons.share_outlined, color: Color(0xFF38BDF8)),
                  title: const Text('모바일 전송 / 공유 (카카오톡, 메일, 드라이브)'),
                  subtitle: Text('팀원이나 외부 협력업체에 $docTitle 파일 전송', style: const TextStyle(fontSize: 11.5)),
                  onTap: () async {
                    Navigator.pop(dialogCtx);
                    // ignore: deprecated_member_use
                    await Share.shareXFiles(
                      [XFile(file.path, mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')],
                      text: '[$projectName] $docTitle 엑셀 파일입니다.',
                      subject: '$docTitle - $projectName',
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
      }
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Excel 생성 실패: $e'),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }

  /// 📄 토지 등기부등본 PDF 다운로드 및 열람/공유
  Future<void> _downloadAndShareRegisterPdf(SiteItemModel item) async {
    if (!item.hasRegisterFile) return;

    final regFile = item.siteInfoFiles.first;
    final lotName = '${item.district}_${item.lotNumber}';

    BuildContext? progressDialogContext;

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
                borderRadius: BorderRadius.zero,
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
                      color: Color(0xFF0D9488),
                    ),
                  ),
                  const SizedBox(width: 16),
                  Text(
                    '등기부등본 다운로드 중...',
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
      final repository = ref.read(siteRepositoryProvider);
      final fileBytes = await repository.downloadSiteRegisterFile(regFile.file);

      if (progressDialogContext != null && progressDialogContext!.mounted) {
        Navigator.of(progressDialogContext!).pop();
        progressDialogContext = null;
      }

      if (fileBytes == null || fileBytes.isEmpty) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('등기부등본 파일을 다운로드할 수 없습니다.'),
              behavior: SnackBarBehavior.floating,
            ),
          );
        }
        return;
      }

      final tempDir = await getTemporaryDirectory();
      final ext = regFile.fileName.contains('.') ? regFile.fileName.split('.').last : 'pdf';
      final cleanLot = lotName.replaceAll(RegExp(r'[^a-zA-Z0-9가-힣]'), '_');
      final fileName = '등기부등본_$cleanLot.$ext';
      final file = File('${tempDir.path}/$fileName');
      await file.writeAsBytes(fileBytes);

      if (!mounted) return;

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
                    Container(
                      padding: const EdgeInsets.all(6),
                      decoration: BoxDecoration(
                        color: const Color(0xFF0D9488).withAlpha(25),
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.picture_as_pdf_rounded, size: 20, color: Color(0xFF0D9488)),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            '등기부등본(등기사항전부증명서)',
                            style: AppTextStyles.titleSm.copyWith(
                              color: context.colors.textPrimary,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          Text(
                            '${item.district} ${item.lotNumber} ($fileName)',
                            style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Divider(color: context.colors.border, height: 1),
                ListTile(
                  leading: const Icon(Icons.visibility_outlined, color: Color(0xFF0D9488)),
                  title: const Text('등기부등본 바로 열기 (PDF 뷰어)'),
                  subtitle: const Text('기기 내 뷰어 앱으로 등본 내용 직접 확인', style: TextStyle(fontSize: 11.5)),
                  onTap: () async {
                    Navigator.pop(dialogCtx);
                    await OpenFilex.open(file.path);
                  },
                ),
                ListTile(
                  leading: const Icon(Icons.share_outlined, color: Color(0xFF38BDF8)),
                  title: const Text('등본 파일 공유 (카카오톡, 메일)'),
                  subtitle: const Text('팀원이나 외부 협력업체에 등본 전송', style: TextStyle(fontSize: 11.5)),
                  onTap: () async {
                    Navigator.pop(dialogCtx);
                    // ignore: deprecated_member_use
                    await Share.shareXFiles(
                      [XFile(file.path, mimeType: 'application/pdf')],
                      text: '[${item.district} ${item.lotNumber}] 토지 등기사항전부증명서(등본)입니다.',
                      subject: '토지 등기부등본 - ${item.district} ${item.lotNumber}',
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
      }
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('등기부등본 열기 실패: $e'),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }

  /// 매매계약서 PDF 다운로드 및 모바일 열람/공유
  Future<void> _downloadAndShareContractPdf(SiteContractItemModel item) async {
    if (!item.hasContractFile) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('등록된 매매계약서 파일이 없습니다.'),
          behavior: SnackBarBehavior.floating,
        ),
      );
      return;
    }

    final contFile = item.siteContFiles.first;
    BuildContext? progressDialogContext;

    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (pCtx) {
        progressDialogContext = pCtx;
        return Dialog(
          backgroundColor: context.colors.bgCard,
          shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 24, horizontal: 20),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const SizedBox(
                  width: 22,
                  height: 22,
                  child: CircularProgressIndicator(
                    strokeWidth: 2.5,
                    color: Color(0xFFF59E0B),
                  ),
                ),
                const SizedBox(width: 16),
                Text(
                  '매매계약서 다운로드 중...',
                  style: AppTextStyles.bodyMd.copyWith(
                    color: context.colors.textPrimary,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );

    try {
      final repository = ref.read(siteRepositoryProvider);
      final fileBytes = await repository.downloadSiteRegisterFile(contFile.file);

      if (progressDialogContext != null && progressDialogContext!.mounted) {
        Navigator.of(progressDialogContext!).pop();
        progressDialogContext = null;
      }

      if (fileBytes == null || fileBytes.isEmpty) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('매매계약서 파일을 다운로드할 수 없습니다.'),
              behavior: SnackBarBehavior.floating,
            ),
          );
        }
        return;
      }

      final tempDir = await getTemporaryDirectory();
      final ext = contFile.fileName.contains('.') ? contFile.fileName.split('.').last : 'pdf';
      final cleanOwner = item.ownerName.replaceAll(RegExp(r'[^a-zA-Z0-9가-힣]'), '_');
      final fileName = '매매계약서_$cleanOwner.$ext';
      final file = File('${tempDir.path}/$fileName');
      await file.writeAsBytes(fileBytes);

      if (!mounted) return;

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
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: const Color(0xFFF59E0B).withAlpha(25),
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(
                        Icons.description_outlined,
                        color: Color(0xFFF59E0B),
                        size: 22,
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            '매매계약서 다운로드 완료',
                            style: AppTextStyles.titleSm.copyWith(
                              color: context.colors.textPrimary,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          Text(
                            '매도인: ${item.ownerName} ($fileName)',
                            style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Divider(color: context.colors.border, height: 1),
                ListTile(
                  leading: const Icon(Icons.visibility_outlined, color: Color(0xFFF59E0B)),
                  title: const Text('매매계약서 바로 열기 (PDF 뷰어)'),
                  subtitle: const Text('기기 내 뷰어 앱으로 계약서 내용 직접 확인', style: TextStyle(fontSize: 11.5)),
                  onTap: () async {
                    Navigator.pop(dialogCtx);
                    await OpenFilex.open(file.path);
                  },
                ),
                ListTile(
                  leading: const Icon(Icons.share_outlined, color: Color(0xFF38BDF8)),
                  title: const Text('계약서 파일 공유 (카카오톡, 메일)'),
                  subtitle: const Text('팀원이나 법무사/세무사에게 계약서 전송', style: TextStyle(fontSize: 11.5)),
                  onTap: () async {
                    Navigator.pop(dialogCtx);
                    // ignore: deprecated_member_use
                    await Share.shareXFiles(
                      [XFile(file.path, mimeType: 'application/pdf')],
                      text: '[매매계약서] 매도인: ${item.ownerName} (${item.contractDate} 계약, ${NumberFormat('#,###').format(item.totalPrice)}원)',
                      subject: '토지 매매계약서 - ${item.ownerName}',
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
      }
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('매매계약서 열기 실패: $e'),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }

  // ── 1. 필지 상세 바텀시트 ──────────────────────────────────────────
  void _showSiteDetailBottomSheet(SiteItemModel item) {
    final numFormat = NumberFormat('#,###');

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
      backgroundColor: context.colors.bgCard,
      builder: (ctx) {
        return SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(6),
                      decoration: BoxDecoration(
                        color: const Color(0xFF0D9488).withAlpha(25),
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(
                        Icons.pin_drop_outlined,
                        size: 20,
                        color: Color(0xFF0D9488),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            '${item.district} ${item.lotNumber}',
                            style: AppTextStyles.titleSm.copyWith(
                              color: context.colors.textPrimary,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          Text(
                            '지목: ${item.sitePurpose} | 순번 #${item.order}',
                            style: AppTextStyles.caption
                                .copyWith(color: context.colors.textMuted),
                          ),
                        ],
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.close, size: 18),
                      onPressed: () => Navigator.pop(ctx),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Divider(color: context.colors.border, height: 1),
                const SizedBox(height: 14),

                _DetailRow(
                  label: '대지면적 (공부상)',
                  value: '${item.officialArea.toStringAsFixed(2)}㎡ (${item.pyungArea.toStringAsFixed(1)}평)',
                  isHighlight: true,
                  color: const Color(0xFF0D9488),
                ),
                if (item.returnedArea != null)
                  _DetailRow(
                    label: '환지면적',
                    value: '${item.returnedArea!.toStringAsFixed(2)}㎡ (${(item.returnedArea! / 3.305785).toStringAsFixed(1)}평)',
                  ),
                if (item.noticePrice != null)
                  _DetailRow(
                    label: '공시지가 (㎡당)',
                    value: '${numFormat.format(item.noticePrice)}원',
                  ),
                if (item.dupIssueDate != null && item.dupIssueDate!.isNotEmpty)
                  _DetailRow(label: '등본 발급일', value: item.dupIssueDate!),
                if (item.rightsA.isNotEmpty)
                  _DetailRow(label: '갑구 권리제한', value: item.rightsA, isDanger: true),
                if (item.rightsB.isNotEmpty)
                  _DetailRow(label: '을구 권리제한', value: item.rightsB, isDanger: true),
                if (item.note.isNotEmpty)
                  _DetailRow(label: '비고 메모', value: item.note),

                if (item.owners.isNotEmpty) ...[
                  const SizedBox(height: 12),
                  Text(
                    '👤 소유자 정보 (${item.owners.length}명)',
                    style: AppTextStyles.caption.copyWith(
                      color: context.colors.textMuted,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Container(
                    padding: const EdgeInsets.all(8),
                    color: context.colors.bgSurface,
                    child: Column(
                      children: item.owners.map((o) {
                        return Padding(
                          padding: const EdgeInsets.symmetric(vertical: 3),
                          child: Row(
                            children: [
                              Text(
                                o.owner,
                                style: AppTextStyles.bodySecond.copyWith(
                                  color: context.colors.textPrimary,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              if (o.ownSortDesc != null) ...[
                                const SizedBox(width: 6),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                                  decoration: BoxDecoration(
                                    color: context.colors.border,
                                    borderRadius: BorderRadius.circular(2),
                                  ),
                                  child: Text(
                                    o.ownSortDesc!,
                                    style: TextStyle(fontSize: 9.5, color: context.colors.textSecond),
                                  ),
                                ),
                              ],
                            ],
                          ),
                        );
                      }).toList(),
                    ),
                  ),
                ],

                const SizedBox(height: 14),
                Divider(color: context.colors.border, height: 1),
                const SizedBox(height: 10),

                // 하단 액션 버튼 영역 (등본 열기/공유 버튼 상시 노출)
                Row(
                  children: [
                    Expanded(
                      child: ElevatedButton.icon(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: item.hasRegisterFile
                              ? const Color(0xFF0D9488)
                              : context.colors.bgSurface,
                          foregroundColor: item.hasRegisterFile
                              ? Colors.white
                              : context.colors.textMuted,
                          elevation: item.hasRegisterFile ? 1 : 0,
                          side: BorderSide(
                            color: item.hasRegisterFile
                                ? const Color(0xFF0D9488)
                                : context.colors.border,
                            width: 0.8,
                          ),
                          shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                          padding: const EdgeInsets.symmetric(vertical: 10),
                        ),
                        onPressed: () {
                          if (item.hasRegisterFile) {
                            Navigator.pop(ctx);
                            _downloadAndShareRegisterPdf(item);
                          } else {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text('해당 지번의 등기부등본 파일이 아직 등록되지 않았습니다.'),
                                behavior: SnackBarBehavior.floating,
                              ),
                            );
                          }
                        },
                        icon: Icon(
                          item.hasRegisterFile
                              ? Icons.picture_as_pdf_outlined
                              : Icons.picture_as_pdf_outlined,
                          size: 16,
                          color: item.hasRegisterFile
                              ? Colors.white
                              : context.colors.textMuted,
                        ),
                        label: Text(
                          item.hasRegisterFile ? '등본 열기/공유' : '등본 미등록',
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: item.hasRegisterFile ? FontWeight.bold : FontWeight.normal,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: OutlinedButton.icon(
                        style: OutlinedButton.styleFrom(
                          foregroundColor: context.colors.textPrimary,
                          side: BorderSide(color: context.colors.border),
                          shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                          padding: const EdgeInsets.symmetric(vertical: 10),
                        ),
                        onPressed: () {
                          Navigator.pop(ctx);
                          Clipboard.setData(ClipboardData(
                              text: '${item.district} ${item.lotNumber} (${item.sitePurpose}, ${item.officialArea}㎡) 소유자: ${item.displayOwnerSummary}'));
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                              content: Text('필지 정보가 복사되었습니다.'),
                              behavior: SnackBarBehavior.floating,
                            ),
                          );
                        },
                        icon: const Icon(Icons.copy_rounded, size: 16),
                        label: const Text('필지 정보 복사', style: TextStyle(fontSize: 12)),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  // ── 2. 소유자 상세 바텀시트 ────────────────────────────────────────
  void _showOwnerDetailBottomSheet(SiteOwnerItemModel item) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
      backgroundColor: context.colors.bgCard,
      builder: (ctx) {
        return SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(6),
                      decoration: BoxDecoration(
                        color: const Color(0xFF38BDF8).withAlpha(25),
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(
                        Icons.person_outline_rounded,
                        size: 20,
                        color: Color(0xFF38BDF8),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            item.owner,
                            style: AppTextStyles.titleSm.copyWith(
                              color: context.colors.textPrimary,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          Text(
                            '구분: ${item.ownSortDesc ?? '개인'} | 사용동의: ${item.useConsent ? '동의 완료' : '미동의'}',
                            style: AppTextStyles.caption
                                .copyWith(color: context.colors.textMuted),
                          ),
                        ],
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.close, size: 18),
                      onPressed: () => Navigator.pop(ctx),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Divider(color: context.colors.border, height: 1),
                const SizedBox(height: 14),

                if (item.phone1.isNotEmpty)
                  _DetailRow(
                    label: '주연락처',
                    value: item.phone1,
                    isPhone: true,
                    onPhoneTap: () => _makePhoneCall(item.phone1),
                    onSmsTap: () => _sendSms(item.phone1),
                  ),
                if (item.phone2.isNotEmpty)
                  _DetailRow(
                    label: '비상연락처',
                    value: item.phone2,
                    isPhone: true,
                    onPhoneTap: () => _makePhoneCall(item.phone2),
                    onSmsTap: () => _sendSms(item.phone2),
                  ),
                if (item.dateOfBirth != null && item.dateOfBirth!.isNotEmpty)
                  _DetailRow(label: '생년월일', value: item.dateOfBirth!),
                if (item.address1.isNotEmpty)
                  _DetailRow(label: '주소', value: '${item.address1} ${item.address2} ${item.address3}'.trim()),
                _DetailRow(
                  label: '소유 총 면적',
                  value: '${item.totalOwnedArea.toStringAsFixed(2)}㎡ (${(item.totalOwnedArea / 3.305785).toStringAsFixed(1)}평)',
                  isHighlight: true,
                  color: const Color(0xFF38BDF8),
                ),
                if (item.note.isNotEmpty)
                  _DetailRow(label: '특이사항', value: item.note),

                if (item.sites.isNotEmpty) ...[
                  const SizedBox(height: 12),
                  Text(
                    '📌 소유 필지 목록 (${item.sites.length}필지)',
                    style: AppTextStyles.caption.copyWith(
                      color: context.colors.textMuted,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Container(
                    padding: const EdgeInsets.all(8),
                    color: context.colors.bgSurface,
                    child: Column(
                      children: item.sites.map((s) {
                        return Padding(
                          padding: const EdgeInsets.symmetric(vertical: 3),
                          child: Row(
                            children: [
                              Text(
                                s.siteName,
                                style: AppTextStyles.bodySecond.copyWith(
                                  color: context.colors.textPrimary,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              const Spacer(),
                              if (s.ownedArea != null)
                                Text(
                                  '${s.ownedArea!.toStringAsFixed(1)}㎡',
                                  style: AppTextStyles.caption.copyWith(
                                    color: context.colors.textSecond,
                                  ),
                                ),
                              if (s.ownershipRatio != null) ...[
                                const SizedBox(width: 6),
                                Text(
                                  '(${(s.ownershipRatio! * 100).toStringAsFixed(1)}%)',
                                  style: AppTextStyles.caption.copyWith(
                                    color: const Color(0xFF0D9488),
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ],
                            ],
                          ),
                        );
                      }).toList(),
                    ),
                  ),
                ],

                const SizedBox(height: 14),
                Divider(color: context.colors.border, height: 1),
                const SizedBox(height: 10),

                // 하단 통화/상담기록/복사 버튼 행
                Row(
                  children: [
                    if (item.phone1.isNotEmpty) ...[
                      Expanded(
                        child: ElevatedButton.icon(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFF10B981),
                            foregroundColor: Colors.white,
                            shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                            padding: const EdgeInsets.symmetric(vertical: 10),
                          ),
                          onPressed: () {
                            Navigator.pop(ctx);
                            _makePhoneCall(item.phone1, ownerName: item.owner);
                          },
                          icon: const Icon(Icons.phone_outlined, size: 16),
                          label: const Text('전화 걸기', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                        ),
                      ),
                      const SizedBox(width: 8),
                    ],
                    Expanded(
                      child: ElevatedButton.icon(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFFF59E0B),
                          foregroundColor: Colors.white,
                          shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                          padding: const EdgeInsets.symmetric(vertical: 10),
                        ),
                        onPressed: () {
                          Navigator.pop(ctx);
                          showModalBottomSheet(
                            context: context,
                            isScrollControlled: true,
                            backgroundColor: Colors.transparent,
                            builder: (consultationCtx) => SiteOwnerConsultationBottomSheet(owner: item),
                          );
                        },
                        icon: const Icon(Icons.edit_calendar_outlined, size: 16),
                        label: const Text('상담/협의 기록', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                      ),
                    ),
                    const SizedBox(width: 8),
                    IconButton(
                      style: IconButton.styleFrom(
                        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                        side: BorderSide(color: context.colors.border),
                        padding: const EdgeInsets.all(10),
                      ),
                      onPressed: () {
                        Navigator.pop(ctx);
                        Clipboard.setData(ClipboardData(
                            text: '${item.owner} (${item.phone1}) 소유: ${item.displaySiteSummary}'));
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text('소유자 정보가 복사되었습니다.'),
                            behavior: SnackBarBehavior.floating,
                          ),
                        );
                      },
                      icon: const Icon(Icons.copy_rounded, size: 16),
                      tooltip: '정보 복사',
                    ),
                  ],
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  // ── 3. 매입 계약 상세 바텀시트 ──────────────────────────────────────
  void _showContractDetailBottomSheet(SiteContractItemModel item) {
    final numFormat = NumberFormat('#,###');

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
      backgroundColor: context.colors.bgCard,
      builder: (ctx) {
        return SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(6),
                      decoration: BoxDecoration(
                        color: const Color(0xFFF59E0B).withAlpha(25),
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(
                        Icons.receipt_long_rounded,
                        size: 20,
                        color: Color(0xFFF59E0B),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            '매도인: ${item.ownerName}',
                            style: AppTextStyles.titleSm.copyWith(
                              color: context.colors.textPrimary,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          Text(
                            '계약체결일: ${item.contractDate} | 소유권확보: ${item.ownershipCompletion ? '완료' : '진행중'}',
                            style: AppTextStyles.caption
                                .copyWith(color: context.colors.textMuted),
                          ),
                        ],
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.close, size: 18),
                      onPressed: () => Navigator.pop(ctx),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Divider(color: context.colors.border, height: 1),
                const SizedBox(height: 14),

                _DetailRow(
                  label: '총 매매대금',
                  value: '${numFormat.format(item.totalPrice)}원',
                  isHighlight: true,
                  color: const Color(0xFFF59E0B),
                ),
                _DetailRow(
                  label: '계약면적 / 평단가',
                  value: '${item.contractArea.toStringAsFixed(2)}㎡ (${item.contractPyung.toStringAsFixed(1)}평) / 평당 ${numFormat.format(item.pricePerPyung)}원',
                ),
                _DetailRow(
                  label: '대금 지급률',
                  value: '${item.paymentRate.toStringAsFixed(1)}% (기지급: ${numFormat.format(item.totalPaidAmount)}원 / 미지급: ${numFormat.format(item.unpaidAmount)}원)',
                  isHighlight: true,
                  color: item.paymentRate >= 100 ? const Color(0xFF10B981) : const Color(0xFF38BDF8),
                ),

                const SizedBox(height: 10),
                Text(
                  '💳 대금 분할 지급 현황',
                  style: AppTextStyles.caption.copyWith(
                    color: context.colors.textMuted,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 6),
                Container(
                  padding: const EdgeInsets.all(8),
                  color: context.colors.bgSurface,
                  child: Column(
                    children: [
                      _PaymentStepRow(
                        title: '계약금 1',
                        amount: item.downPay1,
                        date: item.downPay1Date,
                        isPaid: item.downPay1IsPaid,
                      ),
                      if (item.downPay2 != null && item.downPay2! > 0)
                        _PaymentStepRow(
                          title: '계약금 2',
                          amount: item.downPay2,
                          date: item.downPay2Date,
                          isPaid: item.downPay2IsPaid,
                        ),
                      if (item.interPay1 != null && item.interPay1! > 0)
                        _PaymentStepRow(
                          title: '중도금 1',
                          amount: item.interPay1,
                          date: item.interPay1Date,
                          isPaid: item.interPay1IsPaid,
                        ),
                      if (item.interPay2 != null && item.interPay2! > 0)
                        _PaymentStepRow(
                          title: '중도금 2',
                          amount: item.interPay2,
                          date: item.interPay2Date,
                          isPaid: item.interPay2IsPaid,
                        ),
                      if (item.remainPay != null && item.remainPay! > 0)
                        _PaymentStepRow(
                          title: '잔금',
                          amount: item.remainPay,
                          date: item.remainPayDate,
                          isPaid: item.remainPayIsPaid,
                        ),
                    ],
                  ),
                ),

                if (item.accNumber.isNotEmpty)
                  _DetailRow(
                    label: '지급 수령계좌',
                    value: '${item.accBank} ${item.accNumber} (예금주: ${item.accOwner})',
                  ),
                if (item.note.isNotEmpty)
                  _DetailRow(label: '특이사항', value: item.note),

                const SizedBox(height: 14),
                Divider(color: context.colors.border, height: 1),
                const SizedBox(height: 10),

                // 하단 액션 버튼 영역 (매매계약서 열기/공유 버튼 상시 노출)
                Row(
                  children: [
                    Expanded(
                      child: ElevatedButton.icon(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: item.hasContractFile
                              ? const Color(0xFFF59E0B)
                              : context.colors.bgSurface,
                          foregroundColor: item.hasContractFile
                              ? Colors.white
                              : context.colors.textMuted,
                          elevation: item.hasContractFile ? 1 : 0,
                          side: BorderSide(
                            color: item.hasContractFile
                                ? const Color(0xFFF59E0B)
                                : context.colors.border,
                            width: 0.8,
                          ),
                          shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                          padding: const EdgeInsets.symmetric(vertical: 10),
                        ),
                        onPressed: () {
                          if (item.hasContractFile) {
                            Navigator.pop(ctx);
                            _downloadAndShareContractPdf(item);
                          } else {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text('해당 계약건의 매매계약서 파일이 아직 등록되지 않았습니다.'),
                                behavior: SnackBarBehavior.floating,
                              ),
                            );
                          }
                        },
                        icon: Icon(
                          item.hasContractFile
                              ? Icons.description_outlined
                              : Icons.description_outlined,
                          size: 16,
                          color: item.hasContractFile
                              ? Colors.white
                              : context.colors.textMuted,
                        ),
                        label: Text(
                          item.hasContractFile ? '계약서 열기/공유' : '계약서 미등록',
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: item.hasContractFile ? FontWeight.bold : FontWeight.normal,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: OutlinedButton.icon(
                        style: OutlinedButton.styleFrom(
                          foregroundColor: context.colors.textPrimary,
                          side: BorderSide(color: context.colors.border),
                          shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                          padding: const EdgeInsets.symmetric(vertical: 10),
                        ),
                        onPressed: () {
                          Navigator.pop(ctx);
                          Clipboard.setData(ClipboardData(
                              text: '매도인: ${item.ownerName}, 총 매매대금: ${numFormat.format(item.totalPrice)}원 (${item.contractArea}㎡)'));
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                              content: Text('계약 정보가 복사되었습니다.'),
                              behavior: SnackBarBehavior.floating,
                            ),
                          );
                        },
                        icon: const Icon(Icons.copy_rounded, size: 16),
                        label: const Text('계약 정보 복사', style: TextStyle(fontSize: 12)),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    // ── 🔄 프로젝트 변경 감지 리스너: 프로젝트가 변경되면 3대 탭 목록 및 종합 집계를 즉시 자동 갱신 ──
    ref.listen(selectedRealEstateProjectProvider, (previous, next) {
      if (previous?.realProjectId != next?.realProjectId) {
        ref.invalidate(siteOverallAggregateProvider);
        ref.read(siteListProvider.notifier).fetchInitial();
        ref.read(siteOwnerListProvider.notifier).fetchInitial();
        ref.read(siteContractListProvider.notifier).fetchInitial();
      }
    });

    final selectedProject = ref.watch(selectedRealEstateProjectProvider);
    final aggregateAsync = ref.watch(siteOverallAggregateProvider);
    final currentTab = ref.watch(siteCurrentSubTabProvider);
    final ownSortFilter = ref.watch(siteOwnSortFilterProvider);

    return Scaffold(
      backgroundColor: context.colors.bgPrimary,
      body: Column(
        children: [
          // ── 1. 부지 관리 상단 헤더 ─────────────────────────────────────
          Container(
            color: context.colors.bgSurface,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            child: Row(
              children: [
                Container(
                  width: 34,
                  height: 34,
                  decoration: BoxDecoration(
                    color: const Color(0xFF0D9488).withAlpha(25),
                    borderRadius: BorderRadius.zero,
                  ),
                  child: const Icon(
                    Icons.map_outlined,
                    size: 19,
                    color: Color(0xFF0D9488),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.center,
                        children: [
                          Text(
                            '부지 정보 관리',
                            style: AppTextStyles.titleSm.copyWith(
                              color: context.colors.textPrimary,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(width: 6),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
                            decoration: BoxDecoration(
                              color: const Color(0xFF0D9488).withAlpha(20),
                              border: Border.all(color: const Color(0xFF0D9488).withAlpha(120), width: 0.8),
                              borderRadius: BorderRadius.circular(2),
                            ),
                            child: const Text(
                              'SITE',
                              style: TextStyle(
                                fontSize: 9.5,
                                fontWeight: FontWeight.bold,
                                color: Color(0xFF0D9488),
                                letterSpacing: 0.6,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 2),
                      Text(
                        selectedProject?.name ?? '부동산 개발 프로젝트',
                        style: AppTextStyles.caption.copyWith(
                          color: context.colors.textMuted,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ),
                ),
                IconButton(
                  onPressed: () {
                    ref.invalidate(siteOverallAggregateProvider);
                    _fetchCurrentTabInitial();
                  },
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

          // ── 2. 상단 고정 부지 종합 집계 대시보드 ─────────────────────────
          aggregateAsync.when(
            loading: () => const SizedBox(
              height: 70,
              child: Center(child: SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))),
            ),
            error: (_, __) => const SizedBox.shrink(),
            data: (aggregate) {
              return Container(
                color: context.colors.bgCard,
                padding: const EdgeInsets.fromLTRB(14, 10, 14, 10),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // 헤더: 총 대상부지 면적 및 필지수
                    Row(
                      children: [
                        Icon(Icons.terrain_outlined, size: 13, color: context.colors.textMuted),
                        const SizedBox(width: 5),
                        Text(
                          aggregate.isReturnedArea ? '사업대상 면적(환지)' : '총 대상부지 면적',
                          style: AppTextStyles.caption.copyWith(
                            color: context.colors.textMuted,
                            fontSize: 10.5,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          '${NumberFormat('#,###.#').format(aggregate.targetTotalArea)}㎡ (${NumberFormat('#,###.#').format(aggregate.targetTotalPyung)}평)',
                          style: AppTextStyles.titleSm.copyWith(
                            color: context.colors.textPrimary,
                            fontSize: 13,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const Spacer(),
                        Text(
                          '총 ${aggregate.totalSitesCount}필지 / ${aggregate.totalOwnersCount}명',
                          style: AppTextStyles.caption.copyWith(
                            color: const Color(0xFF0D9488),
                            fontWeight: FontWeight.bold,
                            fontSize: 11,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Divider(color: context.colors.border, height: 1),
                    const SizedBox(height: 7),

                    // 하단 KPI 3종: 계약면적 | 미계약면적 | 확보율(계약율)
                    Row(
                      children: [
                        _KpiItem(
                          label: '계약면적',
                          value: '${NumberFormat('#,###.#').format(aggregate.totalContractedArea)}㎡ (${NumberFormat('#,###.#').format(aggregate.totalContractedPyung)}평)',
                          color: const Color(0xFF10B981),
                        ),
                        _divider(),
                        _KpiItem(
                          label: '미계약면적',
                          value: '${NumberFormat('#,###.#').format(aggregate.uncontractedArea)}㎡',
                          color: context.colors.textSecond,
                        ),
                        _divider(),
                        _KpiItem(
                          label: '확보율(계약율)',
                          value: '${aggregate.securedAreaRate.toStringAsFixed(1)}%',
                          color: aggregate.securedAreaRate >= 100 ? const Color(0xFF10B981) : const Color(0xFF0D9488),
                        ),
                      ],
                    ),
                  ],
                ),
              );
            },
          ),
          Divider(color: context.colors.border, height: 1),

          // ── 3. 3대 서브 탭 바 ──────────────────────────────────────────
          Container(
            color: context.colors.bgSurface,
            child: Row(
              children: [
                _SubTabButton(
                  title: '지번별 토지',
                  icon: Icons.pin_drop_outlined,
                  isSelected: currentTab == SiteSubTab.sites,
                  onTap: () {
                    ref.read(siteCurrentSubTabProvider.notifier).state = SiteSubTab.sites;
                  },
                ),
                _SubTabButton(
                  title: '소유자별',
                  icon: Icons.person_outline_rounded,
                  isSelected: currentTab == SiteSubTab.owners,
                  onTap: () {
                    ref.read(siteCurrentSubTabProvider.notifier).state = SiteSubTab.owners;
                  },
                ),
                _SubTabButton(
                  title: '매입 계약',
                  icon: Icons.receipt_long_outlined,
                  isSelected: currentTab == SiteSubTab.contracts,
                  onTap: () {
                    ref.read(siteCurrentSubTabProvider.notifier).state = SiteSubTab.contracts;
                  },
                ),
              ],
            ),
          ),
          Divider(color: context.colors.border, height: 1),

          // ── 4. 검색창 및 필터 바 ───────────────────────────────────────
          Container(
            color: context.colors.bgCard,
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            child: Column(
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Container(
                        height: 38,
                        decoration: BoxDecoration(
                          color: context.colors.bgSurface,
                          borderRadius: BorderRadius.zero,
                          border: Border.all(color: context.colors.border, width: 0.8),
                        ),
                        child: TextField(
                          controller: _searchController,
                          onChanged: _onSearchChanged,
                          style: AppTextStyles.bodySecond.copyWith(
                            color: context.colors.textPrimary,
                            fontSize: 13,
                          ),
                          decoration: InputDecoration(
                            isDense: true,
                            hintText: currentTab == SiteSubTab.sites
                                ? '지번, 행정동, 지목, 소유자 검색...'
                                : (currentTab == SiteSubTab.owners
                                    ? '소유자명, 연락처, 지번, 비고 검색...'
                                    : '매도인(소유자), 은행, 계좌, 메모 검색...'),
                            hintStyle: AppTextStyles.bodySecond.copyWith(
                              color: context.colors.textMuted,
                              fontSize: 12.5,
                            ),
                            prefixIcon: Icon(
                              Icons.search_rounded,
                              size: 18,
                              color: context.colors.textMuted,
                            ),
                            suffixIcon: _searchController.text.isNotEmpty
                                ? IconButton(
                                    icon: const Icon(Icons.clear_rounded, size: 16),
                                    color: context.colors.textMuted,
                                    onPressed: _onClearSearch,
                                  )
                                : null,
                            border: InputBorder.none,
                            contentPadding: const EdgeInsets.symmetric(vertical: 9),
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Builder(
                      builder: (context) {
                        Color btnColor = const Color(0xFF0D9488);
                        if (currentTab == SiteSubTab.owners) {
                          btnColor = const Color(0xFF38BDF8);
                        } else if (currentTab == SiteSubTab.contracts) {
                          btnColor = const Color(0xFFF59E0B);
                        }

                        return InkWell(
                          onTap: _downloadAndShareCurrentTabExcel,
                          child: Container(
                            height: 38,
                            padding: const EdgeInsets.symmetric(horizontal: 10),
                            decoration: BoxDecoration(
                              color: btnColor.withAlpha(20),
                              border: Border.all(color: btnColor.withAlpha(100), width: 0.8),
                            ),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Icon(Icons.file_download_outlined, size: 16, color: btnColor),
                                const SizedBox(width: 4),
                                Text(
                                  'Excel',
                                  style: TextStyle(
                                    fontSize: 12,
                                    fontWeight: FontWeight.bold,
                                    color: btnColor,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
                  ],
                ),

                // 소유자/계약 탭일 때 소유구분 필터 칩 표시
                if (currentTab != SiteSubTab.sites) ...[
                  const SizedBox(height: 6),
                  Row(
                    children: [
                      _FilterChipBtn(
                        label: '전체',
                        isSelected: ownSortFilter == '',
                        onTap: () {
                          ref.read(siteOwnSortFilterProvider.notifier).state = '';
                          _fetchCurrentTabInitial();
                        },
                      ),
                      const SizedBox(width: 4),
                      _FilterChipBtn(
                        label: '개인',
                        isSelected: ownSortFilter == '1',
                        onTap: () {
                          ref.read(siteOwnSortFilterProvider.notifier).state = '1';
                          _fetchCurrentTabInitial();
                        },
                      ),
                      const SizedBox(width: 4),
                      _FilterChipBtn(
                        label: '법인',
                        isSelected: ownSortFilter == '2',
                        onTap: () {
                          ref.read(siteOwnSortFilterProvider.notifier).state = '2';
                          _fetchCurrentTabInitial();
                        },
                      ),
                      const SizedBox(width: 4),
                      _FilterChipBtn(
                        label: '국공유지',
                        isSelected: ownSortFilter == '3',
                        onTap: () {
                          ref.read(siteOwnSortFilterProvider.notifier).state = '3';
                          _fetchCurrentTabInitial();
                        },
                      ),
                    ],
                  ),
                ],
              ],
            ),
          ),
          Divider(color: context.colors.border, height: 1),

          // ── 5. 탭별 무한 스크롤 목록 뷰 ────────────────────────────────
          Expanded(
            child: _buildCurrentTabContent(currentTab),
          ),
        ],
      ),
    );
  }

  Widget _buildCurrentTabContent(SiteSubTab tab) {
    switch (tab) {
      case SiteSubTab.sites:
        return _buildSitesListView();
      case SiteSubTab.owners:
        return _buildOwnersListView();
      case SiteSubTab.contracts:
        return _buildContractsListView();
    }
  }

  // 1) 지번별 토지 목록 뷰
  Widget _buildSitesListView() {
    final state = ref.watch(siteListProvider);

    if (state.isLoading) {
      return const Center(child: CircularProgressIndicator(strokeWidth: 2));
    }
    if (state.error != null && state.items.isEmpty) {
      return Center(child: Text('데이터 로드 실패: ${state.error}', style: TextStyle(color: context.colors.error)));
    }
    if (state.items.isEmpty) {
      return Center(child: Text('등록된 사업부지 필지가 없습니다.', style: TextStyle(color: context.colors.textMuted)));
    }

    final itemCount = state.items.length + (state.isFetchingNextPage ? 1 : 0);

    return ListView.separated(
      controller: _scrollController,
      padding: const EdgeInsets.all(12),
      itemCount: itemCount,
      separatorBuilder: (_, __) => const SizedBox(height: 8),
      itemBuilder: (ctx, idx) {
        if (idx == state.items.length) {
          return const Padding(
            padding: EdgeInsets.symmetric(vertical: 12),
            child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
          );
        }

        final item = state.items[idx];
        return Card(
          margin: EdgeInsets.zero,
          color: context.colors.bgCard,
          shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
          elevation: 0,
          child: InkWell(
            onTap: () => _showSiteDetailBottomSheet(item),
            child: Container(
              decoration: BoxDecoration(
                border: Border.all(color: context.colors.border, width: 0.8),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 카드 헤더
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    color: context.colors.bgSurface,
                    child: Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
                          decoration: BoxDecoration(
                            color: const Color(0xFF0D9488).withAlpha(20),
                            border: Border.all(color: const Color(0xFF0D9488).withAlpha(80), width: 0.6),
                          ),
                          child: Text(
                            '순번 #${item.order}',
                            style: const TextStyle(
                              fontSize: 10.5,
                              fontWeight: FontWeight.bold,
                              color: Color(0xFF0D9488),
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            '${item.district} ${item.lotNumber}',
                            style: AppTextStyles.titleSm.copyWith(
                              color: context.colors.textPrimary,
                              fontWeight: FontWeight.bold,
                              fontSize: 13.5,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
                          decoration: BoxDecoration(
                            color: context.colors.border.withAlpha(50),
                            borderRadius: BorderRadius.circular(2),
                          ),
                          child: Text(
                            item.sitePurpose,
                            style: TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w600,
                              color: context.colors.textSecond,
                            ),
                          ),
                        ),
                        const SizedBox(width: 5),
                        // 📄 등기부등본 등록 상태 배지 (상시 노출)
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
                          decoration: BoxDecoration(
                            color: item.hasRegisterFile
                                ? const Color(0xFF0D9488).withAlpha(20)
                                : context.colors.border.withAlpha(40),
                            border: Border.all(
                              color: item.hasRegisterFile
                                  ? const Color(0xFF0D9488).withAlpha(80)
                                  : context.colors.border.withAlpha(80),
                              width: 0.6,
                            ),
                            borderRadius: BorderRadius.circular(2),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(
                                item.hasRegisterFile
                                    ? Icons.picture_as_pdf
                                    : Icons.picture_as_pdf_outlined,
                                size: 11,
                                color: item.hasRegisterFile
                                    ? const Color(0xFF0D9488)
                                    : context.colors.textMuted,
                              ),
                              const SizedBox(width: 2.5),
                              Text(
                                item.hasRegisterFile ? '등본' : '미등록',
                                style: TextStyle(
                                  fontSize: 10,
                                  fontWeight: item.hasRegisterFile
                                      ? FontWeight.bold
                                      : FontWeight.normal,
                                  color: item.hasRegisterFile
                                      ? const Color(0xFF0D9488)
                                      : context.colors.textMuted,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  Divider(color: context.colors.border, height: 1),

                  // 카드 본문
                  Padding(
                    padding: const EdgeInsets.all(12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Text(
                              '공부면적: ',
                              style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                            ),
                            Text(
                              '${item.officialArea.toStringAsFixed(2)}㎡',
                              style: AppTextStyles.bodySecond.copyWith(
                                color: context.colors.textPrimary,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const SizedBox(width: 4),
                            Text(
                              '(${item.pyungArea.toStringAsFixed(1)}평)',
                              style: AppTextStyles.caption.copyWith(color: const Color(0xFF0D9488)),
                            ),
                            const Spacer(),
                            if (item.noticePrice != null)
                              Text(
                                '공시: ${NumberFormat('#,###').format(item.noticePrice)}원/㎡',
                                style: AppTextStyles.caption.copyWith(
                                  color: context.colors.textMuted,
                                  fontSize: 11,
                                ),
                              ),
                          ],
                        ),
                        const SizedBox(height: 6),
                        Row(
                          children: [
                            Icon(Icons.person_outline, size: 13, color: context.colors.textMuted),
                            const SizedBox(width: 4),
                            Expanded(
                              child: Text(
                                '소유자: ${item.displayOwnerSummary}',
                                style: AppTextStyles.caption.copyWith(
                                  color: context.colors.textSecond,
                                  fontSize: 11.5,
                                ),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                            if (item.rightsA.isNotEmpty || item.rightsB.isNotEmpty) ...[
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                                decoration: BoxDecoration(
                                  color: const Color(0xFFEF4444).withAlpha(20),
                                  border: Border.all(color: const Color(0xFFEF4444).withAlpha(80), width: 0.5),
                                ),
                                child: const Text(
                                  '권리제한',
                                  style: TextStyle(
                                    fontSize: 9.5,
                                    fontWeight: FontWeight.bold,
                                    color: Color(0xFFEF4444),
                                  ),
                                ),
                              ),
                            ],
                          ],
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  // 2) 소유자별 토지 목록 뷰
  Widget _buildOwnersListView() {
    final state = ref.watch(siteOwnerListProvider);

    if (state.isLoading) {
      return const Center(child: CircularProgressIndicator(strokeWidth: 2));
    }
    if (state.error != null && state.items.isEmpty) {
      return Center(child: Text('데이터 로드 실패: ${state.error}', style: TextStyle(color: context.colors.error)));
    }
    if (state.items.isEmpty) {
      return Center(child: Text('등록된 토지 소유자가 없습니다.', style: TextStyle(color: context.colors.textMuted)));
    }

    final itemCount = state.items.length + (state.isFetchingNextPage ? 1 : 0);

    return ListView.separated(
      controller: _scrollController,
      padding: const EdgeInsets.all(12),
      itemCount: itemCount,
      separatorBuilder: (_, __) => const SizedBox(height: 8),
      itemBuilder: (ctx, idx) {
        if (idx == state.items.length) {
          return const Padding(
            padding: EdgeInsets.symmetric(vertical: 12),
            child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
          );
        }

        final item = state.items[idx];
        return Card(
          margin: EdgeInsets.zero,
          color: context.colors.bgCard,
          shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
          elevation: 0,
          child: InkWell(
            onTap: () => _showOwnerDetailBottomSheet(item),
            child: Container(
              decoration: BoxDecoration(
                border: Border.all(color: context.colors.border, width: 0.8),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 카드 헤더
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    color: context.colors.bgSurface,
                    child: Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
                          decoration: BoxDecoration(
                            color: const Color(0xFF38BDF8).withAlpha(20),
                            border: Border.all(color: const Color(0xFF38BDF8).withAlpha(80), width: 0.6),
                          ),
                          child: Text(
                            item.ownSortDesc ?? '개인',
                            style: const TextStyle(
                              fontSize: 10.5,
                              fontWeight: FontWeight.bold,
                              color: Color(0xFF38BDF8),
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            item.owner,
                            style: AppTextStyles.titleSm.copyWith(
                              color: context.colors.textPrimary,
                              fontWeight: FontWeight.bold,
                              fontSize: 13.5,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
                          decoration: BoxDecoration(
                            color: item.useConsent
                                ? const Color(0xFF10B981).withAlpha(20)
                                : context.colors.border.withAlpha(50),
                            border: Border.all(
                              color: item.useConsent
                                  ? const Color(0xFF10B981).withAlpha(80)
                                  : context.colors.border,
                              width: 0.6,
                            ),
                          ),
                          child: Text(
                            item.useConsent ? '동의완료' : '미동의',
                            style: TextStyle(
                              fontSize: 10.5,
                              fontWeight: FontWeight.bold,
                              color: item.useConsent ? const Color(0xFF10B981) : context.colors.textMuted,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  Divider(color: context.colors.border, height: 1),

                  // 카드 본문
                  Padding(
                    padding: const EdgeInsets.all(12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(Icons.pin_drop_outlined, size: 13, color: context.colors.textMuted),
                            const SizedBox(width: 4),
                            Expanded(
                              child: Text(
                                item.displaySiteSummary,
                                style: AppTextStyles.bodySecond.copyWith(
                                  color: context.colors.textPrimary,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 12.5,
                                ),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                            Text(
                              '총 ${item.totalOwnedArea.toStringAsFixed(1)}㎡',
                              style: AppTextStyles.caption.copyWith(
                                color: const Color(0xFF0D9488),
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ],
                        ),
                        if (item.phone1.isNotEmpty) ...[
                          const SizedBox(height: 6),
                          Row(
                            children: [
                              Icon(Icons.phone_outlined, size: 13, color: context.colors.textMuted),
                              const SizedBox(width: 4),
                              Text(
                                item.phone1,
                                style: AppTextStyles.caption.copyWith(
                                  color: context.colors.textSecond,
                                  fontSize: 11.5,
                                ),
                              ),
                              const Spacer(),
                              InkWell(
                                onTap: () => _makePhoneCall(item.phone1),
                                child: const Padding(
                                  padding: EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                                  child: Icon(Icons.call, size: 15, color: Color(0xFF10B981)),
                                ),
                              ),
                              const SizedBox(width: 6),
                              InkWell(
                                onTap: () => _sendSms(item.phone1),
                                child: const Padding(
                                  padding: EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                                  child: Icon(Icons.sms_outlined, size: 15, color: Color(0xFF38BDF8)),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  // 3) 사업부지 매입계약 목록 뷰
  Widget _buildContractsListView() {
    final state = ref.watch(siteContractListProvider);
    final numFormat = NumberFormat('#,###');

    if (state.isLoading) {
      return const Center(child: CircularProgressIndicator(strokeWidth: 2));
    }
    if (state.error != null && state.items.isEmpty) {
      return Center(child: Text('데이터 로드 실패: ${state.error}', style: TextStyle(color: context.colors.error)));
    }
    if (state.items.isEmpty) {
      return Center(child: Text('체결된 사업부지 매입 계약이 없습니다.', style: TextStyle(color: context.colors.textMuted)));
    }

    final itemCount = state.items.length + (state.isFetchingNextPage ? 1 : 0);

    return ListView.separated(
      controller: _scrollController,
      padding: const EdgeInsets.all(12),
      itemCount: itemCount,
      separatorBuilder: (_, __) => const SizedBox(height: 8),
      itemBuilder: (ctx, idx) {
        if (idx == state.items.length) {
          return const Padding(
            padding: EdgeInsets.symmetric(vertical: 12),
            child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
          );
        }

        final item = state.items[idx];
        return Card(
          margin: EdgeInsets.zero,
          color: context.colors.bgCard,
          shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
          elevation: 0,
          child: InkWell(
            onTap: () => _showContractDetailBottomSheet(item),
            child: Container(
              decoration: BoxDecoration(
                border: Border.all(color: context.colors.border, width: 0.8),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 카드 헤더
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    color: context.colors.bgSurface,
                    child: Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
                          decoration: BoxDecoration(
                            color: const Color(0xFFF59E0B).withAlpha(20),
                            border: Border.all(color: const Color(0xFFF59E0B).withAlpha(80), width: 0.6),
                          ),
                          child: Text(
                            '매도: ${item.ownerName}',
                            style: const TextStyle(
                              fontSize: 10.5,
                              fontWeight: FontWeight.bold,
                              color: Color(0xFFF59E0B),
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            '계약일: ${item.contractDate}',
                            style: AppTextStyles.caption.copyWith(
                              color: context.colors.textMuted,
                              fontSize: 11.5,
                            ),
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
                          decoration: BoxDecoration(
                            color: item.ownershipCompletion
                                ? const Color(0xFF10B981).withAlpha(20)
                                : const Color(0xFF38BDF8).withAlpha(20),
                            border: Border.all(
                              color: item.ownershipCompletion
                                  ? const Color(0xFF10B981).withAlpha(80)
                                  : const Color(0xFF38BDF8).withAlpha(80),
                              width: 0.6,
                            ),
                          ),
                          child: Text(
                            item.ownershipCompletion ? '소유권확보' : '진행중',
                            style: TextStyle(
                              fontSize: 10.5,
                              fontWeight: FontWeight.bold,
                              color: item.ownershipCompletion ? const Color(0xFF10B981) : const Color(0xFF38BDF8),
                            ),
                          ),
                        ),
                        const SizedBox(width: 5),
                        // 📑 매매계약서 등록 상태 배지 (상시 노출)
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
                          decoration: BoxDecoration(
                            color: item.hasContractFile
                                ? const Color(0xFFF59E0B).withAlpha(20)
                                : context.colors.border.withAlpha(40),
                            border: Border.all(
                              color: item.hasContractFile
                                  ? const Color(0xFFF59E0B).withAlpha(80)
                                  : context.colors.border.withAlpha(80),
                              width: 0.6,
                            ),
                            borderRadius: BorderRadius.circular(2),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(
                                item.hasContractFile
                                    ? Icons.description
                                    : Icons.description_outlined,
                                size: 11,
                                color: item.hasContractFile
                                    ? const Color(0xFFF59E0B)
                                    : context.colors.textMuted,
                              ),
                              const SizedBox(width: 2.5),
                              Text(
                                item.hasContractFile ? '계약서' : '미등록',
                                style: TextStyle(
                                  fontSize: 10,
                                  fontWeight: item.hasContractFile
                                      ? FontWeight.bold
                                      : FontWeight.normal,
                                  color: item.hasContractFile
                                      ? const Color(0xFFF59E0B)
                                      : context.colors.textMuted,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  Divider(color: context.colors.border, height: 1),

                  // 카드 본문
                  Padding(
                    padding: const EdgeInsets.all(12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Text(
                              '매매대금: ',
                              style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                            ),
                            Text(
                              '${numFormat.format(item.totalPrice)}원',
                              style: AppTextStyles.titleSm.copyWith(
                                color: context.colors.textPrimary,
                                fontWeight: FontWeight.bold,
                                fontSize: 13.5,
                              ),
                            ),
                            const Spacer(),
                            Text(
                              '지급률 ${item.paymentRate.toStringAsFixed(0)}%',
                              style: TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.bold,
                                color: item.paymentRate >= 100 ? const Color(0xFF10B981) : const Color(0xFFF59E0B),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 6),
                        Row(
                          children: [
                            Text(
                              '계약면적: ${item.contractArea.toStringAsFixed(1)}㎡ (${item.contractPyung.toStringAsFixed(1)}평)',
                              style: AppTextStyles.caption.copyWith(
                                color: context.colors.textSecond,
                                fontSize: 11.5,
                              ),
                            ),
                            const Spacer(),
                            Text(
                              '평당 ${numFormat.format(item.pricePerPyung)}원',
                              style: AppTextStyles.caption.copyWith(
                                color: const Color(0xFF0D9488),
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _divider() => Container(width: 1, height: 26, color: context.colors.border);
}

/// ── 서브 탭 버튼 ───────────────────────────────────────────────
class _SubTabButton extends StatelessWidget {
  final String title;
  final IconData icon;
  final bool isSelected;
  final VoidCallback onTap;

  const _SubTabButton({
    required this.title,
    required this.icon,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: InkWell(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 9),
          decoration: BoxDecoration(
            border: Border(
              bottom: BorderSide(
                color: isSelected ? const Color(0xFF0D9488) : Colors.transparent,
                width: 2.2,
              ),
            ),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                icon,
                size: 14,
                color: isSelected ? const Color(0xFF0D9488) : context.colors.textMuted,
              ),
              const SizedBox(width: 5),
              Text(
                title,
                style: TextStyle(
                  fontSize: 12.5,
                  fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                  color: isSelected ? const Color(0xFF0D9488) : context.colors.textMuted,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// ── 상단 집계 KPI 아이템 ─────────────────────────────────────────
class _KpiItem extends StatelessWidget {
  final String label;
  final String value;
  final Color color;

  const _KpiItem({
    required this.label,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Column(
        children: [
          Text(
            label,
            style: AppTextStyles.caption.copyWith(
              color: context.colors.textMuted,
              fontSize: 10,
            ),
          ),
          const SizedBox(height: 1),
          Text(
            value,
            style: AppTextStyles.caption.copyWith(
              color: color,
              fontWeight: FontWeight.bold,
              fontSize: 12,
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
    );
  }
}

/// ── 빠른 필터 칩 버튼 ───────────────────────────────────────────
class _FilterChipBtn extends StatelessWidget {
  final String label;
  final bool isSelected;
  final VoidCallback onTap;

  const _FilterChipBtn({
    required this.label,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFF0D9488).withAlpha(20) : context.colors.bgSurface,
          border: Border.all(
            color: isSelected ? const Color(0xFF0D9488) : context.colors.border,
            width: isSelected ? 1 : 0.8,
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 10.5,
            fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
            color: isSelected ? const Color(0xFF0D9488) : context.colors.textSecond,
          ),
        ),
      ),
    );
  }
}

/// ── 상세 정보 행 위젯 ───────────────────────────────────────────
class _DetailRow extends StatelessWidget {
  final String label;
  final String value;
  final bool isHighlight;
  final Color? color;
  final bool isDanger;
  final bool isPhone;
  final VoidCallback? onPhoneTap;
  final VoidCallback? onSmsTap;

  const _DetailRow({
    required this.label,
    required this.value,
    this.isHighlight = false,
    this.color,
    this.isDanger = false,
    this.isPhone = false,
    this.onPhoneTap,
    this.onSmsTap,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3.5),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 100,
            child: Text(
              label,
              style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: AppTextStyles.bodySecond.copyWith(
                color: isDanger
                    ? const Color(0xFFEF4444)
                    : (isHighlight
                        ? (color ?? context.colors.textPrimary)
                        : context.colors.textPrimary),
                fontWeight: (isHighlight || isDanger) ? FontWeight.bold : FontWeight.normal,
                fontSize: 12.5,
              ),
            ),
          ),
          if (isPhone) ...[
            InkWell(
              onTap: onPhoneTap,
              child: const Padding(
                padding: EdgeInsets.symmetric(horizontal: 4),
                child: Icon(Icons.call, size: 16, color: Color(0xFF10B981)),
              ),
            ),
            InkWell(
              onTap: onSmsTap,
              child: const Padding(
                padding: EdgeInsets.symmetric(horizontal: 4),
                child: Icon(Icons.sms_outlined, size: 16, color: Color(0xFF38BDF8)),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

/// ── 분할 지급 단계 행 위젯 ─────────────────────────────────────
class _PaymentStepRow extends StatelessWidget {
  final String title;
  final int? amount;
  final String? date;
  final bool isPaid;

  const _PaymentStepRow({
    required this.title,
    this.amount,
    this.date,
    required this.isPaid,
  });

  @override
  Widget build(BuildContext context) {
    final numFormat = NumberFormat('#,###');

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2.5),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
            decoration: BoxDecoration(
              color: isPaid ? const Color(0xFF10B981).withAlpha(25) : context.colors.border.withAlpha(60),
              borderRadius: BorderRadius.circular(2),
            ),
            child: Text(
              isPaid ? '지급완료' : '미지급',
              style: TextStyle(
                fontSize: 9.5,
                fontWeight: FontWeight.bold,
                color: isPaid ? const Color(0xFF10B981) : context.colors.textMuted,
              ),
            ),
          ),
          const SizedBox(width: 6),
          Text(
            title,
            style: AppTextStyles.caption.copyWith(
              color: context.colors.textPrimary,
              fontWeight: FontWeight.w600,
            ),
          ),
          if (date != null && date!.isNotEmpty) ...[
            const SizedBox(width: 4),
            Text(
              '($date)',
              style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 10.5),
            ),
          ],
          const Spacer(),
          Text(
            amount != null ? '${numFormat.format(amount)}원' : '-',
            style: AppTextStyles.caption.copyWith(
              color: isPaid ? context.colors.textPrimary : context.colors.textMuted,
              fontWeight: isPaid ? FontWeight.bold : FontWeight.normal,
            ),
          ),
        ],
      ),
    );
  }
}

/// 💬 토지 소유자 상담 및 협의 기록 관리 바텀시트
class SiteOwnerConsultationBottomSheet extends ConsumerStatefulWidget {
  final SiteOwnerItemModel owner;

  const SiteOwnerConsultationBottomSheet({super.key, required this.owner});

  @override
  ConsumerState<SiteOwnerConsultationBottomSheet> createState() => _SiteOwnerConsultationBottomSheetState();
}

class _SiteOwnerConsultationBottomSheetState extends ConsumerState<SiteOwnerConsultationBottomSheet> {
  late Future<List<SiteOwnerConsultationLogModel>> _logsFuture;

  @override
  void initState() {
    super.initState();
    _loadLogs();
  }

  void _loadLogs() {
    _logsFuture = ref.read(siteRepositoryProvider).fetchOwnerConsultationLogs(siteOwnerId: widget.owner.pk);
  }

  void _showAddDialog() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => _NewSiteOwnerConsultationDialog(
        ownerId: widget.owner.pk,
        ownerName: widget.owner.owner,
        onSuccess: () {
          setState(() {
            _loadLogs();
          });
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      height: MediaQuery.of(context).size.height * 0.85,
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
                      color: const Color(0xFFF59E0B).withAlpha(20),
                      borderRadius: BorderRadius.zero,
                    ),
                    child: const Icon(Icons.edit_calendar_outlined, size: 18, color: Color(0xFFF59E0B)),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Text(
                              '소유자 협의 / 상담 기록',
                              style: AppTextStyles.titleSm.copyWith(
                                color: context.colors.textPrimary,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const SizedBox(width: 6),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                              decoration: BoxDecoration(
                                color: const Color(0xFFF59E0B).withAlpha(20),
                                border: Border.all(color: const Color(0xFFF59E0B).withAlpha(100), width: 0.6),
                              ),
                              child: Text(
                                widget.owner.owner,
                                style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Color(0xFFF59E0B)),
                              ),
                            ),
                          ],
                        ),
                        Text(
                          '소유 필지: ${widget.owner.displaySiteSummary}',
                          style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 11),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close, size: 18),
                    onPressed: () => Navigator.pop(context),
                  ),
                ],
              ),
            ),
            Divider(color: context.colors.border, height: 1),

            // 신규 등록 액션바
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
              child: Row(
                children: [
                  const Text('협의 및 통화 이력', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                  const Spacer(),
                  ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFFF59E0B),
                      foregroundColor: Colors.white,
                      elevation: 0,
                      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                    ),
                    onPressed: _showAddDialog,
                    icon: const Icon(Icons.add, size: 15),
                    label: const Text('상담일지 작성', style: TextStyle(fontSize: 11.5, fontWeight: FontWeight.bold)),
                  ),
                ],
              ),
            ),

            // 목록 영역
            Expanded(
              child: FutureBuilder<List<SiteOwnerConsultationLogModel>>(
                future: _logsFuture,
                builder: (ctx, snapshot) {
                  if (snapshot.connectionState == ConnectionState.waiting) {
                    return const Center(child: CircularProgressIndicator(strokeWidth: 2));
                  }

                  if (snapshot.hasError) {
                    return Center(
                      child: Text('상담 기록 로드 실패: ${snapshot.error}', style: TextStyle(color: context.colors.error, fontSize: 12)),
                    );
                  }

                  final logs = snapshot.data ?? [];
                  if (logs.isEmpty) {
                    return Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.speaker_notes_off_outlined, size: 40, color: context.colors.textMuted.withAlpha(120)),
                          const SizedBox(height: 10),
                          Text('등록된 상담 및 협의 기록이 없습니다.', style: AppTextStyles.bodySm.copyWith(color: context.colors.textMuted)),
                          const SizedBox(height: 8),
                          TextButton.icon(
                            onPressed: _showAddDialog,
                            icon: const Icon(Icons.add, size: 16, color: Color(0xFFF59E0B)),
                            label: const Text('첫 상담일지 작성하기', style: TextStyle(color: Color(0xFFF59E0B))),
                          ),
                        ],
                      ),
                    );
                  }

                  return ListView.separated(
                    padding: const EdgeInsets.all(16),
                    itemCount: logs.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 12),
                    itemBuilder: (ctx, index) {
                      final item = logs[index];
                      return Container(
                        decoration: BoxDecoration(
                          color: context.colors.bgSurface,
                          borderRadius: BorderRadius.zero,
                          border: Border.all(color: context.colors.border, width: 0.8),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            // 카드 헤더
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                              color: context.colors.bgCard,
                              child: Row(
                                children: [
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
                                    decoration: BoxDecoration(
                                      color: const Color(0xFFF59E0B).withAlpha(20),
                                      border: Border.all(color: const Color(0xFFF59E0B).withAlpha(80), width: 0.6),
                                    ),
                                    child: Text(
                                      item.channelKorean,
                                      style: const TextStyle(
                                        fontSize: 10,
                                        fontWeight: FontWeight.bold,
                                        color: Color(0xFFF59E0B),
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  Expanded(
                                    child: Text(
                                      item.title.isNotEmpty ? item.title : '상담 협의 기록',
                                      style: AppTextStyles.bodySm.copyWith(
                                        color: context.colors.textPrimary,
                                        fontWeight: FontWeight.bold,
                                      ),
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                  ),
                                  Text(
                                    item.consultationDate,
                                    style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 11),
                                  ),
                                ],
                              ),
                            ),
                            Divider(color: context.colors.border, height: 1),

                            // 상담 본문
                            Padding(
                              padding: const EdgeInsets.all(12),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    item.content,
                                    style: AppTextStyles.bodySecond.copyWith(
                                      color: context.colors.textPrimary,
                                      height: 1.4,
                                    ),
                                  ),
                                  if (item.followUpRequired) ...[
                                    const SizedBox(height: 8),
                                    Container(
                                      width: double.infinity,
                                      padding: const EdgeInsets.all(8),
                                      color: const Color(0xFFEF4444).withAlpha(15),
                                      child: Row(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          const Icon(Icons.error_outline, size: 14, color: Color(0xFFEF4444)),
                                          const SizedBox(width: 6),
                                          Expanded(
                                            child: Text(
                                              '후속조치: ${item.followUpNote ?? "조치 예정"}',
                                              style: const TextStyle(fontSize: 11, color: Color(0xFFDC2626), fontWeight: FontWeight.w500),
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ],
                                  const SizedBox(height: 6),
                                  Row(
                                    children: [
                                      if (item.consultantName != null)
                                        Text(
                                          '담당자: ${item.consultantName}',
                                          style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 10.5),
                                        ),
                                      const Spacer(),
                                      if (item.created != null)
                                        Text(
                                          '등록: ${item.created!.split("T").first}',
                                          style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 10.5),
                                        ),
                                    ],
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      );
                    },
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// ➕ 신규 소유자 상담 기록 등록 다이얼로그
class _NewSiteOwnerConsultationDialog extends ConsumerStatefulWidget {
  final int ownerId;
  final String ownerName;
  final VoidCallback onSuccess;

  const _NewSiteOwnerConsultationDialog({
    required this.ownerId,
    required this.ownerName,
    required this.onSuccess,
  });

  @override
  ConsumerState<_NewSiteOwnerConsultationDialog> createState() => _NewSiteOwnerConsultationDialogState();
}

class _NewSiteOwnerConsultationDialogState extends ConsumerState<_NewSiteOwnerConsultationDialog> {
  final _titleController = TextEditingController();
  final _contentController = TextEditingController();
  final _followUpController = TextEditingController();

  String _channel = 'phone';
  String _date = DateFormat('yyyy-MM-dd').format(DateTime.now());
  bool _followUpRequired = false;
  bool _isLoading = false;

  @override
  void dispose() {
    _titleController.dispose();
    _contentController.dispose();
    _followUpController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_titleController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('상담 제목을 입력하세요.'), behavior: SnackBarBehavior.floating),
      );
      return;
    }
    if (_contentController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('상담 내용을 입력하세요.'), behavior: SnackBarBehavior.floating),
      );
      return;
    }

    setState(() => _isLoading = true);

    final repository = ref.read(siteRepositoryProvider);
    final errorMsg = await repository.createOwnerConsultationLog(
      siteOwnerId: widget.ownerId,
      consultationDate: _date,
      channel: _channel,
      title: _titleController.text.trim(),
      content: _contentController.text.trim(),
      followUpRequired: _followUpRequired,
      followUpNote: _followUpController.text.trim(),
    );

    setState(() => _isLoading = false);

    if (mounted) {
      if (errorMsg == null) {
        widget.onSuccess();
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('상담일지가 등록되었습니다.'), behavior: SnackBarBehavior.floating),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('상담일지 등록 실패: $errorMsg'),
            backgroundColor: context.colors.error,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      scrollable: true,
      backgroundColor: context.colors.bgCard,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.zero,
        side: BorderSide(color: context.colors.border, width: 0.8),
      ),
      titlePadding: const EdgeInsets.fromLTRB(16, 16, 16, 12),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16),
      actionsPadding: const EdgeInsets.all(12),
      title: Row(
        children: [
          const Icon(Icons.edit_note, size: 22, color: Color(0xFFF59E0B)),
          const SizedBox(width: 8),
          Text(
            '소유자 상담일지 작성',
            style: AppTextStyles.titleSm.copyWith(
              color: context.colors.textPrimary,
              fontWeight: FontWeight.bold,
            ),
          ),
          const Spacer(),
          Text(
            widget.ownerName,
            style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
          ),
        ],
      ),
      content: SizedBox(
        width: MediaQuery.of(context).size.width * 0.95,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Divider(color: context.colors.border, height: 1),
            const SizedBox(height: 12),

            // 1. 상담일자 & 상담채널
            Row(
              children: [
                Expanded(
                  child: InkWell(
                    onTap: () async {
                      final picked = await showDatePicker(
                        context: context,
                        initialDate: DateTime.parse(_date),
                        firstDate: DateTime(2000),
                        lastDate: DateTime(2100),
                      );
                      if (picked != null) {
                        setState(() => _date = DateFormat('yyyy-MM-dd').format(picked));
                      }
                    },
                    child: InputDecorator(
                      decoration: const InputDecoration(
                        labelText: '상담일자',
                        isDense: true,
                        border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                      ),
                      child: Text(_date, style: const TextStyle(fontSize: 13)),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: DropdownButtonFormField<String>(
                    initialValue: _channel,
                    decoration: const InputDecoration(
                      labelText: '상담채널',
                      isDense: true,
                      border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                    ),
                    items: const [
                      DropdownMenuItem(value: 'phone', child: Text('전화')),
                      DropdownMenuItem(value: 'visit', child: Text('방문')),
                      DropdownMenuItem(value: 'kakao', child: Text('카카오톡')),
                      DropdownMenuItem(value: 'sms', child: Text('문자')),
                      DropdownMenuItem(value: 'email', child: Text('이메일')),
                      DropdownMenuItem(value: 'other', child: Text('기타')),
                    ],
                    onChanged: (val) => setState(() => _channel = val ?? 'phone'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // 2. 제목
            TextField(
              controller: _titleController,
              style: const TextStyle(fontSize: 13),
              decoration: const InputDecoration(
                labelText: '상담 제목 (요약)',
                hintText: '예: 매매 희망단가 및 양도세 문의 협의',
                isDense: true,
                border: OutlineInputBorder(borderRadius: BorderRadius.zero),
              ),
            ),
            const SizedBox(height: 12),

            // 3. 내용
            TextField(
              controller: _contentController,
              maxLines: 4,
              style: const TextStyle(fontSize: 13),
              decoration: const InputDecoration(
                labelText: '상세 상담 및 협의 내용',
                hintText: '소유자와의 통화/면담 세부 협의 내용을 입력하세요.',
                isDense: true,
                border: OutlineInputBorder(borderRadius: BorderRadius.zero),
              ),
            ),
            const SizedBox(height: 10),

            // 4. 후속조치 체크
            CheckboxListTile(
              contentPadding: EdgeInsets.zero,
              controlAffinity: ListTileControlAffinity.leading,
              dense: true,
              title: const Text('후속 조치 필요', style: TextStyle(fontSize: 12)),
              value: _followUpRequired,
              onChanged: (val) => setState(() => _followUpRequired = val ?? false),
            ),
            if (_followUpRequired)
              Padding(
                padding: const EdgeInsets.only(top: 4),
                child: TextField(
                  controller: _followUpController,
                  style: const TextStyle(fontSize: 12.5),
                  decoration: const InputDecoration(
                    labelText: '후속조치 메모',
                    hintText: '예: 예상 양도세 산출표 작성 후 다음 주 재통화 예정',
                    isDense: true,
                    border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                  ),
                ),
              ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: _isLoading ? null : () => Navigator.pop(context),
          child: Text('취소', style: TextStyle(color: context.colors.textMuted)),
        ),
        ElevatedButton(
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFFF59E0B),
            foregroundColor: Colors.white,
            shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
          ),
          onPressed: _isLoading ? null : _submit,
          child: _isLoading
              ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
              : const Text('등록 완료', style: TextStyle(fontWeight: FontWeight.bold)),
        ),
      ],
    );
  }
}
