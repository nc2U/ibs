from django.db import connection

# API의 메인 쿼리와 동일한 로직으로 확인
print("=== API 메인 쿼리 결과 ===")

project_id = 1

with connection.cursor() as cursor:
    # API의 메인 쿼리
    query = """
            SELECT
                pib.order_group_id as order_group_id,
                og.name as order_group_name,
                pib.unit_type_id as unit_type_id,
                ut.name as unit_type_name,
                ut.color as unit_type_color,
                pib.quantity as planned_units,
                pib.budget as total_budget,
                pib.average_price as average_price

            FROM project_projectincbudget pib
            INNER JOIN items_unittype ut ON pib.unit_type_id = ut.id
            INNER JOIN contract_ordergroup og ON pib.order_group_id = og.id
            WHERE pib.project_id = %s
            ORDER BY order_group_id, unit_type_id
            """

    cursor.execute(query, [project_id])

    print("ProjectIncBudget에서 가져온 데이터:")
    for row in cursor.fetchall():
        order_group_id = row[0]
        order_group_name = row[1]
        unit_type_id = row[2]
        unit_type_name = row[3]

        print(f"{order_group_name} (ID: {order_group_id}) | {unit_type_name} (ID: {unit_type_id})")

        # 각 행에 대해 미계약 세대수 계산
        from apiV1.views.payment import PaymentStatusByUnitTypeViewSet
        non_contract_units = PaymentStatusByUnitTypeViewSet._get_non_contract_units_by_unit_type(
            project_id, order_group_id, unit_type_id
        )
        print(f"  → 미계약 세대수: {non_contract_units}")
        print()

print("\n=== 일반분양 order_group 확인 ===")
from project.models import Project
from contract.models import OrderGroup

project = Project.objects.get(pk=project_id)
default_og = OrderGroup.get_default_for_project(project)

print(f"기본 order_group: {default_og.name} (ID: {default_og.pk})")

# ProjectIncBudget에 일반분양이 있는지 확인
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT COUNT(*)
        FROM project_projectincbudget pib
        WHERE pib.project_id = %s
          AND pib.order_group_id = %s
    """, [project_id, default_og.pk])

    count = cursor.fetchone()[0]
    print(f"ProjectIncBudget에서 일반분양 (ID: {default_og.pk}) 레코드 수: {count}")

    if count == 0:
        print("⚠️ 문제 발견: ProjectIncBudget에 일반분양 데이터가 없습니다!")
        print("   → 미계약 세대는 일반분양에만 할당되지만, ProjectIncBudget에 일반분양 행이 없어서 API 결과에 나타나지 않음")