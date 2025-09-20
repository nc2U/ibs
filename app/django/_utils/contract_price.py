from decimal import Decimal
from payment.models import SalesPriceByGT, DownPayment, InstallmentPaymentOrder, PaymentPerInstallment
from project.models import ProjectIncBudget


def get_floor_type(contract):
    """
    Get UnitFloorType instance related to Contract instance.

    Args:
        contract: Contract instance

    Returns:
        UnitFloorType instance or None

    Notes:
        Relationship path: Contract -> KeyUnit -> HouseUnit -> UnitFloorType

    For optimization, use prefetch when calling:
    Contract.objects.select_related('key_unit__houseunit__floor_type')
    """
    if not contract or not contract.key_unit:
        return None
    try:
        house_unit = contract.key_unit.houseunit
        return house_unit.floor_type
    except AttributeError:
        return None


def get_contract_price(contract):
    """
    Get contract price details with 5-step fallback logic.

    Args:
        contract: Contract instance

    Returns:
        tuple: (price, price_build, price_land, price_tax) or (0, 0, 0, 0) if no price found

    Priority order:
        1. ContractPrice (all fields if exists)
        2. SalesPriceByGT (all fields matched by order_group, unit_type, unit_floor_type)
        3. ProjectIncBudget.average_price (only price, others 0)
        4. UnitType.average_price (only price, others 0)
        5. (0, 0, 0, 0)

    For optimization, use prefetch when calling:
    Contract.objects.select_related(
        'contractprice', 'project', 'order_group', 'unit_type',
        'key_unit__houseunit__floor_type'
    ).prefetch_related('project__projectincbudget_set')
    """
    if not contract:
        return 0, 0, 0, 0

    # Step 1: Check ContractPrice (all fields)
    try:
        cp = contract.contractprice
        return (
            cp.price or 0,
            cp.price_build or 0,
            cp.price_land or 0,
            cp.price_tax or 0
        )
    except AttributeError:
        pass

    # Step 2: Check SalesPriceByGT (all fields)
    try:
        # Get unit_floor_type
        unit_floor_type = get_floor_type(contract)

        # Query SalesPriceByGT with different conditions
        sales_price_query = SalesPriceByGT.objects.filter(
            project=contract.project,
            order_group=contract.order_group,
            unit_type=contract.unit_type
        )

        if unit_floor_type:
            # Try with unit_floor_type first
            sales_price = sales_price_query.filter(unit_floor_type=unit_floor_type).first()
            if sales_price:
                return (
                    sales_price.price or 0,
                    sales_price.price_build or 0,
                    sales_price.price_land or 0,
                    sales_price.price_tax or 0
                )

        # Try without unit_floor_type
        sales_price = sales_price_query.first()
        if sales_price:
            return (
                sales_price.price or 0,
                sales_price.price_build or 0,
                sales_price.price_land or 0,
                sales_price.price_tax or 0
            )

    except AttributeError:
        # contract.project, contract.order_group, or contract.unit_type is None
        pass

    # Step 3: Check ProjectIncBudget.average_price (only price, others 0)
    try:
        project_budget = ProjectIncBudget.objects.filter(
            project=contract.project,
            unit_type=contract.unit_type
        ).first()

        if project_budget and project_budget.average_price:
            return project_budget.average_price, 0, 0, 0

    except AttributeError:
        # contract.project or contract.unit_type is None
        pass

    # Step 4: Check UnitType.average_price (only price, others 0)
    try:
        if contract.unit_type and contract.unit_type.average_price:
            return contract.unit_type.average_price, 0, 0, 0
    except AttributeError:
        pass

    # Step 5: Return default values
    return 0, 0, 0, 0


def get_down_payment(contract, installment_order):
    """
    Get down payment amount for specific contract and installment order.

    Args:
        contract: Contract instance
        installment_order: InstallmentPaymentOrder instance with pay_sort='1' (계약금)

    Returns:
        int: Down payment amount or None if calculation failed

    Priority order:
        1. PaymentPerInstallment (if exists for this sales_price and installment_order)
        2. DownPayment (matched by order_group and unit_type)
        3. InstallmentPaymentOrder.pay_ratio (default 10%)

    For optimization, use prefetch when calling:
    Contract.objects.select_related('order_group', 'unit_type')
    """
    if not contract or not installment_order:
        return None

    if installment_order.pay_sort != '1':  # Only for 계약금
        return None

    # Step 1: Check PaymentPerInstallment (new structure using SalesPriceByGT)
    try:
        # Get unit_floor_type for SalesPriceByGT lookup
        unit_floor_type = get_floor_type(contract)

        # Find matching SalesPriceByGT
        sales_price_query = SalesPriceByGT.objects.filter(
            project=contract.project,
            order_group=contract.order_group,
            unit_type=contract.unit_type
        )

        if unit_floor_type:
            sales_price = sales_price_query.filter(unit_floor_type=unit_floor_type).first()
        else:
            sales_price = sales_price_query.first()

        if sales_price:
            payment_per_installment = PaymentPerInstallment.objects.filter(
                sales_price=sales_price,
                pay_order=installment_order
            ).first()

            if payment_per_installment:
                return payment_per_installment.amount
    except (AttributeError, TypeError, ValueError):
        # AttributeError: contract.project/order_group/unit_type is None
        # TypeError: Invalid filter parameter types
        # ValueError: Invalid data conversion
        pass

    # Step 2: Check DownPayment
    try:
        down_payment = DownPayment.objects.filter(
            project=contract.project,
            order_group=contract.order_group,
            unit_type=contract.unit_type
        ).first()

        if down_payment and down_payment.payment_amount:
            return down_payment.payment_amount
    except (AttributeError, TypeError):
        # AttributeError: contract.project/order_group/unit_type is None
        # TypeError: Invalid filter parameter types
        pass

    # Step 3: Use InstallmentPaymentOrder.pay_ratio (default 10%)
    try:
        # Get contract price first
        contract_price_data = get_contract_price(contract)
        contract_price = contract_price_data[0]  # Get price from tuple
        if not contract_price:
            return None

        # Get pay_ratio from InstallmentPaymentOrder
        pay_ratio = installment_order.pay_ratio
        if pay_ratio is None:
            pay_ratio = Decimal('10.0')  # Default 10%

        # Calculate amount: contract_price * (pay_ratio / 100)
        down_payment_amount = int(contract_price * (pay_ratio / 100))
        return down_payment_amount

    except (TypeError, ValueError, OverflowError):
        # TypeError: Invalid arithmetic operations (None * number)
        # ValueError: Invalid conversion to int
        # OverflowError: Result too large for int
        pass

    return None


def get_installment_payment_amount(contract, installment_order):
    """
    Get payment amount for specific contract and installment order with 5-step priority logic.

    Args:
        contract: Contract instance
        installment_order: InstallmentPaymentOrder instance

    Returns:
        int: Payment amount or 0 if no amount found

    Priority logic:
        1. InstallmentPaymentOrder.pay_amt (fixed amount for all types) - highest priority
        2. For 중도금 (pay_sort='2'): Always use pay_ratio (default 10%)
        3. For 잔금 (pay_sort='3'): Total price minus sum of other installments
        4. For 계약금 (pay_sort='1'): Use get_down_payment function
        5. For other types: pay_amt/pay_ratio -> PaymentPerInstallment -> 0
    """
    if not contract or not installment_order:
        return 0

    # Step 1: Check InstallmentPaymentOrder.pay_amt (highest priority for all types)
    if installment_order.pay_amt:
        return installment_order.pay_amt

    # Get contract price
    contract_price_data = get_contract_price(contract)
    contract_price = contract_price_data[0]  # Get price from tuple
    if not contract_price:
        return 0

    pay_sort = installment_order.pay_sort

    # Step 2: Handle 중도금 (always use pay_ratio)
    if pay_sort == '2':  # 중도금
        pay_ratio = installment_order.pay_ratio
        if pay_ratio is None:
            pay_ratio = Decimal('10.0')  # Default 10%
        return int(contract_price * (pay_ratio / 100))

    # Step 3: Handle 잔금 (total minus other installments)
    elif pay_sort == '3':  # 잔금
        return calculate_remain_payment(contract, installment_order)

    # Step 4: Handle 계약금 (use get_down_payment function)
    elif pay_sort == '1':  # 계약금
        down_payment = get_down_payment(contract, installment_order)
        return down_payment if down_payment is not None else 0

    # Step 5: Handle other types (기타 부담금, 제세 공과금, 금융 비용, 업무 대행비)
    else:
        # Try pay_ratio first
        if installment_order.pay_ratio:
            return int(contract_price * (installment_order.pay_ratio / 100))

        # Try PaymentPerInstallment (new structure using SalesPriceByGT)
        try:
            # Get unit_floor_type for SalesPriceByGT lookup
            unit_floor_type = get_floor_type(contract)

            # Find matching SalesPriceByGT
            sales_price_query = SalesPriceByGT.objects.filter(
                project=contract.project,
                order_group=contract.order_group,
                unit_type=contract.unit_type
            )

            if unit_floor_type:
                sales_price = sales_price_query.filter(unit_floor_type=unit_floor_type).first()
            else:
                sales_price = sales_price_query.first()

            if sales_price:
                payment_per_installment = PaymentPerInstallment.objects.filter(
                    sales_price=sales_price,
                    pay_order=installment_order
                ).first()

                if payment_per_installment:
                    return payment_per_installment.amount
        except (AttributeError, TypeError, ValueError):
            # AttributeError: contract.project/order_group/unit_type is None
            # TypeError: Invalid filter parameter types
            # ValueError: Invalid data conversion
            pass

        # Default to 0
        return 0


def calculate_remain_payment(contract, remain_installment_order):
    """
    Calculate remain payment by subtracting all other installment amounts from total price.

    Args:
        contract: Contract instance
        remain_installment_order: InstallmentPaymentOrder instance with pay_sort='3' (잔금)

    Returns:
        int: Remain payment amount
    """
    if not contract or not remain_installment_order:
        return 0

    # Get total contract price
    contract_price_data = get_contract_price(contract)
    contract_price = contract_price_data[0]  # Get price from tuple
    if not contract_price:
        return 0

    # Get all installment orders for this contract's project excluding remain payment
    try:
        other_installments = InstallmentPaymentOrder.objects.filter(
            project=contract.project,
            type_sort=contract.unit_type.sort
        ).exclude(
            pay_sort='3'  # Exclude 잔금
        ).exclude(
            id=remain_installment_order.id  # Exclude current remain installment
        )

        total_other_payments = 0

        for installment in other_installments:
            # Get payment amount for each installment
            amount = get_installment_payment_amount(contract, installment)
            total_other_payments += amount

        # Calculate remain payment
        remain_payment = contract_price - total_other_payments

        # Ensure non-negative
        return max(0, remain_payment)

    except (AttributeError, TypeError, ValueError):
        # AttributeError: contract.project/unit_type is None
        # TypeError: Invalid filter operations
        # ValueError: Invalid arithmetic operations
        return 0


def get_contract_payment_plan(contract):
    """
    Get complete payment plan for a contract with all installment amounts.

    Args:
        contract: Contract instance

    Returns:
        list: List of dictionaries containing installment order and calculated amount

    Example return:
        [
            {
                'installment_order': InstallmentPaymentOrder instance,
                'amount': 50000000,
                'source': 'calculated'  # or 'manual_override'
            },
            ...
        ]
    """
    if not contract:
        return []

    try:
        # Get all installment orders for this contract
        installments = InstallmentPaymentOrder.objects.filter(
            project=contract.project,
            type_sort=contract.unit_type.sort
        ).order_by('pay_code', 'pay_time')

        payment_plan = []

        for installment in installments:
            # Check if there's a manual override (new structure using SalesPriceByGT)
            try:
                # Get unit_floor_type for SalesPriceByGT lookup
                unit_floor_type = get_floor_type(contract)

                # Find matching SalesPriceByGT
                sales_price_query = SalesPriceByGT.objects.filter(
                    project=contract.project,
                    order_group=contract.order_group,
                    unit_type=contract.unit_type
                )

                if unit_floor_type:
                    sales_price = sales_price_query.filter(unit_floor_type=unit_floor_type).first()
                else:
                    sales_price = sales_price_query.first()

                if sales_price:
                    manual_payment = PaymentPerInstallment.objects.filter(
                        sales_price=sales_price,
                        pay_order=installment
                    ).first()

                    if manual_payment:
                        payment_plan.append({
                            'installment_order': installment,
                            'amount': manual_payment.amount,
                            'source': 'payment_per_installment'
                        })
                        continue
            except (AttributeError, TypeError, ValueError):
                # AttributeError: contract.project/order_group/unit_type is None
                # TypeError: Invalid filter parameter types
                # ValueError: Invalid data conversion
                pass

            # Calculate amount using priority logic
            amount = get_installment_payment_amount(contract, installment)

            payment_plan.append({
                'installment_order': installment,
                'amount': amount,
                'source': 'calculated'
            })

        return payment_plan

    except (AttributeError, TypeError):
        # AttributeError: contract.project/unit_type is None
        # TypeError: Invalid filter operations
        return []
