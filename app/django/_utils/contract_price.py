from payment.models import SalesPriceByGT
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
    Get contract price with 5-step fallback logic.

    Args:
        contract: Contract instance

    Returns:
        int: Price value or None if no price found

    Priority order:
        1. ContractPrice.price (if exists)
        2. SalesPriceByGT.price (matched by order_group, unit_type, unit_floor_type)
        3. ProjectIncBudget.average_price
        4. UnitType.average_price
        5. None

    For optimization, use prefetch when calling:
    Contract.objects.select_related(
        'contractprice', 'project', 'order_group', 'unit_type',
        'key_unit__houseunit__floor_type'
    ).prefetch_related('project__projectincbudget_set')
    """
    if not contract:
        return None

    # Step 1: Check ContractPrice.price
    try:
        return contract.contractprice.price
    except AttributeError:
        pass

    # Step 2: Check SalesPriceByGT
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
                return sales_price.price

        # Try without unit_floor_type
        sales_price = sales_price_query.first()
        if sales_price:
            return sales_price.price

    except AttributeError:
        # contract.project, contract.order_group, or contract.unit_type is None
        pass

    # Step 3: Check ProjectIncBudget.average_price
    try:
        project_budget = ProjectIncBudget.objects.filter(
            project=contract.project,
            unit_type=contract.unit_type
        ).first()

        if project_budget and project_budget.average_price:
            return project_budget.average_price

    except AttributeError:
        # contract.project or contract.unit_type is None
        pass

    # Step 4: Check UnitType.average_price
    try:
        if contract.unit_type and contract.unit_type.average_price:
            return contract.unit_type.average_price
    except AttributeError:
        pass

    # Step 5: Return None
    return None
