/// 📊 0. 부지 종합 집계 현황 모델
class SiteAggregateModel {
  final int totalSitesCount;          // 총 필지 수
  final double totalOfficialArea;     // 공부상 총면적 (㎡)
  final double totalReturnedArea;     // 환지 총면적 (㎡)
  final bool isReturnedArea;          // 환지방식 여부 (동춘 등 환지사업은 환지면적이 사업대상)
  final int totalOwnersCount;         // 총 소유자 수
  final int totalContractsCount;      // 총 계약 체결 건수
  final double totalContractedArea;   // 계약 완료 총면적 (㎡)
  final int totalPrice;               // 총 매입계약 금액 (원)

  SiteAggregateModel({
    required this.totalSitesCount,
    required this.totalOfficialArea,
    required this.totalReturnedArea,
    this.isReturnedArea = false,
    required this.totalOwnersCount,
    required this.totalContractsCount,
    required this.totalContractedArea,
    required this.totalPrice,
  });

  /// 실제 사업 기준 총 대상면적 (환지방식이면 환지면적, 아니면 공부상면적)
  double get targetTotalArea {
    if (isReturnedArea && totalReturnedArea > 0) {
      return totalReturnedArea;
    }
    return totalOfficialArea;
  }

  /// 대상면적 기준 평수 환산
  double get targetTotalPyung => targetTotalArea / 3.305785;
  double get totalContractedPyung => totalContractedArea / 3.305785;

  /// 미계약 면적 (㎡)
  double get uncontractedArea {
    final diff = targetTotalArea - totalContractedArea;
    return diff < 0 ? 0.0 : diff;
  }

  /// 면적 확보율 / 계약율 (%) - 최대 100%
  double get securedAreaRate {
    if (targetTotalArea <= 0) return 0.0;
    final rate = (totalContractedArea / targetTotalArea) * 100;
    return rate > 100 ? 100.0 : rate;
  }
}

/// 📁 부지 첨부파일 (등기사항전부증명서 등본) 모델
class SiteInfoFileModel {
  final int pk;
  final String file;
  final String fileName;
  final int? fileSize;
  final String created;

  SiteInfoFileModel({
    required this.pk,
    required this.file,
    required this.fileName,
    this.fileSize,
    required this.created,
  });

  factory SiteInfoFileModel.fromJson(Map<String, dynamic> json) {
    return SiteInfoFileModel(
      pk: json['pk'] ?? json['id'] ?? 0,
      file: json['file']?.toString() ?? '',
      fileName: json['file_name']?.toString() ?? '등기부등본.pdf',
      fileSize: json['file_size'] as int?,
      created: json['created']?.toString() ?? '',
    );
  }
}

/// 📌 1. 필지 / 지번 모델 (/api/v1/site/)
class SiteItemModel {
  final int pk;
  final int project;
  final int order;
  final String district;              // 행정동 (예: 동춘동)
  final String lotNumber;             // 지번 (예: 123-4)
  final String sitePurpose;           // 지목 (대, 답, 전 등)
  final double officialArea;          // 대지면적 (㎡)
  final double? returnedArea;         // 환지면적 (㎡)
  final int? noticePrice;             // 공시지가
  final String rightsA;               // 갑구 권리제한
  final String rightsB;               // 을구 권리제한
  final String? dupIssueDate;         // 등본발급일
  final List<SiteOwnerInSiteModel> owners; // 소유자 목록
  final List<SiteInfoFileModel> siteInfoFiles; // 등기사항전부증명서 첨부파일
  final String note;                  // 비고

  SiteItemModel({
    required this.pk,
    required this.project,
    required this.order,
    required this.district,
    required this.lotNumber,
    required this.sitePurpose,
    required this.officialArea,
    this.returnedArea,
    this.noticePrice,
    required this.rightsA,
    required this.rightsB,
    this.dupIssueDate,
    this.owners = const [],
    this.siteInfoFiles = const [],
    required this.note,
  });

  factory SiteItemModel.fromJson(Map<String, dynamic> json) {
    final rawOwners = json['owners'] as List<dynamic>? ?? [];
    final ownersList = rawOwners
        .whereType<Map<String, dynamic>>()
        .map((e) => SiteOwnerInSiteModel.fromJson(e))
        .toList();

    final rawFiles = json['site_info_files'] as List<dynamic>? ?? [];
    final filesList = rawFiles
        .whereType<Map<String, dynamic>>()
        .map((e) => SiteInfoFileModel.fromJson(e))
        .toList();

    return SiteItemModel(
      pk: json['pk'] ?? json['id'] ?? 0,
      project: json['project'] ?? 0,
      order: json['order'] ?? 0,
      district: json['district']?.toString() ?? '',
      lotNumber: json['lot_number']?.toString() ?? '',
      sitePurpose: json['site_purpose']?.toString() ?? '',
      officialArea: double.tryParse(json['official_area']?.toString() ?? '') ?? 0.0,
      returnedArea: double.tryParse(json['returned_area']?.toString() ?? ''),
      noticePrice: json['notice_price'] as int?,
      rightsA: json['rights_a']?.toString() ?? '',
      rightsB: json['rights_b']?.toString() ?? '',
      dupIssueDate: json['dup_issue_date']?.toString(),
      owners: ownersList,
      siteInfoFiles: filesList,
      note: json['note']?.toString() ?? '',
    );
  }

  /// 평수 환산
  double get pyungArea => officialArea / 3.305785;

  /// 등기부등본 파일 보유 여부
  bool get hasRegisterFile => siteInfoFiles.isNotEmpty && siteInfoFiles.first.file.isNotEmpty;

  /// 대표 소유자 명칭
  String get displayOwnerSummary {
    if (owners.isEmpty) return '소유자 미등록';
    if (owners.length == 1) return owners.first.owner;
    return '${owners.first.owner} 외 ${owners.length - 1}명';
  }
}

/// 필지 내 소유자 정보 간이 모델
class SiteOwnerInSiteModel {
  final int pk;
  final String owner;
  final String? ownSortDesc;

  SiteOwnerInSiteModel({
    required this.pk,
    required this.owner,
    this.ownSortDesc,
  });

  factory SiteOwnerInSiteModel.fromJson(Map<String, dynamic> json) {
    return SiteOwnerInSiteModel(
      pk: json['pk'] ?? json['id'] ?? 0,
      owner: json['owner']?.toString() ?? '',
      ownSortDesc: json['own_sort_desc']?.toString(),
    );
  }
}

/// 👤 2. 토지 소유자 모델 (/api/v1/site-owner/)
class SiteOwnerItemModel {
  final int pk;
  final int project;
  final String owner;                 // 소유자 성명/법인명
  final bool useConsent;              // 사용동의 여부
  final String? dateOfBirth;          // 생년월일
  final String phone1;                // 주연락처
  final String phone2;                // 비상연락처
  final String zipcode;               // 우편번호
  final String address1;              // 주소
  final String address2;              // 상세주소
  final String address3;              // 참고항목
  final String ownSort;               // '1': 개인, '2': 법인, '3': 국공유지
  final String? ownSortDesc;          // 소유구분 명칭
  final List<RelationsInSiteOwnerModel> sites; // 소유 필지 목록
  final List<SiteOwnerConsultationLogModel> consultationLogs; // 상담 기록 목록
  final String note;                  // 특이사항

  SiteOwnerItemModel({
    required this.pk,
    required this.project,
    required this.owner,
    this.useConsent = false,
    this.dateOfBirth,
    required this.phone1,
    required this.phone2,
    required this.zipcode,
    required this.address1,
    required this.address2,
    required this.address3,
    required this.ownSort,
    this.ownSortDesc,
    this.sites = const [],
    this.consultationLogs = const [],
    required this.note,
  });

  factory SiteOwnerItemModel.fromJson(Map<String, dynamic> json) {
    final rawSites = json['sites'] as List<dynamic>? ?? [];
    final sitesList = rawSites
        .whereType<Map<String, dynamic>>()
        .map((e) => RelationsInSiteOwnerModel.fromJson(e))
        .toList();

    final rawLogs = json['consultation_logs'] as List<dynamic>? ?? [];
    final logsList = rawLogs
        .whereType<Map<String, dynamic>>()
        .map((e) => SiteOwnerConsultationLogModel.fromJson(e))
        .toList();

    return SiteOwnerItemModel(
      pk: json['pk'] ?? json['id'] ?? 0,
      project: json['project'] ?? 0,
      owner: json['owner']?.toString() ?? '',
      useConsent: json['use_consent'] == true,
      dateOfBirth: json['date_of_birth']?.toString(),
      phone1: json['phone1']?.toString() ?? '',
      phone2: json['phone2']?.toString() ?? '',
      zipcode: json['zipcode']?.toString() ?? '',
      address1: json['address1']?.toString() ?? '',
      address2: json['address2']?.toString() ?? '',
      address3: json['address3']?.toString() ?? '',
      ownSort: json['own_sort']?.toString() ?? '1',
      ownSortDesc: json['own_sort_desc']?.toString(),
      sites: sitesList,
      consultationLogs: logsList,
      note: json['note']?.toString() ?? '',
    );
  }

  /// 소유 필지 대표 명칭 (예: 동춘동 123-4 외 2필지)
  String get displaySiteSummary {
    if (sites.isEmpty) return '소유 필지 없음';
    final firstName = sites.first.siteName;
    if (sites.length == 1) return firstName;
    return '$firstName 외 ${sites.length - 1}필지';
  }

  /// 소유 총 면적 합산 (㎡)
  double get totalOwnedArea {
    return sites.fold(0.0, (sum, s) => sum + (s.ownedArea ?? 0.0));
  }
}

/// 💬 토지 소유자 상담/협의 기록 모델 (/api/v1/site-owner-consultations/)
class SiteOwnerConsultationLogModel {
  final int pk;
  final int siteOwner;
  final String consultationDate;
  final String channel;               // 'phone', 'visit', 'kakao', 'sms', 'email', 'other'
  final String? channelDisplay;
  final String title;
  final String content;
  final String? consultantName;
  final bool followUpRequired;
  final String? followUpNote;
  final String? completionDate;
  final String? created;

  SiteOwnerConsultationLogModel({
    required this.pk,
    required this.siteOwner,
    required this.consultationDate,
    required this.channel,
    this.channelDisplay,
    required this.title,
    required this.content,
    this.consultantName,
    this.followUpRequired = false,
    this.followUpNote,
    this.completionDate,
    this.created,
  });

  factory SiteOwnerConsultationLogModel.fromJson(Map<String, dynamic> json) {
    final consultant = json['consultant'];
    String? consultantName;
    if (consultant is Map) {
      consultantName = consultant['username']?.toString();
    }

    return SiteOwnerConsultationLogModel(
      pk: json['pk'] ?? json['id'] ?? 0,
      siteOwner: json['site_owner'] is int ? json['site_owner'] : 0,
      consultationDate: json['consultation_date']?.toString() ?? '',
      channel: json['channel']?.toString() ?? 'phone',
      channelDisplay: json['channel_display']?.toString(),
      title: json['title']?.toString() ?? '',
      content: json['content']?.toString() ?? '',
      consultantName: consultantName,
      followUpRequired: json['follow_up_required'] == true,
      followUpNote: json['follow_up_note']?.toString(),
      completionDate: json['completion_date']?.toString(),
      created: json['created']?.toString(),
    );
  }

  String get channelKorean {
    if (channelDisplay != null && channelDisplay!.isNotEmpty) return channelDisplay!;
    switch (channel) {
      case 'phone':
        return '전화';
      case 'visit':
        return '방문';
      case 'kakao':
        return '카카오톡';
      case 'sms':
        return '문자';
      case 'email':
        return '이메일';
      default:
        return '기타';
    }
  }
}

/// 소유자-필지 관계 모델
class RelationsInSiteOwnerModel {
  final int pk;
  final int siteId;
  final String siteName;              // 필지 지번 (__str__)
  final double? ownershipRatio;       // 소유지분
  final double? ownedArea;            // 소유면적 (㎡)
  final String? acquisitionDate;      // 취득일자

  RelationsInSiteOwnerModel({
    required this.pk,
    required this.siteId,
    required this.siteName,
    this.ownershipRatio,
    this.ownedArea,
    this.acquisitionDate,
  });

  factory RelationsInSiteOwnerModel.fromJson(Map<String, dynamic> json) {
    return RelationsInSiteOwnerModel(
      pk: json['pk'] ?? json['id'] ?? 0,
      siteId: json['site'] ?? 0,
      siteName: json['__str__']?.toString() ?? '필지',
      ownershipRatio: double.tryParse(json['ownership_ratio']?.toString() ?? ''),
      ownedArea: double.tryParse(json['owned_area']?.toString() ?? ''),
      acquisitionDate: json['acquisition_date']?.toString(),
    );
  }
}

/// 📑 3. 사업부지 매입 계약 모델 (/api/v1/site-contract/)
class SiteContractItemModel {
  final int pk;
  final int project;
  final int ownerId;
  final String ownerName;             // 매도인 (소유자 성명)
  final String contractDate;          // 계약체결일
  final int totalPrice;               // 총 매매대금 (원)
  final double contractArea;          // 계약면적 (㎡)
  final int? downPay1;                // 계약금1
  final String? downPay1Date;
  final bool downPay1IsPaid;
  final int? downPay2;                // 계약금2
  final String? downPay2Date;
  final bool downPay2IsPaid;
  final int? interPay1;               // 중도금1
  final String? interPay1Date;
  final bool interPay1IsPaid;
  final int? interPay2;               // 중도금2
  final String? interPay2Date;
  final bool interPay2IsPaid;
  final int? remainPay;               // 잔금
  final String? remainPayDate;
  final bool remainPayIsPaid;
  final bool ownershipCompletion;     // 소유권 확보(등기) 완료 여부
  final String accBank;               // 수령 은행
  final String accNumber;             // 계좌번호
  final String accOwner;              // 예금주
  final List<SiteInfoFileModel> siteContFiles; // 매매계약서 첨부파일
  final String note;                  // 특이사항

  SiteContractItemModel({
    required this.pk,
    required this.project,
    required this.ownerId,
    required this.ownerName,
    required this.contractDate,
    required this.totalPrice,
    required this.contractArea,
    this.downPay1,
    this.downPay1Date,
    this.downPay1IsPaid = false,
    this.downPay2,
    this.downPay2Date,
    this.downPay2IsPaid = false,
    this.interPay1,
    this.interPay1Date,
    this.interPay1IsPaid = false,
    this.interPay2,
    this.interPay2Date,
    this.interPay2IsPaid = false,
    this.remainPay,
    this.remainPayDate,
    this.remainPayIsPaid = false,
    this.ownershipCompletion = false,
    required this.accBank,
    required this.accNumber,
    required this.accOwner,
    this.siteContFiles = const [],
    required this.note,
  });

  factory SiteContractItemModel.fromJson(Map<String, dynamic> json) {
    String parsedOwnerName = '소유자';
    if (json['owner_desc'] is Map) {
      parsedOwnerName = json['owner_desc']['owner']?.toString() ?? '소유자';
    } else if (json['owner'] != null) {
      parsedOwnerName = json['owner'].toString();
    }

    final rawFiles = json['site_cont_files'] as List<dynamic>? ?? [];
    final filesList = rawFiles
        .whereType<Map<String, dynamic>>()
        .map((e) => SiteInfoFileModel.fromJson(e))
        .toList();

    return SiteContractItemModel(
      pk: json['pk'] ?? json['id'] ?? 0,
      project: json['project'] ?? 0,
      ownerId: json['owner'] is int ? json['owner'] : (json['owner_desc'] is Map ? json['owner_desc']['pk'] ?? 0 : 0),
      ownerName: parsedOwnerName,
      contractDate: json['contract_date']?.toString() ?? '',
      totalPrice: (json['total_price'] ?? 0) as int,
      contractArea: double.tryParse(json['contract_area']?.toString() ?? '') ?? 0.0,
      downPay1: json['down_pay1'] as int?,
      downPay1Date: json['down_pay1_date']?.toString(),
      downPay1IsPaid: json['down_pay1_is_paid'] == true,
      downPay2: json['down_pay2'] as int?,
      downPay2Date: json['down_pay2_date']?.toString(),
      downPay2IsPaid: json['down_pay2_is_paid'] == true,
      interPay1: json['inter_pay1'] as int?,
      interPay1Date: json['inter_pay1_date']?.toString(),
      interPay1IsPaid: json['inter_pay1_is_paid'] == true,
      interPay2: json['inter_pay2'] as int?,
      interPay2Date: json['inter_pay2_date']?.toString(),
      interPay2IsPaid: json['inter_pay2_is_paid'] == true,
      remainPay: json['remain_pay'] as int?,
      remainPayDate: json['remain_pay_date']?.toString(),
      remainPayIsPaid: json['remain_pay_is_paid'] == true,
      ownershipCompletion: json['ownership_completion'] == true,
      accBank: json['acc_bank']?.toString() ?? '',
      accNumber: json['acc_number']?.toString() ?? '',
      accOwner: json['acc_owner']?.toString() ?? '',
      siteContFiles: filesList,
      note: json['note']?.toString() ?? '',
    );
  }

  /// 평수 환산
  double get contractPyung => contractArea / 3.305785;

  /// 평당 매입 단가
  int get pricePerPyung {
    if (contractPyung <= 0) return 0;
    return (totalPrice / contractPyung).round();
  }

  /// 총 기지급액 계산 (지급 완료된 계약금+중도금+잔금 합산)
  int get totalPaidAmount {
    int sum = 0;
    if (downPay1IsPaid && downPay1 != null) sum += downPay1!;
    if (downPay2IsPaid && downPay2 != null) sum += downPay2!;
    if (interPay1IsPaid && interPay1 != null) sum += interPay1!;
    if (interPay2IsPaid && interPay2 != null) sum += interPay2!;
    if (remainPayIsPaid && remainPay != null) sum += remainPay!;
    return sum;
  }

  /// 미지급 잔액
  int get unpaidAmount => totalPrice - totalPaidAmount;

  /// 대금 지급 진행률 (%)
  double get paymentRate {
    if (totalPrice <= 0) return 0.0;
    return (totalPaidAmount / totalPrice) * 100;
  }

  /// 매매계약서 파일 보유 여부
  bool get hasContractFile => siteContFiles.isNotEmpty && siteContFiles.first.file.isNotEmpty;
}
