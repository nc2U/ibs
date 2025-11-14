from datetime import date, datetime

from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import FileSystemStorage
from django.db.models import Sum, Q, Max
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.generic import View
from weasyprint import HTML

from _pdf.utils import get_contract, get_due_date_per_order
from _utils.contract_price import get_contract_payment_plan, get_contract_price
from _utils.payment_adjustment import aggregate_installment_adjustments
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
        late_fee_data = self.calculate_late_fees_standardized(contract, payment_orders, now_due_order, pub_date)

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
            'discount_sum': sum([pi.get("discount", 0) for pi in bill_data['this_pay_info']]),
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
        # late_fee_data에는 모든 도래한 회차(기납부 + 미납)의 연체료/할인이 포함됨
        # this_pay_sum은 미납 회차만 포함하므로, 전체 연체료는 late_fee_data에서 가져와야 함
        bill_data['late_fee_sum'] = late_fee_data.get('total_late_fee', 0)
        bill_data['discount_sum'] = late_fee_data.get('total_discount', 0)
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
        :: ■ 회차별 납부 내역 집계
        :param contract: 계약정보
        :return dict(payment_by_order: 회차별 납부 정보), int(paid_sum_total: 납부 총액):

        회차별 납부 정보 구조:
        {
            order_id: {'paid_amt': 총납부금액, 'paid_date': 최종납부일},
            ...
        }
        """

        # 회차별 납부 내역 집계 (payment_records 사용)
        payment_summary = ProjectCashBook.objects.payment_records().filter(
            contract=contract,
            income__isnull=False,
            installment_order__isnull=False
        ).values('installment_order').annotate(
            total_paid=Sum('income'),
            last_payment_date=Max('deal_date')
        )

        # 회차별 딕셔너리 생성 {order_id: {'paid_amt': amount, 'paid_date': date}}
        payment_by_order = {
            p['installment_order']: {
                'paid_amt': p['total_paid'] or 0,
                'paid_date': p['last_payment_date']
            }
            for p in payment_summary
        }

        # 전체 납부 총액
        paid_sum_total = sum(p['paid_amt'] for p in payment_by_order.values())

        return payment_by_order, paid_sum_total

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
        cont_date = contract.sup_cont_date or contract.contractor.contract_date
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
    def get_this_pay_info(contract, orders_info, payment_orders,
                          now_due_order, paid_code, late_fee_details=None):
        """
        :: ■ 납부대금 안내
        :param contract: 계약 정보
        :param orders_info: 회차별 부가정보
        :param payment_orders: 회차 정보
        :param now_due_order: 당회 납부 회차
        :param paid_code: 완납 회차
        :param late_fee_details: 연체료 및 할인 상세 정보 (calculate_late_fees_standardized 결과)
        :return list(dict(
            order: 납부회차,
            due_date: 납부기한,
            amount: 약정금액,
            unpaid: 미납금액,
            penalty: 연체가산금,
            discount: 선납할인,
            sum_amount: 납부금액)):
        """
        payment_list = []

        # 회차별 연체료와 할인 매핑 생성
        adjustment_by_order = {}
        if late_fee_details and late_fee_details.get('installment_details'):
            for detail in late_fee_details['installment_details']:
                installment = detail['installment']
                adjustment_by_order[installment.pay_code] = {
                    'penalty': detail['penalty_amount'],
                    'discount': detail['discount_amount']
                }

        # 총 할인액 계산
        total_discount = late_fee_details.get('total_discount', 0) if late_fee_details else 0

        # 선납 할인이 있으면 첫 행에 추가 (할인은 납부금액에서 차감되므로 음수)
        if total_discount > 0:
            payment_list.append({
                'order': '선납 할인',
                'due_date': '',
                'amount': 0,
                'unpaid': 0,
                'penalty': 0,
                'discount': total_discount,
                'sum_amount': -total_discount,  # 할인은 차감
                'is_discount': True  # 선납 할인 표시용
            })

        unpaid_orders = payment_orders.filter(pay_code__gt=paid_code,
                                              pay_code__lte=now_due_order)  # 최종 기납부회차 이후부터 납부지정회차 까지 회차그룹

        for order in unpaid_orders:
            ord_info = list(filter(lambda o: o['order'] == order, orders_info))[0]

            amount = ord_info['pay_amount']
            unpaid = ord_info['unpaid_amount']

            # 회차별 연체료 및 할인 조회
            adjustment = adjustment_by_order.get(order.pay_code, {})
            penalty = adjustment.get('penalty', 0)
            discount = adjustment.get('discount', 0)

            payment_dict = {
                'order': order,
                'due_date': get_due_date_per_order(contract, order, unpaid_orders),
                'amount': amount,
                'unpaid': unpaid,
                'penalty': penalty,
                'discount': discount,
                'sum_amount': unpaid + penalty - discount  # 미납금 + 연체료 - 할인
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
        :param late_fee_details: 연체료 및 할인 상세 정보 (calculate_late_fees_standardized 결과)
        :return list(paid_list: 완납 회차 목록):
        """

        # 회차별 조정금액(할인/연체) 매핑 생성
        adjustment_by_order = {}
        if late_fee_details and late_fee_details.get('installment_details'):
            for detail in late_fee_details['installment_details']:
                installment = detail['installment']
                adjustment_by_order[installment.pay_code] = {
                    'late_amount': detail.get('late_amount', 0),  # 지연 납부액
                    'late_days': detail.get('late_days', 0),  # 지연일수 (연체)
                    'prepay_days': detail.get('prepay_days', 0),  # 선납일수
                    'penalty_amount': detail.get('penalty_amount', 0),  # 연체료
                    'discount_amount': detail.get('discount_amount', 0)  # 선납할인
                }

        # 회차별 납부 내역 조회
        payment_by_order, _ = self.get_paid(contract)

        # 전체 리턴 데이터 목록
        paid_amt_list = []
        due_orders = payment_orders.filter(pay_code__lte=now_due_order)  # 금 회차까지 납부 회차

        for order in due_orders:
            due_date = get_due_date_per_order(contract, order, due_orders)  # 납부기한
            ord_info = list(filter(lambda o: o['order'] == order, orders_info))[0]  # 금 회차 orders_info
            amount = ord_info['pay_amount']  # 금 회차 납부 약정액

            # 회차별 납부 정보 조회 (없으면 0, '')
            payment_info = payment_by_order.get(order.id, {'paid_amt': 0, 'paid_date': ''})

            # 회차별 조정금액 정보 조회
            adjustment = adjustment_by_order.get(order.pay_code, {})

            paid_dict = dict()
            paid_dict['order'] = order.pay_name
            paid_dict['due_date'] = due_date
            paid_dict['amount'] = amount
            paid_dict['paid_date'] = payment_info['paid_date']
            paid_dict['paid_amt'] = payment_info['paid_amt']

            # 조정금액 정보 (할인/연체)
            paid_dict['unpaid_amt'] = adjustment.get('late_amount', 0)  # 지연 납부액 (미납액)
            penalty = adjustment.get('penalty_amount', 0)  # 연체료 (가산금)
            discount = adjustment.get('discount_amount', 0)  # 선납할인
            late_days = adjustment.get('late_days', 0)  # 연체일수
            prepay_days = adjustment.get('prepay_days', 0)  # 선납일수

            # 일수: 선납은 음수(-), 연체는 양수(+)
            if discount > 0 and penalty == 0:
                # 선납할인이 있고 연체료가 없는 경우 - 선납일수를 음수로 표시
                paid_dict['unpaid_days'] = -prepay_days if prepay_days > 0 else 0
            elif penalty > 0:
                # 연체인 경우 - 연체일수를 양수로 표시
                paid_dict['unpaid_days'] = late_days
            else:
                # 할인도 연체도 없는 경우
                paid_dict['unpaid_days'] = 0

            paid_dict['penalty'] = penalty
            paid_dict['discount'] = discount

            # 최종 조정 결과 계산: 연체료 - 할인 (양수면 가산, 음수면 할인)
            paid_dict['unpaid_result'] = penalty - discount

            paid_dict['note'] = ''
            paid_amt_list.append(paid_dict)

        return paid_amt_list

    @staticmethod
    def calculate_late_fees_standardized(contract, payment_orders, now_due_order, pub_date):
        """
        :: 표준화된 연체료 및 할인 계산 (waterfall 기반)

        PdfExportPayments와 동일한 계산 로직 사용:
        - aggregate_installment_adjustments(): waterfall 기반 개별 납부 연체료 집계
        - 분할 납부 시에도 PdfExportPayments와 동일한 금액 보장

        Args:
            contract: 계약 인스턴스
            payment_orders: 전체 납부 회차
            now_due_order: 금회 납부 회차 (고지서 기준)
            pub_date: 발행일자

        Returns:
            dict: {
                'total_late_fee': int,           # 총 연체료
                'total_discount': int,           # 총 선납 할인
                'installment_details': list,     # 회차별 상세 정보
                'penalty_count': int,            # 연체료 발생 건수
                'discount_count': int            # 할인 발생 건수
            }
        """

        # aggregate_installment_adjustments가 모든 계산을 처리
        # waterfall 로직을 사용하여 개별 납부건의 연체료를 회차별로 집계
        return aggregate_installment_adjustments(
            contract,
            payment_orders,
            now_due_order,
            pub_date
        )

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
                'penalty_amt': 0,
            }
            remain_amt_list.append(paid_dict)

        return remain_amt_list
