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

  Color get sortColor {
    if (isIncome) return const Color(0xFF10B981); // 수입 (초록)
    if (isExpense) return const Color(0xFFEF4444); // 지출 (빨강)
    return const Color(0xFF38BDF8);                // 대체/이체 (파랑)
  }

  String get sortSign => isIncome ? '+' : (isExpense ? '-' : '');
}

/// 📑 3. 회계 분개 항목 모델 (복식부기 항목)
class ProjectAccountingEntryModel {
  final int pk;
  final int? accountId;
  final String? accountName;
  final int amount;
  final String? trader;

  ProjectAccountingEntryModel({
    required this.pk,
    this.accountId,
    this.accountName,
    required this.amount,
    this.trader,
  });

  factory ProjectAccountingEntryModel.fromJson(Map<String, dynamic> json) {
    return ProjectAccountingEntryModel(
      pk: json['pk'] ?? json['id'] ?? 0,
      accountId: json['account'] is int ? json['account'] : (json['account'] is Map ? json['account']['pk'] : null),
      accountName: json['account_desc'] ?? (json['account'] is Map ? json['account']['name'] : null),
      amount: (json['amount'] ?? 0) as int,
      trader: json['trader']?.toString(),
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

/// 📈 5. 회계 자금 종합 요약 KPI 모델
class LedgerOverallAggregateModel {
  final int totalBalance;     // 총 잔고액
  final int totalIncome;      // 총 수입 누계
  final int totalExpense;     // 총 지출 누계
  final int currentBalance;   // 당월/당기 수지차

  LedgerOverallAggregateModel({
    required this.totalBalance,
    required this.totalIncome,
    required this.totalExpense,
    required this.currentBalance,
  });
}
