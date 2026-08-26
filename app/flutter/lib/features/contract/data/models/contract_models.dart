/// 계약 관리 데이터 모델 (Contract Models)

class ContractAggregateModel {
  final int totalUnits;
  final int subsNum;
  final int contsNum;
  final int nonContsNum;

  ContractAggregateModel({
    required this.totalUnits,
    required this.subsNum,
    required this.contsNum,
    required this.nonContsNum,
  });

  factory ContractAggregateModel.fromJson(Map<String, dynamic> json) {
    return ContractAggregateModel(
      totalUnits: json['total_units'] ?? 0,
      subsNum: json['subs_num'] ?? 0,
      contsNum: json['conts_num'] ?? 0,
      nonContsNum: json['non_conts_num'] ?? 0,
    );
  }

  double get contractRate =>
      totalUnits > 0 ? (contsNum / totalUnits) * 100 : 0.0;
}

class HouseUnitModel {
  final int pk;
  final String str;
  final String? floorType;

  HouseUnitModel({
    required this.pk,
    required this.str,
    this.floorType,
  });

  factory HouseUnitModel.fromJson(Map<String, dynamic> json) {
    return HouseUnitModel(
      pk: json['pk'] ?? 0,
      str: json['__str__'] ?? '',
      floorType: json['floor_type']?.toString(),
    );
  }
}

class KeyUnitModel {
  final int pk;
  final String unitCode;
  final HouseUnitModel? houseunit;

  KeyUnitModel({
    required this.pk,
    required this.unitCode,
    this.houseunit,
  });

  factory KeyUnitModel.fromJson(Map<String, dynamic> json) {
    return KeyUnitModel(
      pk: json['pk'] ?? 0,
      unitCode: json['unit_code'] ?? '',
      houseunit: json['houseunit'] != null
          ? HouseUnitModel.fromJson(json['houseunit'])
          : null,
    );
  }
}

class ContractorContactModel {
  final int? pk;
  final String? cellPhone;
  final String? homePhone;
  final String? otherPhone;
  final String? email;

  ContractorContactModel({
    this.pk,
    this.cellPhone,
    this.homePhone,
    this.otherPhone,
    this.email,
  });

  factory ContractorContactModel.fromJson(Map<String, dynamic> json) {
    return ContractorContactModel(
      pk: json['pk'],
      cellPhone: json['cell_phone'],
      homePhone: json['home_phone'],
      otherPhone: json['other_phone'],
      email: json['email'],
    );
  }
}

class ContractorAddressModel {
  final int? pk;
  final String? idZipcode;
  final String? idAddress1;
  final String? idAddress2;
  final String? idAddress3;
  final String? dmZipcode;
  final String? dmAddress1;
  final String? dmAddress2;
  final String? dmAddress3;

  ContractorAddressModel({
    this.pk,
    this.idZipcode,
    this.idAddress1,
    this.idAddress2,
    this.idAddress3,
    this.dmZipcode,
    this.dmAddress1,
    this.dmAddress2,
    this.dmAddress3,
  });

  factory ContractorAddressModel.fromJson(Map<String, dynamic> json) {
    return ContractorAddressModel(
      pk: json['pk'],
      idZipcode: json['id_zipcode'],
      idAddress1: json['id_address1'],
      idAddress2: json['id_address2'],
      idAddress3: json['id_address3'],
      dmZipcode: json['dm_zipcode'],
      dmAddress1: json['dm_address1'],
      dmAddress2: json['dm_address2'],
      dmAddress3: json['dm_address3'],
    );
  }
}

class ContractorModel {
  final int pk;
  final String name;
  final String? birthDate;
  final String? gender;
  final String? qualification;
  final String? qualifiDisplay;
  final String? status;
  final String? changeType;
  final String? reservationDate;
  final String? contractDate;
  final bool isActive;
  final String? note;
  final ContractorContactModel? contact;
  final ContractorAddressModel? address;

  ContractorModel({
    required this.pk,
    required this.name,
    this.birthDate,
    this.gender,
    this.qualification,
    this.qualifiDisplay,
    this.status,
    this.changeType,
    this.reservationDate,
    this.contractDate,
    required this.isActive,
    this.note,
    this.contact,
    this.address,
  });

  factory ContractorModel.fromJson(Map<String, dynamic> json) {
    return ContractorModel(
      pk: json['pk'] ?? 0,
      name: json['name'] ?? '',
      birthDate: json['birth_date'],
      gender: json['gender'],
      qualification: json['qualification'],
      qualifiDisplay: json['qualifi_display'],
      status: json['status'],
      changeType: json['change_type'],
      reservationDate: json['reservation_date'],
      contractDate: json['contract_date'],
      isActive: json['is_active'] ?? true,
      note: json['note'],
      contact: json['contractorcontact'] != null
          ? ContractorContactModel.fromJson(json['contractorcontact'])
          : null,
      address: json['contractoraddress'] != null
          ? ContractorAddressModel.fromJson(json['contractoraddress'])
          : null,
    );
  }
}

class ContractPriceModel {
  final int? pk;
  final int price;
  final int? priceBuild;
  final int? priceLand;
  final int? priceTax;

  ContractPriceModel({
    this.pk,
    required this.price,
    this.priceBuild,
    this.priceLand,
    this.priceTax,
  });

  factory ContractPriceModel.fromJson(Map<String, dynamic> json) {
    return ContractPriceModel(
      pk: json['pk'],
      price: json['price'] ?? 0,
      priceBuild: json['price_build'],
      priceLand: json['price_land'],
      priceTax: json['price_tax'],
    );
  }
}

class ContractItemModel {
  final int pk;
  final int project;
  final int? orderGroup;
  final String? orderGroupSort;
  final String? orderGroupName;
  final int? unitType;
  final String? unitTypeName;
  final String? unitTypeColor;
  final String? serialNumber;
  final bool isActive;
  final bool isCompleted;
  final bool isSupCont;
  final String? supContDate;
  final KeyUnitModel? keyUnit;
  final ContractorModel? contractor;
  final ContractPriceModel? contractPrice;
  final int totalPaid;
  final String? lastPaidOrderName;

  ContractItemModel({
    required this.pk,
    required this.project,
    this.orderGroup,
    this.orderGroupSort,
    this.orderGroupName,
    this.unitType,
    this.unitTypeName,
    this.unitTypeColor,
    this.serialNumber,
    required this.isActive,
    required this.isCompleted,
    required this.isSupCont,
    this.supContDate,
    this.keyUnit,
    this.contractor,
    this.contractPrice,
    required this.totalPaid,
    this.lastPaidOrderName,
  });

  factory ContractItemModel.fromJson(Map<String, dynamic> json) {
    final orderDesc = json['order_group_desc'];
    final unitDesc = json['unit_type_desc'];
    final lastPaid = json['last_paid_order'];

    return ContractItemModel(
      pk: json['pk'] ?? 0,
      project: json['project'] ?? 0,
      orderGroup: json['order_group'],
      orderGroupSort: json['order_group_sort'],
      orderGroupName: orderDesc != null ? orderDesc['name'] : null,
      unitType: json['unit_type'],
      unitTypeName: unitDesc != null ? unitDesc['name'] : null,
      unitTypeColor: unitDesc != null ? unitDesc['color'] : null,
      serialNumber: json['serial_number'],
      isActive: json['is_active'] ?? true,
      isCompleted: json['is_completed'] ?? false,
      isSupCont: json['is_sup_cont'] ?? false,
      supContDate: json['sup_cont_date'],
      keyUnit: json['key_unit'] != null
          ? KeyUnitModel.fromJson(json['key_unit'])
          : null,
      contractor: json['contractor'] != null
          ? ContractorModel.fromJson(json['contractor'])
          : null,
      contractPrice: json['contractprice'] != null
          ? ContractPriceModel.fromJson(json['contractprice'])
          : null,
      totalPaid: json['total_paid'] ?? 0,
      lastPaidOrderName: lastPaid != null ? lastPaid['pay_name'] : null,
    );
  }

  String get displayUnit => keyUnit?.houseunit?.str.isNotEmpty == true
      ? keyUnit!.houseunit!.str
      : '동호 미지정';

  int get price => contractPrice?.price ?? 0;

  int get remainingAmount => price > totalPaid ? price - totalPaid : 0;

  double get paymentRate => price > 0 ? (totalPaid / price) * 100 : 0.0;
}

/// ── 권리의무 승계 데이터 모델 (Succession Model) ─────────────────────────
class SuccessionItemModel {
  final int pk;
  final int? contractId;
  final String? serialNumber;
  final String sellerName;
  final String buyerName;
  final String? buyerBirthDate;
  final String? buyerCellPhone;
  final String applyDate;
  final String? tradingDate;
  final String status; // '1': 신청접수, '2': 변경인가대기, '3': 변경인가완료(승계완료), '9': 승계취소
  final String? approvalDate;
  final String? note;

  SuccessionItemModel({
    required this.pk,
    this.contractId,
    this.serialNumber,
    required this.sellerName,
    required this.buyerName,
    this.buyerBirthDate,
    this.buyerCellPhone,
    required this.applyDate,
    this.tradingDate,
    required this.status,
    this.approvalDate,
    this.note,
  });

  factory SuccessionItemModel.fromJson(Map<String, dynamic> json) {
    final contract = json['contract'];
    final seller = json['seller'];
    final buyer = json['buyer'];
    final buyerContact = buyer != null ? buyer['contractorcontact'] : null;

    return SuccessionItemModel(
      pk: json['pk'] ?? 0,
      contractId: contract != null ? contract['pk'] : null,
      serialNumber: contract != null ? contract['serial_number'] : null,
      sellerName: seller != null ? (seller['name'] ?? '') : '',
      buyerName: buyer != null ? (buyer['name'] ?? '') : '',
      buyerBirthDate: buyer != null ? buyer['birth_date'] : null,
      buyerCellPhone: buyerContact != null ? buyerContact['cell_phone'] : null,
      applyDate: json['apply_date'] ?? '',
      tradingDate: json['trading_date'],
      status: json['status']?.toString() ?? '1',
      approvalDate: json['approval_date'],
      note: json['note'],
    );
  }

  String get statusDisplay {
    switch (status) {
      case '1':
        return '신청접수';
      case '2':
        return '변경인가대기';
      case '3':
        return '승계완료';
      case '9':
        return '승계취소';
      default:
        return '처리중';
    }
  }
}

/// ── 계약 해약 관리 데이터 모델 (ContractorRelease Model) ──────────────────
class ContractorReleaseItemModel {
  final int pk;
  final int project;
  final int contractorId;
  final String contractorName;
  final String requestDate;
  final String releaseType;
  final String status; // '0': 신청취소, '1': 해지신청, '2': 정산완료, '3': 환불완료, '4': 해지확정
  final int? refundAmount;
  final String? refundAccountBank;
  final String? refundAccountNumber;
  final String? refundAccountDepositor;
  final String? refundCompletionDate;
  final String? completionDate;
  final String? note;

  ContractorReleaseItemModel({
    required this.pk,
    required this.project,
    required this.contractorId,
    required this.contractorName,
    required this.requestDate,
    required this.releaseType,
    required this.status,
    this.refundAmount,
    this.refundAccountBank,
    this.refundAccountNumber,
    this.refundAccountDepositor,
    this.refundCompletionDate,
    this.completionDate,
    this.note,
  });

  factory ContractorReleaseItemModel.fromJson(Map<String, dynamic> json) {
    return ContractorReleaseItemModel(
      pk: json['pk'] ?? 0,
      project: json['project'] ?? 0,
      contractorId: json['contractor'] is int ? json['contractor'] : 0,
      contractorName: json['__str__'] ?? '',
      requestDate: json['request_date'] ?? '',
      releaseType: json['release_type']?.toString() ?? '1',
      status: json['status']?.toString() ?? '1',
      refundAmount: json['refund_amount'],
      refundAccountBank: json['refund_account_bank'],
      refundAccountNumber: json['refund_account_number'],
      refundAccountDepositor: json['refund_account_depositor'],
      refundCompletionDate: json['refund_completion_date'],
      completionDate: json['completion_date'],
      note: json['note'],
    );
  }

  String get statusDisplay {
    switch (status) {
      case '0':
        return '신청취소';
      case '1':
        return '해지신청';
      case '2':
        return '정산완료';
      case '3':
        return '환불완료';
      case '4':
        return '해지확정';
      default:
        return '처리중';
    }
  }
}
