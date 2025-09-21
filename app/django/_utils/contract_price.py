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


def get_sales_price_by_gt(contract, houseunit=None):
    """
    Get SalesPriceByGT instance for specific contract and houseunit.

    Args:
        contract: Contract instance
        houseunit: HouseUnit instance (if None, uses contract.key_unit.houseunit)

    Returns:
        SalesPriceByGT instance or None

    Notes:
        For optimization, use prefetch when calling:
        Contract.objects.select_related('order_group', 'unit_type', 'key_unit__houseunit__floor_type')
    """
    if not contract:
        return None

    # Use provided houseunit or extract from contract
    if houseunit is None:
        if not contract.key_unit:
            return None
        try:
            houseunit = contract.key_unit.houseunit
        except AttributeError:
            return None

    if not houseunit or not hasattr(houseunit, 'floor_type'):
        return None

    try:
        # Query SalesPriceByGT with order_group, unit_type, unit_floor_type
        sales_price = SalesPriceByGT.objects.get(
            order_group=contract.order_group,
            unit_type=contract.unit_type,
            unit_floor_type=houseunit.floor_type
        )
        return sales_price
    except (SalesPriceByGT.DoesNotExist, AttributeError):
        # SalesPriceByGT.DoesNotExist: No matching record
        # AttributeError: contract.order_group/unit_type is None or houseunit.floor_type is None
        return None


def get_contract_price(contract, houseunit=None, is_set=False):
    """
    Get contract price details with flexible fallback logic.

    Args:
        contract: Contract instance
        houseunit: HouseUnit instance (if None, uses contract.key_unit.houseunit)
        is_set: Write mode flag - if True, skips ContractPrice and uses reference pricing only

    Returns:
        tuple: (price, price_build, price_land, price_tax) or (0, 0, 0, 0) if no price found

    Read mode priority (is_set=False):
        1. ContractPrice (all fields if exists)
        2. SalesPriceByGT (all fields matched by order_group, unit_type, unit_floor_type)
        3. ProjectIncBudget.average_price (only price, others 0)
        4. UnitType.average_price (only price, others 0)
        5. (0, 0, 0, 0)

    Write mode priority (is_set=True):
        1. SalesPriceByGT (all fields matched by order_group, unit_type, unit_floor_type)
        2. ProjectIncBudget.average_price (only price, others 0)
        3. UnitType.average_price (only price, others 0)
        4. (0, 0, 0, 0)

    For optimization, use prefetch when calling:
    Contract.objects.select_related(
        'contractprice', 'project', 'order_group', 'unit_type',
        'key_unit__houseunit__floor_type'
    ).prefetch_related('project__projectincbudget_set')
    """
    if not contract:
        return 0, 0, 0, 0

    # Step 1: Check ContractPrice (only in read mode)
    if not is_set:
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
        # Use provided houseunit or get from contract
        if houseunit is not None:
            # Use explicit houseunit parameter
            sales_price = get_sales_price_by_gt(contract, houseunit)
            if sales_price:
                return (
                    sales_price.price or 0,
                    sales_price.price_build or 0,
                    sales_price.price_land or 0,
                    sales_price.price_tax or 0
                )
        else:
            # houseunit is None, use contract.key_unit.houseunit
            pass

    except AttributeError:
        # contract.project, contract.order_group, or contract.unit_type is None
        pass

    # Step 3: Check ProjectIncBudget.average_price (only price, others 0)
    try:
        project_budget = ProjectIncBudget.objects.get(
            project=contract.project,
            order_group=contract.order_group,
            unit_type=contract.unit_type
        )

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
            amount = get_payment_amount(contract, installment)
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


def get_payment_amount(contract, installment_order):
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
                'source': 'calculated'  # or 'payment_per_installment'
            },
            ...
        ]
    """
    if not contract:
        return []

    try:
        # Get unit_floor_type once outside the loop
        unit_floor_type = get_floor_type(contract)

        # Find matching SalesPriceByGT once outside the loop
        sales_price_query = SalesPriceByGT.objects.filter(
            project=contract.project,
            order_group=contract.order_group,
            unit_type=contract.unit_type
        )

        if unit_floor_type:
            sales_price = sales_price_query.filter(unit_floor_type=unit_floor_type).first()
        else:
            sales_price = sales_price_query.first()

        # Cache all manual payments in a dictionary for O(1) lookup
        manual_payments = {}
        if sales_price:
            try:
                manual_payment_qs = PaymentPerInstallment.objects.filter(
                    sales_price=sales_price
                ).select_related('pay_order')

                # Convert to dictionary for O(1) lookup
                manual_payments = {
                    payment.pay_order_id: payment.amount
                    for payment in manual_payment_qs
                }
            except (AttributeError, TypeError, ValueError):
                # AttributeError: sales_price is None or invalid
                # TypeError: Invalid filter parameter types
                # ValueError: Invalid data conversion
                manual_payments = {}

        # Get all installment orders for this contract
        installments = InstallmentPaymentOrder.objects.filter(
            project=contract.project,
            type_sort=contract.unit_type.sort
        ).order_by('pay_code', 'pay_time')

        payment_plan = []

        for installment in installments:
            # Check if there's a manual override using O(1) dictionary lookup
            if installment.id in manual_payments:
                payment_plan.append({
                    'installment_order': installment,
                    'amount': manual_payments[installment.id],
                    'source': 'payment_per_installment'
                })
            else:
                # Calculate amount using priority logic
                amount = get_payment_amount(contract, installment)
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


def get_project_payment_summary(project, order_group=None, unit_type=None):
    """
    Get payment summary for all contracts in a project with installment-wise totals.

    Args:
        project: Project instance
        order_group: OrderGroup instance (optional filter)
        unit_type: UnitType instance (optional filter)

    Returns:
        dict: Summary data with installment-wise totals

    Example return:
        {
            'installment_summaries': [
                {
                    'installment_order': InstallmentPaymentOrder instance,
                    'total_amount': 5000000000,
                    'contract_count': 100,
                    'average_amount': 50000000,
                    'source_breakdown': {
                        'calculated': 4500000000,
                        'payment_per_installment': 500000000
                    }
                }
            ],
            'grand_total': 50000000000,
            'total_contracts': 100
        }
    """
    if not project:
        return {
            'installment_summaries': [],
            'grand_total': 0,
            'total_contracts': 0
        }

    try:
        # Get contracts with optimized queries
        contracts_query = project.contract_set.filter(
            activation=True
        ).select_related(
            'contractprice', 'order_group', 'unit_type',
            'key_unit__houseunit__floor_type'
        ).prefetch_related('project__projectincbudget_set')

        # Apply filters if provided
        if order_group:
            contracts_query = contracts_query.filter(order_group=order_group)
        if unit_type:
            contracts_query = contracts_query.filter(unit_type=unit_type)

        contracts = list(contracts_query)

        if not contracts:
            return {
                'installment_summaries': [],
                'grand_total': 0,
                'total_contracts': 0
            }

        # Get all installment orders for this project
        installments_query = InstallmentPaymentOrder.objects.filter(project=project)
        if unit_type:
            installments_query = installments_query.filter(type_sort=unit_type.sort)

        installments = list(installments_query.order_by('pay_code', 'pay_time'))

        # Initialize summary structure
        installment_summaries = {}
        for installment in installments:
            installment_summaries[installment.id] = {
                'installment_order': installment,
                'total_amount': 0,
                'contract_count': 0,
                'source_breakdown': {
                    'calculated': 0,
                    'payment_per_installment': 0
                }
            }

        # Process each contract's payment plan
        grand_total = 0
        processed_contracts = 0

        for contract in contracts:
            try:
                payment_plan = get_contract_payment_plan(contract)

                contract_has_payments = False
                for plan_item in payment_plan:
                    installment_id = plan_item['installment_order'].id
                    amount = plan_item['amount']
                    source = plan_item['source']

                    if installment_id in installment_summaries:
                        installment_summaries[installment_id]['total_amount'] += amount
                        installment_summaries[installment_id]['source_breakdown'][source] += amount
                        grand_total += amount
                        contract_has_payments = True

                # Only count contracts that have payment data
                if contract_has_payments:
                    for plan_item in payment_plan:
                        installment_id = plan_item['installment_order'].id
                        if installment_id in installment_summaries:
                            installment_summaries[installment_id]['contract_count'] += 1
                            break  # Count each contract only once
                    processed_contracts += 1

            except (AttributeError, TypeError, ValueError) as e:
                # Log error but continue processing other contracts
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f'Error processing contract {contract.id}: {str(e)}')
                continue

        # Convert to list and add average calculations
        result_summaries = []
        for summary_data in installment_summaries.values():
            if summary_data['contract_count'] > 0:
                summary_data['average_amount'] = summary_data['total_amount'] // summary_data['contract_count']
            else:
                summary_data['average_amount'] = 0

            # Only include installments that have data
            if summary_data['total_amount'] > 0:
                result_summaries.append(summary_data)

        # Sort by installment order
        result_summaries.sort(key=lambda x: (x['installment_order'].pay_code, x['installment_order'].pay_time))

        return {
            'installment_summaries': result_summaries,
            'grand_total': grand_total,
            'total_contracts': processed_contracts
        }

    except (AttributeError, TypeError) as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Error in get_project_payment_summary: {str(e)}')
        return {
            'installment_summaries': [],
            'grand_total': 0,
            'total_contracts': 0
        }


def get_multiple_projects_payment_summary(projects, order_group=None, unit_type=None):
    """
    Get payment summary for multiple projects.

    Args:
        projects: List of Project instances
        order_group: OrderGroup instance (optional filter)
        unit_type: UnitType instance (optional filter)

    Returns:
        dict: Combined summary data for all projects
    """
    if not projects:
        return {
            'installment_summaries': [],
            'grand_total': 0,
            'total_contracts': 0
        }

    combined_summaries = {}
    combined_grand_total = 0
    combined_total_contracts = 0

    for project in projects:
        try:
            project_summary = get_project_payment_summary(project, order_group, unit_type)

            combined_total_contracts += project_summary['total_contracts']
            combined_grand_total += project_summary['grand_total']

            # Merge installment summaries
            for summary in project_summary['installment_summaries']:
                installment_id = summary['installment_order'].id

                if installment_id not in combined_summaries:
                    combined_summaries[installment_id] = {
                        'installment_order': summary['installment_order'],
                        'total_amount': 0,
                        'contract_count': 0,
                        'source_breakdown': {
                            'calculated': 0,
                            'payment_per_installment': 0
                        }
                    }

                combined_summaries[installment_id]['total_amount'] += summary['total_amount']
                combined_summaries[installment_id]['contract_count'] += summary['contract_count']
                combined_summaries[installment_id]['source_breakdown']['calculated'] += summary['source_breakdown'][
                    'calculated']
                combined_summaries[installment_id]['source_breakdown']['payment_per_installment'] += \
                    summary['source_breakdown']['payment_per_installment']

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f'Error processing project {project.id}: {str(e)}')
            continue

    # Convert to list and add averages
    result_summaries = []
    for summary_data in combined_summaries.values():
        if summary_data['contract_count'] > 0:
            summary_data['average_amount'] = summary_data['total_amount'] // summary_data['contract_count']
        else:
            summary_data['average_amount'] = 0
        result_summaries.append(summary_data)

    # Sort by installment order
    result_summaries.sort(key=lambda x: (x['installment_order'].pay_code, x['installment_order'].pay_time))

    return {
        'installment_summaries': result_summaries,
        'grand_total': combined_grand_total,
        'total_contracts': combined_total_contracts
    }
