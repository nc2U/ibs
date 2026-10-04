import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:mobile_ibs/core/services/share_helper.dart';
import 'package:open_filex/open_filex.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/providers/project_provider.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/models/site_models.dart';
import '../../data/site_repository.dart';
import '../../providers/site_provider.dart';

/// 📁 사업부지 관련 파일 (토지조서 엑셀, 등기부등본 PDF, 매매계약서 PDF) 다운로드 및 공유 헬퍼
class SiteFileHelper {
  SiteFileHelper._();

  /// 1. 현재 탭별 Excel 다운로드 및 모바일/웹 열람 및 공유
  static Future<void> downloadAndShareCurrentTabExcel({
    required BuildContext context,
    required WidgetRef ref,
  }) async {
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
        return _buildProgressDialog(context, themeColor, '$docTitle Excel 생성 중...');
      },
    );

    try {
      final repository = ref.read(siteRepositoryProvider);
      List<int>? rawBytes;

      if (currentTab == SiteSubTab.sites) {
        rawBytes = await repository.downloadSitesExcel(
          projectId: selectedProject.realProjectId,
          search: searchQuery,
        );
      } else if (currentTab == SiteSubTab.owners) {
        rawBytes = await repository.downloadOwnersExcel(
          projectId: selectedProject.realProjectId,
          search: searchQuery,
          ownSort: ownSortFilter,
        );
      } else if (currentTab == SiteSubTab.contracts) {
        rawBytes = await repository.downloadContractsExcel(
          projectId: selectedProject.realProjectId,
          search: searchQuery,
          ownSort: ownSortFilter,
        );
      }

      if (progressDialogContext != null && progressDialogContext!.mounted) {
        Navigator.of(progressDialogContext!).pop();
        progressDialogContext = null;
      }

      if (rawBytes == null || rawBytes.isEmpty) {
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('$docTitle Excel을 다운로드할 수 없습니다.'),
              behavior: SnackBarBehavior.floating,
            ),
          );
        }
        return;
      }

      final bytes = Uint8List.fromList(rawBytes);
      final nowStr = DateFormat('yyyyMMdd_HHmm').format(DateTime.now());
      final cleanProjectName = projectName.replaceAll(RegExp(r'[^a-zA-Z0-9가-힣]'), '_');
      final fileName = '${filePrefix}_${cleanProjectName}_$nowStr.xlsx';
      const mimeType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';

      if (!context.mounted) return;

      _showFileBottomSheet(
        context: context,
        title: '$docTitle Excel 준비 완료',
        subtitle: fileName,
        icon: Icons.table_chart_rounded,
        themeColor: themeColor,
        openViewerLabel: 'Excel 바로 열기 (스프레드시트 뷰어)',
        openViewerSubtitle: '기기 내 오피스 앱으로 $docTitle 직접 열람',
        shareLabel: '모바일 전송 / 공유 (카카오톡, 메일, 드라이브)',
        shareSubtitle: '팀원이나 외부 협력업체에 $docTitle 파일 전송',
        bytes: bytes,
        fileName: fileName,
        mimeType: mimeType,
        shareText: '[$projectName] $docTitle 엑셀 파일입니다.',
        shareSubject: '$docTitle - $projectName',
      );
    } catch (e) {
      if (progressDialogContext != null && progressDialogContext!.mounted) {
        Navigator.of(progressDialogContext!).pop();
      }
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Excel 생성 실패: $e'),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }

  /// 2. 토지 등기부등본 PDF 다운로드 및 열람/공유
  static Future<void> downloadAndShareRegisterPdf({
    required BuildContext context,
    required WidgetRef ref,
    required SiteItemModel item,
  }) async {
    if (!item.hasRegisterFile) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('등록된 등기부등본 파일이 없습니다.'),
          behavior: SnackBarBehavior.floating,
        ),
      );
      return;
    }

    final regFile = item.siteInfoFiles.first;
    final lotName = '${item.district}_${item.lotNumber}';
    const themeColor = Color(0xFF0D9488);

    BuildContext? progressDialogContext;

    showDialog(
      context: context,
      barrierDismissible: false,
      barrierColor: Colors.black45,
      useRootNavigator: true,
      builder: (ctx) {
        progressDialogContext = ctx;
        return _buildProgressDialog(context, themeColor, '등기부등본 다운로드 중...');
      },
    );

    try {
      final repository = ref.read(siteRepositoryProvider);
      final rawBytes = await repository.downloadSiteRegisterFile(regFile.file);

      if (progressDialogContext != null && progressDialogContext!.mounted) {
        Navigator.of(progressDialogContext!).pop();
        progressDialogContext = null;
      }

      if (rawBytes == null || rawBytes.isEmpty) {
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('등기부등본 파일을 다운로드할 수 없습니다.'),
              behavior: SnackBarBehavior.floating,
            ),
          );
        }
        return;
      }

      final bytes = Uint8List.fromList(rawBytes);
      final ext = regFile.fileName.contains('.') ? regFile.fileName.split('.').last : 'pdf';
      final cleanLot = lotName.replaceAll(RegExp(r'[^a-zA-Z0-9가-힣]'), '_');
      final fileName = '등기부등본_$cleanLot.$ext';
      const mimeType = 'application/pdf';

      if (!context.mounted) return;

      _showFileBottomSheet(
        context: context,
        title: '등기부등본(등기사항전부증명서)',
        subtitle: '${item.district} ${item.lotNumber} ($fileName)',
        icon: Icons.picture_as_pdf_rounded,
        themeColor: themeColor,
        openViewerLabel: '등기부등본 바로 열기 (PDF 뷰어)',
        openViewerSubtitle: '기기 내 뷰어 앱으로 등본 내용 직접 확인',
        shareLabel: '등본 파일 공유 (카카오톡, 메일)',
        shareSubtitle: '팀원이나 외부 협력업체에 등본 전송',
        bytes: bytes,
        fileName: fileName,
        mimeType: mimeType,
        shareText: '[${item.district} ${item.lotNumber}] 토지 등기사항전부증명서(등본)입니다.',
        shareSubject: '토지 등기부등본 - ${item.district} ${item.lotNumber}',
      );
    } catch (e) {
      if (progressDialogContext != null && progressDialogContext!.mounted) {
        Navigator.of(progressDialogContext!).pop();
      }
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('등기부등본 열기 실패: $e'),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }

  /// 3. 매매계약서 PDF 다운로드 및 모바일 열람/공유
  static Future<void> downloadAndShareContractPdf({
    required BuildContext context,
    required WidgetRef ref,
    required SiteContractItemModel item,
  }) async {
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
    const themeColor = Color(0xFFF59E0B);

    BuildContext? progressDialogContext;

    showDialog(
      context: context,
      barrierDismissible: false,
      barrierColor: Colors.black45,
      useRootNavigator: true,
      builder: (pCtx) {
        progressDialogContext = pCtx;
        return _buildProgressDialog(context, themeColor, '매매계약서 다운로드 중...');
      },
    );

    try {
      final repository = ref.read(siteRepositoryProvider);
      final rawBytes = await repository.downloadSiteRegisterFile(contFile.file);

      if (progressDialogContext != null && progressDialogContext!.mounted) {
        Navigator.of(progressDialogContext!).pop();
        progressDialogContext = null;
      }

      if (rawBytes == null || rawBytes.isEmpty) {
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('매매계약서 파일을 다운로드할 수 없습니다.'),
              behavior: SnackBarBehavior.floating,
            ),
          );
        }
        return;
      }

      final bytes = Uint8List.fromList(rawBytes);
      final ext = contFile.fileName.contains('.') ? contFile.fileName.split('.').last : 'pdf';
      final cleanOwner = item.ownerName.replaceAll(RegExp(r'[^a-zA-Z0-9가-힣]'), '_');
      final fileName = '매매계약서_$cleanOwner.$ext';
      const mimeType = 'application/pdf';

      if (!context.mounted) return;

      _showFileBottomSheet(
        context: context,
        title: '매매계약서 다운로드 완료',
        subtitle: '매도인: ${item.ownerName} ($fileName)',
        icon: Icons.description_outlined,
        themeColor: themeColor,
        openViewerLabel: '매매계약서 바로 열기 (PDF 뷰어)',
        openViewerSubtitle: '기기 내 뷰어 앱으로 계약서 내용 직접 확인',
        shareLabel: '계약서 파일 공유 (카카오톡, 메일)',
        shareSubtitle: '팀원이나 법무사/세무사에게 계약서 전송',
        bytes: bytes,
        fileName: fileName,
        mimeType: mimeType,
        shareText: '[매매계약서] 매도인: ${item.ownerName} (${item.contractDate} 계약, ${NumberFormat('#,###').format(item.totalPrice)}원)',
        shareSubject: '토지 매매계약서 - ${item.ownerName}',
      );
    } catch (e) {
      if (progressDialogContext != null && progressDialogContext!.mounted) {
        Navigator.of(progressDialogContext!).pop();
      }
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('매매계약서 열기 실패: $e'),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }

  /// 공통 다운로드 진행 중 인디케이터 다이얼로그
  static Widget _buildProgressDialog(BuildContext context, Color color, String message) {
    return Center(
      child: Material(
        color: Colors.transparent,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
          decoration: BoxDecoration(
            color: context.colors.bgCard,
            borderRadius: BorderRadius.circular(12),
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
                  color: color,
                ),
              ),
              const SizedBox(width: 16),
              Text(
                message,
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
  }

  /// 공통 파일 완료 바텀시트 (바로 열기 vs 공유)
  static void _showFileBottomSheet({
    required BuildContext context,
    required String title,
    required String subtitle,
    required IconData icon,
    required Color themeColor,
    required String openViewerLabel,
    required String openViewerSubtitle,
    required String shareLabel,
    required String shareSubtitle,
    required Uint8List bytes,
    required String fileName,
    required String mimeType,
    required String shareText,
    required String shareSubject,
  }) {
    showModalBottomSheet(
      context: context,
      backgroundColor: context.colors.bgCard,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      clipBehavior: Clip.antiAlias,
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
                    child: Icon(icon, size: 20, color: themeColor),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          title,
                          style: AppTextStyles.titleSm.copyWith(
                            color: context.colors.textPrimary,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Text(
                          subtitle,
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
                leading: Icon(Icons.visibility_outlined, color: themeColor),
                title: Text(openViewerLabel),
                subtitle: Text(openViewerSubtitle, style: const TextStyle(fontSize: 11.5)),
                onTap: () async {
                  Navigator.pop(dialogCtx);
                  if (kIsWeb) {
                    // 웹 환경에서는 브라우저 공유/다운로드 실행
                    await AppShareHelper.shareXFiles(
                      [XFile.fromData(bytes, name: fileName, mimeType: mimeType)],
                      text: shareText,
                      subject: shareSubject,
                    );
                  } else {
                    // 모바일/데스크톱에서는 로컬 캐시에 저장 후 기본 뷰어 오픈
                    try {
                      final tempDir = await getTemporaryDirectory();
                      final file = File('${tempDir.path}/$fileName');
                      await file.writeAsBytes(bytes);
                      await OpenFilex.open(file.path);
                    } catch (_) {
                      await AppShareHelper.shareXFiles(
                        [XFile.fromData(bytes, name: fileName, mimeType: mimeType)],
                        text: shareText,
                        subject: shareSubject,
                      );
                    }
                  }
                },
              ),
              ListTile(
                leading: const Icon(Icons.share_outlined, color: Color(0xFF38BDF8)),
                title: Text(shareLabel),
                subtitle: Text(shareSubtitle, style: const TextStyle(fontSize: 11.5)),
                onTap: () async {
                  Navigator.pop(dialogCtx);
                  await AppShareHelper.shareXFiles(
                    [XFile.fromData(bytes, name: fileName, mimeType: mimeType)],
                    text: shareText,
                    subject: shareSubject,
                  );
                },
              ),
            ],
          ),
        ),
      ),
    );
  }
}
