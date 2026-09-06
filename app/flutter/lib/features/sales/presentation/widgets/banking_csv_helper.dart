import 'dart:io';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';
import '../../data/models/sales_models.dart';

/// 🏦 기업 뱅킹 대량 이체용 CSV 생성 및 공유 헬퍼
class BankingCsvHelper {
  /// 은행 대량 이체 표준 CSV 파일 생성 및 공유
  static Future<void> exportAndShareCsv({
    required BuildContext context,
    required List<CommissionPayoutModel> payouts,
    required String periodTitle,
  }) async {
    if (payouts.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('내보낼 지급 명세 내역이 없습니다.')),
      );
      return;
    }

    try {
      // 은행 대량 이체 14개 표준 헤더 (웹 시스템과 100% 동일 규격)
      final headers = [
        '순번',
        '입금은행',
        '입금계좌번호',
        '예금주',
        '실지급액(세후)',
        '세전총액',
        '원천세(3.3%)',
        '성명',
        '소속팀',
        '직책',
        '지급상태',
        '지급일자',
        '정산회차',
        '비고/메모',
      ];

      final rows = payouts.asMap().entries.map((entry) {
        final index = entry.key + 1;
        final p = entry.value;

        return [
          index.toString(),
          _escapeCsv(p.bankName ?? ''),
          // \t 삽입으로 엑셀 열람 시 긴 계좌번호의 지수(Exponential) 변환 방지
          _escapeCsv('\t${p.accountNumber ?? ''}'),
          _escapeCsv(p.accountHolder ?? ''),
          p.netAmount.toString(),
          p.grossAmount.toString(),
          p.totalTax.toString(),
          _escapeCsv(p.salesPersonName ?? ''),
          _escapeCsv(p.teamName ?? ''),
          _escapeCsv(p.dutyDisplay ?? ''),
          _escapeCsv(p.payStatusDisplay ?? ''),
          _escapeCsv(p.paidDate ?? ''),
          _escapeCsv(periodTitle),
          _escapeCsv(p.note ?? ''),
        ];
      }).toList();

      // UTF-8 BOM (\uFEFF) 추가로 엑셀에서 한글 깨짐 원천 방지
      final csvBuffer = StringBuffer('\uFEFF');
      csvBuffer.writeln(headers.join(','));
      for (final row in rows) {
        csvBuffer.writeln(row.join(','));
      }

      final tempDir = await getTemporaryDirectory();
      final cleanTitle = periodTitle.replaceAll(RegExp(r'[\\/:*?"<>|\s]'), '_');
      final dateStr = DateFormat('yyyyMMdd_HHmmss').format(DateTime.now());
      final fileName = '은행이체명세_${cleanTitle}_$dateStr.csv';
      final file = File('${tempDir.path}/$fileName');

      await file.writeAsString(csvBuffer.toString());

      // 모바일 공유 시트 호출
      // ignore: deprecated_member_use
      await Share.shareXFiles(
        [XFile(file.path, mimeType: 'text/csv')],
        text: '[$periodTitle] 은행 대량 이체용 지급 명세서 (${payouts.length}건)',
        subject: '은행 대량 이체 파일 - $periodTitle',
      );
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('이체 파일 생성 실패: $e')),
        );
      }
    }
  }

  static String _escapeCsv(String value) {
    if (value.contains(',') || value.contains('"') || value.contains('\n') || value.contains('\r')) {
      return '"${value.replaceAll('"', '""')}"';
    }
    return '"$value"';
  }
}
