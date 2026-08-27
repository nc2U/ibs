import 'package:flutter/material.dart';

/// 🏦 1. 프로젝트 은행 계좌 모델 (/api/v1/ledger/project-bank-account/)
class ProjectBankAccountModel {
  final int pk;
  final String aliasName;
  final String? number;
  final String? holder;
  final String? bankName;
  final bool isHide;
  final bool inactive;
  final bool isImprest;
  final bool directpay;

  ProjectBankAccountModel({
    required this.pk,
    required this.aliasName,
    this.number,
    this.holder,
    this.bankName,
    this.isHide = false,
    this.inactive = false,
    this.isImprest = false,
    this.directpay = false,
  });

  factory ProjectBankAccountModel.fromJson(Map<String, dynamic> json) {
    return ProjectBankAccountModel(
      pk: json['pk'] ?? json['id'] ?? 0,
      aliasName: json['alias_name']?.toString() ?? '',
      number: json['number']?.toString(),
      holder: json['holder']?.toString(),
      bankName: json['bankcode_desc'] ?? json['bank_name'],
      isHide: json['is_hide'] ?? false,
      inactive: json['inactive'] ?? false,
      isImprest: json['is_imprest'] ?? false,
      directpay: json['directpay'] ?? false,
    );
  }
}

/// 💳 2. 프로젝트 거래 전표(출납) 모델 (/api/v1/ledger/project-transaction/)
class ProjectTransactionItemModel {
  final int pk;
  final int project;
  final String? sort;           // '1': 입금/수입, '2': 출금/지출, '3': 대체/이체
  final String? sortName;
  final String? accountName;
  final String? content;
  final String? trader;
  final int? bankAccountId;
  final String? bankAccountName;
  final int amount;
  final String dealDate;
  final String? note;
  final List<ProjectAccountingEntryModel> accountingEntries;

  ProjectTransactionItemModel({
    required this.pk,
    required this.project,
    this.sort,
    this.sortName,
    this.accountName,
    this.content,
    this.trader,
    this.bankAccountId,
    this.bankAccountName,
    required this.amount,
    required this.dealDate,
    this.note,
    this.accountingEntries = const [],
  });

  factory ProjectTransactionItemModel.fromJson(Map<String, dynamic> json) {
    final entries = (json['accounting_entries'] is List)
        ? (json['accounting_entries'] as List)
            .map((e) => ProjectAccountingEntryModel.fromJson(e))
            .toList()
        : <ProjectAccountingEntryModel>[];

    // 대표 거래처 및 계정과목 추출
    String? firstTrader;
    String? firstAccount;
    if (entries.isNotEmpty) {
      firstTrader = entries.first.trader;
      firstAccount = entries.first.accountName;
    }

    return ProjectTransactionItemModel(
      pk: json['pk'] ?? json['id'] ?? 0,
      project: json['project'] ?? 0,
      sort: json['sort']?.toString(),
      sortName: json['sort_desc'] ?? json['sort_name'] ?? (json['sort'] == '1' ? '입금' : json['sort'] == '2' ? '출금' : '대체'),
      accountName: firstAccount ?? json['account_name'],
      content: json['content']?.toString(),
      trader: firstTrader ?? json['trader']?.toString(),
      bankAccountId: json['bank_account'] is int ? json['bank_account'] : null,
      bankAccountName: json['bank_account_desc'] ?? json['bank_account_name'],
      amount: (json['amount'] ?? 0) as int,
      dealDate: json['deal_date']?.toString() ?? '',
      note: json['note']?.toString(),
      accountingEntries: entries,
    );
  }

  bool get isIncome => sort == '1';
  bool get isExpense => sort == '2';
  bool get isTransfer => sort == '3';

  /// 계정과목 표출 텍스트 (예: '복리후생비', '소방 공사비 외 2건')
  String get displayAccountName {
    final validAccounts = accountingEntries
        .map((e) => e.accountName?.trim())
        .where((name) => name != null && name.isNotEmpty)
        .map((name) => name!)
        .toSet() // 동일한 계정과목 중복 제거
        .toList();

    if (validAccounts.isEmpty) {
      if (accountName != null && accountName!.isNotEmpty) {
        return accountName!;
      }
      return '계정과목 미지정';
    }

    final firstName = validAccounts.first;
    final otherCount = validAccounts.length - 1;

    if (otherCount > 0) {
      return '$firstName 외 $otherCount건';
    }
    return firstName;
  }

  /// 거래처 표출 텍스트 (예: '스타벅스', '스타벅스 외 2곳')
  String? get displayTraderName {
    final validTraders = accountingEntries
        .map((e) => e.trader?.trim())
        .where((t) => t != null && t.isNotEmpty)
        .map((t) => t!)
        .toList();

    if (validTraders.isEmpty) {
      return trader;
    }

    final firstTrader = validTraders.first;
    final otherCount = validTraders.length - 1;

    if (otherCount > 0) {
      return '$firstTrader 외 $otherCount곳';
    }
    return firstTrader;
  }

  Color get sortColor {
    if (isIncome) return const Color(0xFF10B981); // 수입 (초록)
    if (isExpense) return const Color(0xFFEF4444); // 지출 (빨강)
    return const Color(0xFF38BDF8);                // 대체/이체 (파랑)
  }

  String get sortSign => isIncome ? '+' : (isExpense ? '-' : '');

  /// 순수 분양대금(분담금, ProjectAccount.is_payment=true) 수납 분개 항목 조회
  ProjectAccountingEntryModel? get paymentContractEntry {
    for (final entry in accountingEntries) {
      if (entry.isPayment && entry.contractId != null) {
        return entry;
      }
    }
    return null;
  }
}

/// 📑 3. 회계 분개 항목 모델 (복식부기 항목)
class ProjectAccountingEntryModel {
  final int pk;
  final int? accountId;
  final String? accountName;
  final int amount;
  final String? trader;
  final bool isPayment;
  final int? contractId;
  final String? contractDisplay;
  final String? contractorDisplay;

  ProjectAccountingEntryModel({
    required this.pk,
    this.accountId,
    this.accountName,
    required this.amount,
    this.trader,
    this.isPayment = false,
    this.contractId,
    this.contractDisplay,
    this.contractorDisplay,
  });

  factory ProjectAccountingEntryModel.fromJson(Map<String, dynamic> json) {
    return ProjectAccountingEntryModel(
      pk: json['pk'] ?? json['id'] ?? 0,
      accountId: json['account'] is int ? json['account'] : (json['account'] is Map ? json['account']['pk'] : null),
      accountName: json['account_name'] ?? json['account_desc'] ?? (json['account'] is Map ? json['account']['name'] : null),
      amount: (json['amount'] ?? 0) as int,
      trader: json['trader']?.toString(),
      isPayment: json['is_payment'] == true,
      contractId: json['contract'] is int ? json['contract'] : (json['contract'] is Map ? json['contract']['pk'] : null),
      contractDisplay: json['contract_display']?.toString(),
      contractorDisplay: json['contractor_display']?.toString(),
    );
  }
}

/// 📊 4. 계좌별 잔액 현황 모델 (/api/v1/ledger/project-transaction/balance_by_account/)
class ProjectBalanceByAccountModel {
  final String bankAcc;       // 계좌 별칭
  final String bankNum;       // 계좌 번호
  final int incSum;           // 수입 총누계
  final int outSum;           // 지출 총누계
  final int dateInc;          // 당일 수입
  final int dateOut;          // 당일 지출
  final int balance;          // 현재 잔액

  ProjectBalanceByAccountModel({
    required this.bankAcc,
    required this.bankNum,
    required this.incSum,
    required this.outSum,
    required this.dateInc,
    required this.dateOut,
    required this.balance,
  });

  factory ProjectBalanceByAccountModel.fromJson(Map<String, dynamic> json) {
    return ProjectBalanceByAccountModel(
      bankAcc: json['bank_acc']?.toString() ?? '',
      bankNum: json['bank_num']?.toString() ?? '',
      incSum: (json['inc_sum'] ?? 0) as int,
      outSum: (json['out_sum'] ?? 0) as int,
      dateInc: (json['date_inc'] ?? 0) as int,
      dateOut: (json['date_out'] ?? 0) as int,
      balance: (json['balance'] ?? 0) as int,
    );
  }
}

/// 📈 5. 회계 자금 종합 요약 KPI 모델 (100% 팩트 기반 실시간 잔고 & 당월 캐시플로우)
class LedgerOverallAggregateModel {
  final int totalBalance;      // 총 잔고액 (모든 프로젝트 계좌 실시간 가용 시재)
  final int monthIncome;       // 당월 입금(수입)
  final int monthExpense;      // 당월 출금(지출)
  final int monthBalance;      // 당월 수지차 (당월 입금 - 당월 지출)

  LedgerOverallAggregateModel({
    required this.totalBalance,
    required this.monthIncome,
    required this.monthExpense,
    required this.monthBalance,
  });
}
