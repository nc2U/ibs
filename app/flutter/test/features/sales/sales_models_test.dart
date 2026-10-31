import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_ibs/features/sales/data/models/sales_models.dart';

void main() {
  group('Sales Models Unit Tests', () {
    test('CommissionPolicyModel.fromJson parses is_active and calculates fees', () {
      final inactivePolicy = CommissionPolicyModel.fromJson({
        'id': 10,
        'project': 1,
        'name': '비활성 정책',
        'agent_fee': 2000000,
        'leader_fee': 1000000,
        'director_fee': 500000,
        'agency_fee': 1500000,
        'pay_condition': '1',
        'start_date': '2026-01-01',
        'is_active': false,
      });

      expect(inactivePolicy.isActive, isFalse);
      expect(inactivePolicy.totalFee, 5000000);
      expect(inactivePolicy.vatAmount, 500000);
      expect(inactivePolicy.totalBillingAmount, 5500000);

      final defaultActivePolicy = CommissionPolicyModel.fromJson({
        'id': 11,
        'project': 1,
        'name': '기본 활성 정책',
        'start_date': '2026-01-01',
      });
      expect(defaultActivePolicy.isActive, isTrue);
    });

    test('SalesAgencyModel.fromJson defaults isDirectManaged to true', () {
      final defaultAgency = SalesAgencyModel.fromJson({
        'id': 1,
        'project': 1,
        'name': '본사 직영 사업부',
      });
      expect(defaultAgency.isDirectManaged, isTrue);

      final outsourcedAgency = SalesAgencyModel.fromJson({
        'id': 2,
        'project': 1,
        'name': '외주 대행사',
        'is_direct_managed': false,
      });
      expect(outsourcedAgency.isDirectManaged, isFalse);
    });

    test('AgencyPayoutModel.fromJson sets agency roleType defaults on contractDetails', () {
      final agencyPayout = AgencyPayoutModel.fromJson({
        'id': 5,
        'period': 2,
        'agency': 3,
        'agency_name': '외주대행사A',
        'is_direct_managed': false,
        'contract_count': 1,
        'agency_fee_sum': 3000000,
        'vat_amount': 300000,
        'total_amount': 3300000,
        'pay_status': '2',
        'contract_details': [
          {
            'id': 100,
            'payout': 5,
            'contract': 55,
            'contract_serial': '101-101',
            'contractor_name': '홍길동',
            'unit_fee': 3000000,
          },
        ],
      });

      expect(agencyPayout.contractDetails, hasLength(1));
      expect(agencyPayout.contractDetails.first.roleType, 'agency');
      expect(agencyPayout.contractDetails.first.roleTypeDisplay, '대행사 수수료');
      expect(agencyPayout.contractDetails.first.unitFee, 3000000);
    });

    test('SettlementPeriodModel.hasCalculatedData supports outsourced-agency-only periods', () {
      final emptyDraft = SettlementPeriodModel.fromJson({
        'id': 1,
        'project': 1,
        'title': '빈 회차',
        'start_date': '2026-10-01',
        'end_date': '2026-10-15',
        'status': '1',
        'total_contracts': 0,
        'payout_count': 0,
        'agency_payout_count': 0,
      });
      expect(emptyDraft.hasCalculatedData, isFalse);

      final agencyOnlyPeriod = SettlementPeriodModel.fromJson({
        'id': 2,
        'project': 1,
        'title': '외주 전용 회차',
        'start_date': '2026-10-01',
        'end_date': '2026-10-15',
        'status': '1',
        'total_contracts': 3,
        'payout_count': 0,
        'total_gross_amount': 0,
        'agency_payout_count': 1,
        'agency_fee_total': 9000000,
      });
      expect(agencyOnlyPeriod.isDraft, isTrue);
      expect(agencyOnlyPeriod.hasCalculatedData, isTrue);
      expect(agencyOnlyPeriod.billingSupplyPrice, 9000000);
      expect(agencyOnlyPeriod.billingVat, 900000);
      expect(agencyOnlyPeriod.billingTotalAmount, 9900000);
    });

    test('SalesPersonModel.fromJson parses 3-tier status codes (1: 재직, 2: 휴직, 3: 해촉)', () {
      final leavePerson = SalesPersonModel.fromJson({
        'id': 7,
        'team': 2,
        'name': '김휴직',
        'duty': '1',
        'status': '2',
        'status_display': '휴직',
      });
      expect(leavePerson.status, '2');
      expect(leavePerson.statusDisplay, '휴직');

      final resignedPerson = SalesPersonModel.fromJson({
        'id': 8,
        'team': 2,
        'name': '이해촉',
        'duty': '2',
        'status': '3',
        'status_display': '해촉 (퇴사)',
      });
      expect(resignedPerson.status, '3');
      expect(resignedPerson.statusDisplay, '해촉 (퇴사)');
    });
  });
}
