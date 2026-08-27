import 'package:flutter/material.dart';

/// 💰 1. 개별 납부 거래 내역 모델 (/api/v1/ledger/payment/)
class PaymentTransactionItemModel {
  final int pk;
  final int? dealId;
  final String? contractorName;
  final String? unitStr;
  final String? unitTypeName;
  final String? unitTypeColor;
  final int? contractId;
  final int? installmentOrderId;
  final int? accountingEntryId;
  final int? bankTransactionId;
  final bool isPaymentMismatch;
  final String? payName;
  final int amount;
  final String dealDate;
  final String? bankAccountName;
  final String? trader;
  final String? note;

  PaymentTransactionItemModel({
    required this.pk,
    this.dealId,
    this.contractorName,
    this.unitStr,
    this.unitTypeName,
    this.unitTypeColor,
    this.contractId,
    this.installmentOrderId,
    this.accountingEntryId,
    this.bankTransactionId,
    this.isPaymentMismatch = false,
    this.payName,
    required this.amount,
    required this.dealDate,
    this.bankAccountName,
    this.trader,
    this.note,
  });

  factory PaymentTransactionItemModel.fromJson(Map<String, dynamic> json) {
    // contract 객체/ID 파싱
    final contractRaw = json['contract'];
    final contract = contractRaw is Map ? contractRaw : null;
    final int? parsedContractId = contract != null ? (contract['pk'] ?? contract['id']) : (contractRaw is int ? contractRaw : json['contract_id']);

    final contractor = contract != null && contract['contractor'] is Map ? contract['contractor'] : null;
    final unitType = contract != null && contract['unit_type'] is Map ? contract['unit_type'] : null;
    final keyUnit = contract != null && contract['key_unit'] is Map ? contract['key_unit'] : null;
    final houseunit = keyUnit != null && keyUnit['houseunit'] is Map ? keyUnit['houseunit'] : null;

    // installment_order 객체/ID 파싱
    final installRaw = json['installment_order'];
    final installmentOrder = installRaw is Map ? installRaw : null;
    final int? parsedInstallOrderId = installmentOrder != null
        ? (installmentOrder['pk'] ?? installmentOrder['id'])
        : (installRaw is int ? installRaw : json['installment_order_id']);

    // accounting_entry 파싱
    final entryRaw = json['accounting_entry'];
    final int? parsedEntryId = entryRaw is Map ? (entryRaw['pk'] ?? entryRaw['id']) : (entryRaw is int ? entryRaw : null);

    // bank_account 파싱
    final bankAcc = json['bank_account'] is Map ? json['bank_account'] : null;

    String? parsedUnit;
    if (houseunit != null) {
      final name = houseunit['name']?.toString() ?? '';
      final bldg = houseunit['building_unit']?.toString() ?? '';
      parsedUnit = bldg.isNotEmpty ? '$bldg동 $name호' : name;
    } else if (contract != null && contract['serial_number'] != null) {
      parsedUnit = contract['serial_number'];
    }

    return PaymentTransactionItemModel(
      pk: json['pk'] ?? json['id'] ?? 0,
      dealId: json['deal_id'],
      contractorName: contractor != null ? contractor['name'] : (json['contractor_name'] ?? json['trader']),
      unitStr: parsedUnit ?? (json['unit_desc'] ?? (parsedContractId == null ? '계약 미매칭' : '-')),
      unitTypeName: unitType != null ? unitType['name'] : json['unit_type_name'],
      unitTypeColor: unitType != null ? unitType['color'] : json['unit_type_color'],
      contractId: parsedContractId,
      installmentOrderId: parsedInstallOrderId,
      accountingEntryId: parsedEntryId,
      bankTransactionId: json['bank_transaction_id'] ?? json['bank_transaction']?['pk'],
      isPaymentMismatch: json['is_payment_mismatch'] ?? false,
      payName: installmentOrder != null ? installmentOrder['pay_name'] : (json['pay_name'] ?? (parsedInstallOrderId == null ? null : '-')),
      amount: (json['income'] ?? json['amount'] ?? 0) as int,
      dealDate: json['deal_date']?.toString() ?? '',
      bankAccountName: bankAcc != null ? (bankAcc['alias_name'] ?? bankAcc['bank_name']) : json['bank_account_name'],
      trader: json['trader']?.toString(),
      note: json['note']?.toString(),
    );
  }

  /// 계약 미매칭 여부
  bool get isContractUnmatched => contractId == null;

  /// 회차 미매칭 여부 (계약은 있으나 납부 회차가 없음)
  bool get isInstallmentUnmatched => contractId != null && installmentOrderId == null;

  /// 정상 매칭 완료 여부
  bool get isFullyMatched => contractId != null && installmentOrderId != null;

  /// 배지 배경색: 타입 원색 그대로 사용 (불투명)
  Color get typeBadgeBgColor {
    if (unitTypeColor == null || unitTypeColor!.isEmpty) {
      return const Color(0xFF64748B);
    }
    try {
      final hex = unitTypeColor!.replaceAll('#', '');
      return Color(int.parse('FF$hex', radix: 16));
    } catch (_) {
      return const Color(0xFF64748B);
    }
  }

  /// 배지 텍스트색: 배경 밝기에 따라 흰색 또는 다크 자동 선택
  Color get typeBadgeTextColor {
    final bg = typeBadgeBgColor;
    // 상대 휘도 기준 (W3C WCAG): 0.179 임계값
    final luminance = bg.computeLuminance();
    return luminance > 0.179 ? const Color(0xFF1E293B) : Colors.white;
  }
}

/// 📊 2. 회차별 수납 현황 모델 (/api/v1/overall-summary/)
class InstallmentStatusItemModel {
  final int orderId;
  final int payCode;
  final int payTime;
  final String payName;
  final String? aliasName;
  final String? payDueDate;
  final int payAmt;
  final double payRatio;
  final bool isExceptPrice;
  final int totalDueAmount;       // 약정 합계금액
  final int totalPaidAmount;      // 실제 수납금액
  final int unpaidAmount;         // 미납액
  final double collectionRate;    // 수납률 (%)
  final int paidCount;            // 완납 세대수
  final int totalCount;           // 대상 세대수

  InstallmentStatusItemModel({
    required this.orderId,
    required this.payCode,
    required this.payTime,
    required this.payName,
    this.aliasName,
    this.payDueDate,
    required this.payAmt,
    required this.payRatio,
    required this.isExceptPrice,
    required this.totalDueAmount,
    required this.totalPaidAmount,
    required this.unpaidAmount,
    required this.collectionRate,
    required this.paidCount,
    required this.totalCount,
  });

  factory InstallmentStatusItemModel.fromJson(Map<String, dynamic> json) {
    final collection = json['collection'] is Map ? json['collection'] : null;
    final duePeriod = json['due_period'] is Map ? json['due_period'] : null;

    final totalDue = (json['contract_amount'] ?? json['total_due_amount'] ?? json['amount'] ?? 0) as int;
    final totalPaid = collection != null
        ? (collection['actual_collected'] ?? collection['collected_amount'] ?? 0) as int
        : (json['actual_collected'] ?? json['total_paid_amount'] ?? json['paid_amount'] ?? 0) as int;
    final unpaid = (json['total_unpaid'] ?? (duePeriod != null ? duePeriod['unpaid_amount'] : null) ?? (totalDue > totalPaid ? totalDue - totalPaid : 0)) as int;
    
    double rate = 0.0;
    if (collection != null && collection['collection_rate'] != null) {
      rate = double.tryParse(collection['collection_rate'].toString()) ?? 0.0;
    } else if (json['collection_rate'] != null) {
      rate = double.tryParse(json['collection_rate'].toString()) ?? 0.0;
    } else if (totalDue > 0) {
      rate = (totalPaid / totalDue) * 100;
    }

    return InstallmentStatusItemModel(
      orderId: json['pk'] ?? json['id'] ?? 0,
      payCode: json['pay_code'] ?? 0,
      payTime: json['pay_time'] ?? 0,
      payName: json['pay_name']?.toString() ?? '',
      aliasName: json['alias_name']?.toString(),
      payDueDate: json['pay_due_date']?.toString(),
      payAmt: (json['pay_amt'] ?? 0) as int,
      payRatio: (json['pay_ratio'] is num) ? (json['pay_ratio'] as num).toDouble() : 0.0,
      isExceptPrice: json['is_except_price'] ?? false,
      totalDueAmount: totalDue,
      totalPaidAmount: totalPaid,
      unpaidAmount: unpaid,
      collectionRate: rate,
      paidCount: json['paid_count'] ?? 0,
      totalCount: json['total_count'] ?? 0,
    );
  }

  String get displayDueDate => (payDueDate != null && payDueDate!.isNotEmpty) ? payDueDate! : '일정 미지정';
}

/// 📈 3. 수납 종합 집계 KPI 모델
class PaymentOverallAggregateModel {
  final int totalBudget;          // 총 매출예산 (A) — 전체 공급 가능 금액
  final int totalContractAmount;  // 총 분양금액 (B) — 계약된 금액 합계
  final int totalPaidAmount;      // 총 수납금액 (C) — 실제 수납된 금액
  final int totalUnpaidAmount;    // 미수납금액 (B-C) — 계약됐으나 미납
  final int unsoldAmount;         // 미분양금액 (A-B) — 미계약 공급가
  final double paymentRate;       // 전체 수납률 (%)
  final int totalUnits;           // 총 세대수
  final int contractedUnits;      // 계약 세대수

  PaymentOverallAggregateModel({
    required this.totalBudget,
    required this.totalContractAmount,
    required this.totalPaidAmount,
    required this.totalUnpaidAmount,
    required this.unsoldAmount,
    required this.paymentRate,
    required this.totalUnits,
    required this.contractedUnits,
  });

  factory PaymentOverallAggregateModel.fromJson(Map<String, dynamic> json) {
    final budget = (json['total_budget'] ?? json['total_sales_price'] ?? 0) as int;
    final contractAmt = (json['total_contract_amount'] ?? 0) as int;
    final totalPaid = (json['total_paid_amount'] ?? json['total_paid'] ?? json['total_collected'] ?? 0) as int;
    final unpaid = (json['unpaid_amount'] ?? (contractAmt > totalPaid ? contractAmt - totalPaid : 0)) as int;
    final unsold = (json['unsold_amount'] ?? (budget > contractAmt ? budget - contractAmt : 0)) as int;
    final rate = (json['payment_rate'] is num)
        ? (json['payment_rate'] as num).toDouble()
        : (contractAmt > 0 ? (totalPaid / contractAmt) * 100 : 0.0);

    return PaymentOverallAggregateModel(
      totalBudget: budget,
      totalContractAmount: contractAmt,
      totalPaidAmount: totalPaid,
      totalUnpaidAmount: unpaid,
      unsoldAmount: unsold,
      paymentRate: rate,
      totalUnits: json['total_units'] ?? 0,
      contractedUnits: json['conts_num'] ?? 0,
    );
  }
}
