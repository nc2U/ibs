from datetime import date, datetime

from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import FileSystemStorage
from django.db.models import Sum, Q
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.generic import View
from weasyprint import HTML

from _pdf.utils import (get_contract, get_due_date_per_order)
from _utils.contract_price import get_contract_payment_plan, get_contract_price
from _utils.payment_adjustment import (
    get_unpaid_installments,
    calculate_late_penalty,
    calculate_daily_interest
)
from cash.models import ProjectCashBook
from notice.models import SalesBillIssue
from payment.models import InstallmentPaymentOrder

TODAY = date.today()


class PdfExportBill(View):
    """고지서 리스트"""

    def get(self, request):
        """
        :: PDF 파일 생성 함수
        :parma request:
        :return:
        """
        project = request.GET.get('project')  # 프로젝트 ID
        pub_date = request.GET.get('date')
        pub_date = datetime.strptime(pub_date, '%Y-%m-%d').date() if pub_date else TODAY
        bill_info = SalesBillIssue.objects.get(project=project)
        np = True if request.GET.get('np') else False
        nl = True if request.GET.get('nl') else False

        context = {
            'pub_date': pub_date,
            'bill_info': bill_info
        }  # 전체 데이터 딕셔너리
        payment_orders = InstallmentPaymentOrder.objects.filter(project=project)  # 전체 납부회차 리스트
        now_due_order = bill_info.now_payment_order.pay_code if bill_info.now_payment_order else 2  # 당회 납부 회차

        contractor_list = request.GET.get('seq').split('-')  # 계약 건 ID 리스트

        # 해당 계약건에 대한 데이터 정리 --------------------------------------- start
        context['data_list'] = (self.get_bill_data(cont_id,
                                                   payment_orders,
                                                   now_due_order, pub_date, np, nl) for cont_id in contractor_list)

        # 해당 계약건에 대한 데이터 정리 --------------------------------------- end

        html_string = render_to_string('pdf/bill_control.html', context)
        html = HTML(string=html_string)
        html.write_pdf(target='/tmp/mypdf.pdf')

        filename = request.GET.get('filename', 'payment_bill')
        filename = f'{filename}({len(contractor_list)}건)' if contractor_list else filename

        fs = FileSystemStorage('/tmp')
        with fs.open('mypdf.pdf') as pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
            return response

    def get_bill_data(self, cont_id, payment_orders, now_due_order, pub_date, np, nl):
        """
        :: 계약 건 당 전달 데이터 생성 함수
        :param cont_id: 계약자 아이디
        :param payment_orders: 전체 납부 회차
        :param now_due_order: 금회 납부 회차
        :param pub_date: 발행일
        :param np: no price 가격 미표시 여부
        :param nl: no late 연체 미표시 여부
        :return dict(bill_data: 계약 건당 데이터):
        """
        bill_data = {}  # 현재 계약 정보 딕셔너리

        # 계약 건 객체
        bill_data['contract'] = contract = get_contract(cont_id)

        try:
            unit = contract.key_unit.houseunit
        except ObjectDoesNotExist:
            unit = None

        # 동호수
        bill_data['unit'] = unit

        # 이 계약 건 분양가격
        price, price_build, price_land, price_tax = get_contract_price(contract)

        bill_data['price'] = price if unit else '동호 지정 후 고지'  # 이 건 분양가격
        bill_data['price_build'] = price_build if unit else '-'  # 이 건 건물가
        bill_data['price_land'] = price_land if unit else '-'  # 이 건 대지가
        bill_data['price_tax'] = price_tax if unit else '-'  # 이 건 부가세

        # get_contract_payment_plan을 사용해서 정확한 회차별 금액 계산
        payment_plan = get_contract_payment_plan(contract)

        # 납부목록, 완납금액 구하기 ------------------------------------------
        paid_list, paid_sum_total = self.get_paid(contract)
        # --------------------------------------------------------------

        # 해당 계약 건의 회차별 관련 정보 (payment_plan을 직접 사용)
        orders_info = self.get_orders_info(payment_orders, payment_plan, paid_sum_total)

        # 완납 회차
        paid_code = self.get_paid_code(orders_info, paid_sum_total)

        # ■ 계약 내용 -----------------------------------------------------
        bill_data['cont_content'] = self.get_cont_content(contract, unit)

        # 연체료 계산 (payment_adjustment.py 사용 - 항상 계산, 템플릿에서 표시 제어)
        late_fee_data = self.calculate_late_fees_standardized(
            contract, payment_orders, now_due_order, pub_date
        )

        # ■ 납부대금 안내 ----------------------------------------------
        bill_data['this_pay_info'] = self.get_this_pay_info(contract,
                                                            orders_info,
                                                            payment_orders,
                                                            now_due_order,
                                                            paid_code,
                                                            late_fee_data)

        # 납부대금 합계
        bill_data['this_pay_sum'] = {
            'amount_sum': sum([pi["amount"] for pi in bill_data['this_pay_info']]),
            'unpaid_sum': sum([pi["unpaid"] for pi in bill_data['this_pay_info']]),
            'penalty_sum': sum([pi["penalty"] for pi in bill_data['this_pay_info']]),
            'amount_total': sum([pi["sum_amount"] for pi in bill_data['this_pay_info']]),
        }

        # ■ 납부방법 안내 ------------------------------------------------
        pm_cost_sum = sum([pm['pm_cost_sum'] for pm in orders_info])
        bill_data['pay_method'] = (bill_data['this_pay_sum']['amount_total'], pm_cost_sum)

        # ■ 납부약정 및 납입내역 -------------------------------------------
        # 기 도래한 약정 회차 내역
        bill_data['due_orders'] = self.get_due_orders(contract, orders_info,
                                                      payment_orders, now_due_order,
                                                      paid_code, pub_date, late_fee_data)

        # 미 도래한 약정 회차 내역
        bill_data['remain_orders'] = self.get_remain_orders(contract, orders_info,
                                                            payment_orders, now_due_order)

        bill_data['paid_sum_total'] = paid_sum_total  # 기 납부 총액

        # 연체료 정보를 bill_data에 추가
        # 실제 청구 대상 회차의 연체료만 사용 (this_pay_info에 포함된 회차만)
        bill_data['late_fee_sum'] = bill_data['this_pay_sum']['penalty_sum']
        bill_data['late_fee_details'] = late_fee_data

        # 표시 정보 제한 여부
        bill_data['no_price'] = np
        bill_data['no_late'] = nl

        # 공백 개수 구하기
        unpaid_count = len(bill_data['this_pay_info'])
        rem_count = len(bill_data['remain_orders'])

        bill_data['blank_line'] = self.get_blank_line(unpaid_count,
                                                      pm_cost_sum,
                                                      payment_orders.count())

        # --------------------------------------------------------------
        return bill_data

    @staticmethod
    def get_paid(contract):
        """
        :: ■ 기 납부금액 구하기
        :param contract: 계약정보
        :param pub_date: 발행일
        :return list(paid_list: 납부 건 리스트), int(paid_sum_total: 납부 총액):
        """
        paid_list = ProjectCashBook.objects.filter(
            income__isnull=False,
            project_account_d3__is_payment=True,  # 분(부)담금 or 분양수입금
            contract=contract,
        ).order_by('deal_date', 'id')  # 해당 계약 건 납부 데이터

        paid_sum_total = paid_list.aggregate(Sum('income'))['income__sum']  # 완납 총금액
        paid_sum_total = paid_sum_total if paid_sum_total else 0
        return paid_list, paid_sum_total

    @staticmethod
    def get_orders_info(payment_orders, payment_plan, paid_sum_total):
        """
        :: 회차별 부가정보 (payment_plan 기반으로 정확한 회차별 금액 계산)
        :param payment_orders: 회차 정보
        :param payment_plan: get_contract_payment_plan에서 반환된 payment plan 데이터
        :param paid_sum_total: 기 납부 총액
        :return list(dict(order_info_list)): 회차별 부가정보 딕셔너리 리스트
        """
        order_info_list = []
        sum_pay_amount = 0  # 회당 납부 약정액 누계
        pm_cost_sum = 0  # PM 용역비 합계

        # payment_plan을 딕셔너리로 변환하여 O(1) 조회 가능하도록 함
        plan_dict = {}
        for plan_item in payment_plan:
            order_pk = plan_item['installment_order'].pk
            plan_dict[order_pk] = plan_item['amount']

        # 지연가산금 관련 계산 시작 회차 ----------------------------------------------
        try:
            calc_start_code = payment_orders.filter(Q(is_prep_discount=True) | Q(is_late_penalty=True))[0].pay_code
        except IndexError:
            calc_start_code = 2

        for order in payment_orders:
            info = {'order': order}

            # payment_plan에서 해당 회차의 정확한 금액을 가져옴
            pay_amount = plan_dict.get(order.pk, 0)  # 회당 납부 약정액 (정확한 값)

            info['pay_amount'] = pay_amount  # 회당 납부 약정액
            sum_pay_amount += pay_amount  # 회당 납부 약정액 누계
            info['sum_pay_amount'] = sum_pay_amount  # 회당 납부 약정액 누계
            unpaid = sum_pay_amount - paid_sum_total  # 약정액 누계 - 총 납부액
            unpaid = unpaid if unpaid > 0 else 0  # 음수(초과 납부 시)는 0 으로 설정
            info['unpaid_amount'] = unpaid if unpaid < pay_amount else pay_amount  # 미납액
            pm_cost_sum += pay_amount if order.pay_sort == '7' else 0  # PM 용역비 합계
            info['pm_cost_sum'] = pm_cost_sum  # PM 용역비 합계

            order_info_list.append(info)

        return order_info_list

    @staticmethod
    def get_cont_content(contract, unit):
        """
        :: ■ 계약 내용
        :param contract: 계약정보
        :param unit: 동호수 정보
        :return dict(contractor: 계약자명, cont_date: 계약일, cont_no: 계약번호, cont_type: 평형):
        """
        contractor = contract.contractor.name
        cont_date = contract.contractor.contract_date
        cont_no = contract.key_unit.houseunit if unit else contract.serial_number
        cont_type = contract.unit_type or contract.key_unit.unit_type

        return {
            'contractor': contractor,
            'cont_date': cont_date,
            'cont_no': cont_no,
            'cont_type': cont_type,
        }

    @staticmethod
    def get_paid_code(orders_info, paid_sum_total):
        """
        :: 완납 회차 구하기
        :param orders_info: 전체 납부 회차
        :param paid_sum_total: 납부 총액
        :return 완납회차 객체:
        """
        try:
            paid_code = [c['order'].pay_code for c in orders_info if paid_sum_total >= c['sum_pay_amount']][-1]
        except IndexError:  # paid_sum_total 이 1회차에 미치지 못하는 경우 == 계약금 부족 시
            paid_code = 0

        return paid_code

    @staticmethod
    def get_this_pay_info(contract,
                          orders_info, payment_orders,
                          now_due_order, paid_code, late_fee_details=None):
        """
        :: ■ 납부대금 안내
        :param contract: 계약 정보
        :param orders_info: 회차별 부가정보
        :param payment_orders: 회차 정보
        :param now_due_order: 당회 납부 회차
        :param paid_code: 완납 회차
        :param late_fee_details: 연체료 상세 정보 (calculate_late_fees_standardized 결과)
        :return list(dict(order: 납부회차, due_date: 납부기한, amount: 약정금액, unpaid: 미납금액, penalty: 연체가산금, sum_amount: 납부금액)):
        """
        payment_list = []
        unpaid_orders = payment_orders.filter(pay_code__gt=paid_code,
                                              pay_code__lte=now_due_order)  # 최종 기납부회차 이후부터 납부지정회차 까지 회차그룹

        # 회차별 연체료 매핑 생성 (late_fee_details가 있는 경우)
        penalty_by_order = {}
        if late_fee_details and late_fee_details.get('unpaid_penalties'):
            for unpaid_penalty in late_fee_details['unpaid_penalties']:
                installment = unpaid_penalty['installment']
                penalty_by_order[installment.pay_code] = unpaid_penalty['penalty_amount']

        for order in unpaid_orders:
            ord_info = list(filter(lambda o: o['order'] == order, orders_info))[0]

            amount = ord_info['pay_amount']
            unpaid = ord_info['unpaid_amount']

            # 회차별 연체료 조회 (미납 회차만 해당)
            penalty = penalty_by_order.get(order.pay_code, 0)

            payment_dict = {
                'order': order,
                'due_date': get_due_date_per_order(contract, order, unpaid_orders),
                'amount': amount,
                'unpaid': unpaid,
                'penalty': penalty,
                'sum_amount': unpaid + penalty
            }
            payment_list.append(payment_dict)

        return payment_list

    def get_due_orders(self, contract, orders_info,
                       payment_orders, now_due_order,
                       paid_code, pub_date, late_fee_details=None):
        """
        :: ■ 납부약정 및 납입내역 - 납입내역
        :param contract: 계약 건
        :param orders_info: 납부 회차별 부가정보
        :param payment_orders: 전체 납부회차
        :param now_due_order: 금회 납부 회차
        :param paid_code: 완납회차
        :param pub_date: 발행일자
        :param late_fee_details: 연체료 상세 정보
        :return list(paid_list: 완납 회차 목록):
        """

        # 회차별 미납 연체료 매핑 생성
        unpaid_penalty_by_order = {}
        if late_fee_details and late_fee_details.get('unpaid_penalties'):
            for unpaid_penalty in late_fee_details['unpaid_penalties']:
                installment = unpaid_penalty['installment']
                unpaid_penalty_by_order[installment.pay_code] = {
                    'unpaid_amt': unpaid_penalty['remaining_amount'],
                    'unpaid_days': unpaid_penalty['late_days'],
                    'unpaid_result': unpaid_penalty['penalty_amount']
                }

        # 해당 계약 건 전체 납부 목록 -> [(income, deal_date), ...]
        paid_list = [(p.income, p.deal_date) for p in self.get_paid(contract)[0]]
        paid_date = paid_list[0][1] if len(paid_list) > 0 else None

        # 전체 리턴 데이터 목록
        paid_amt_list = []
        due_orders = payment_orders.filter(pay_code__lte=now_due_order)  # 금 회차까지 납부 회차

        excess = 0  # 회차별 초과 납부분

        for order in due_orders:
            due_date = get_due_date_per_order(contract, order, due_orders)  # 납부기한
            ord_info = list(filter(lambda o: o['order'] == order, orders_info))[0]  # 금 회차 orders_info
            amount = ord_info['pay_amount']  # 금 회차 납부 약정액

            paid_amt = 0  # 금회 납부금액

            while True:  # 납입회차별 납입금 구하기
                try:
                    paid = paid_list.pop(0)  # (income, deal_date) <- 첫번째 요소(가장 빠른 납부일자)
                    paid_amt += paid[0]  # 납부액 += income (loop 동안 income 을 모두 더함)
                    paid_date = paid[1]  # 납부일 = deal_date(loop 마지막 납부건 납부일)
                    is_over_amt = (excess + paid_amt) >= amount  # (전회 초과 납부분 + 납부액) >= 약정액
                    # 현재 회차 == 금회 직전 회차 (이 경우 루프 마지막까지 순회하기 위해서 루프탈출 조건에서 제외)

                    is_last_ord = order.pay_code + 1 == now_due_order
                    if is_over_amt and not is_last_ord:  # loop 탈출 조건
                        excess += (paid_amt + excess - amount)  # 금회 초과 납부분 += (금회 납부액 + 전회 초과납부분 - 약정액)
                        break
                except IndexError:  # .pop(0) 에러 시 탈출
                    break

            paid_date = paid_date if paid_amt else ''  # 납부 금액이 있을 때만 납부일 저장

            # 회차별 미납 연체료 정보 조회
            penalty_info = unpaid_penalty_by_order.get(order.pay_code, {})

            paid_dict = dict()
            paid_dict['order'] = order.pay_name
            paid_dict['due_date'] = due_date
            paid_dict['amount'] = amount
            paid_dict['paid_date'] = paid_date
            paid_dict['paid_amt'] = paid_amt
            paid_dict['unpaid_amt'] = penalty_info.get('unpaid_amt', 0)
            paid_dict['unpaid_days'] = penalty_info.get('unpaid_days', 0)
            paid_dict['unpaid_result'] = penalty_info.get('unpaid_result', 0)
            paid_dict['note'] = ''
            paid_amt_list.append(paid_dict)

        return paid_amt_list

    @staticmethod
    def calculate_late_fees_standardized(contract, payment_orders, now_due_order, pub_date):
        """
        :: 표준화된 연체료 계산 (payment_adjustment.py 사용)

        Args:
            contract: 계약 인스턴스
            payment_orders: 전체 납부 회차
            now_due_order: 금회 납부 회차 (고지서 기준)
            pub_date: 발행일자

        Returns:
            dict: {
                'total_late_fee': int,           # 총 연체료
                'paid_penalties': list,          # 완납된 납부건의 연체료 목록
                'unpaid_penalties': list,        # 미납 회차 연체료 목록
                'paid_penalty_count': int,       # 납부 연체 건수
                'unpaid_penalty_count': int      # 미납 연체 건수
            }
        """
        from decimal import Decimal

        total_late_fee = 0
        paid_penalties = []
        unpaid_penalties = []

        # 1. 완납된 납부건의 연체료 계산 (과거 지연 납부)
        paid_records = ProjectCashBook.objects.payment_records().filter(
            contract=contract,
            deal_date__lte=pub_date
        ).order_by('deal_date', 'id')

        for payment in paid_records:
            if payment.installment_order and payment.installment_order.pay_code <= now_due_order:
                penalty_info = calculate_late_penalty(payment)
                if penalty_info and penalty_info['penalty_amount'] > 0:
                    paid_penalties.append(penalty_info)
                    total_late_fee += penalty_info['penalty_amount']

        # 2. 미납 회차의 연체료 계산 (현재 기준)
        unpaid_installments = get_unpaid_installments(contract, pub_date)

        for unpaid_info in unpaid_installments:
            installment = unpaid_info['installment_order']

            # now_due_order까지만 계산 (고지서 범위)
            if installment.pay_code <= now_due_order:
                if installment.is_late_penalty and unpaid_info['is_overdue']:
                    penalty_rate = Decimal(str(installment.late_penalty_ratio)) if installment.late_penalty_ratio else Decimal('0')

                    if penalty_rate > 0:
                        penalty_amount = calculate_daily_interest(
                            unpaid_info['remaining_amount'],
                            penalty_rate,
                            unpaid_info['late_days']
                        )

                        unpaid_penalties.append({
                            'installment': installment,
                            'order_name': installment.pay_name,
                            'remaining_amount': unpaid_info['remaining_amount'],
                            'late_days': unpaid_info['late_days'],
                            'penalty_rate': penalty_rate,
                            'penalty_amount': penalty_amount
                        })
                        total_late_fee += penalty_amount

        return {
            'total_late_fee': total_late_fee,
            'paid_penalties': paid_penalties,
            'unpaid_penalties': unpaid_penalties,
            'paid_penalty_count': len(paid_penalties),
            'unpaid_penalty_count': len(unpaid_penalties)
        }

    @staticmethod
    def get_blank_line(unpaid_count, pm, total_orders_count):
        """
        :: 공백 라인 개수 구하기
        :param unpaid_count: 미납내역 개수
        :param pm: pm 용역비 적용여부
        :param total_orders_count: 전체 납부회차 개수
        :return str(. * 공백라인 수):
        """
        num = unpaid_count + 1 if pm else unpaid_count
        blank_line = (14 - (num + total_orders_count))
        return '.' * blank_line

    @staticmethod
    def get_remain_orders(contract, orders_info, payment_orders, now_due_order):
        """
        :: ■ 납부약정 및 납입내역 - 잔여회차
        :param contract: 계약 건
        :param orders_info: 납부 회차별 부가정보
        :param payment_orders: 전체 납부 회차
        :param now_due_order: 금회 납부 회차
        :return list(dict(remain_amt_list)): 잔여 회차(dict) 목록:
        """
        remain_amt_list = []
        remain_orders = payment_orders.filter(pay_code__gt=now_due_order)

        for order in remain_orders:
            ord_info = list(filter(lambda o: o['order'] == order, orders_info))[0]
            amount = ord_info['pay_amount']

            paid_dict = {
                'order': order.pay_name,
                'due_date': get_due_date_per_order(contract, order, remain_orders),
                'amount': amount,
                'paid_date': '',
                'paid_amt': 0,
                # 'delayed_amt': 0,
                'penalty_days': 0,
                'panalty_amt': 0,
            }
            remain_amt_list.append(paid_dict)

        return remain_amt_list