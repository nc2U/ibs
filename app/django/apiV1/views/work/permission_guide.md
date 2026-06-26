# Django Backend Permission Implementation Guide (`ProjectPermission`)

본 가이드는 `ProjectPermission`을 활용하여 `work` 앱 내의 각 `ViewSet`에서 프로젝트 단위의 정교한 권한 제어를 구현하는 방법을 설명합니다.

## 1. 기본 원칙

`ProjectPermission`은 `ViewSet`의 `required_permission` 속성을 참조하여 사용자가 해당 액션을 수행할 권한이 있는지 판단합니다.

## 2. 구현 방법

### Step 1: Permission 클래스 적용

`ViewSet`의 `permission_classes`에 `ProjectPermission`을 추가합니다. 반드시 `permissions.IsAuthenticated`가 포함되어야 합니다.

```python
from rest_framework import permissions, viewsets
from apiV1.permission import ProjectPermission


class IssueViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, ProjectPermission]
    ...
```

### Step 2: `required_permission` 속성 정의

`self.action`을 기반으로 필요한 권한 코드를 반환하는 `@property`를 정의합니다.

```python
from rest_framework import viewsets, permissions
from apiV1.permission import ProjectPermission


class IssueViewSet(viewsets.ModelViewSet):
    # 1. 권한 클래스 적용
    permission_classes = [permissions.IsAuthenticated, ProjectPermission]

    # 2. 필요한 권한 매핑 정의
    @property
    def required_permission(self):
        # 매핑 로직 정의
        mapping = {
            'list': 'issue.read',
            'retrieve': 'issue.read',
            'create': 'issue.create',
            'update': 'issue.update',
            'partial_update': 'issue.update',
            'destroy': 'issue.delete'
        }
        # 정의되지 않은 액션에 대해 기본 권한 반환
        return mapping.get(self.action, 'issue.read')
```

## 3. 핵심 주의사항

### A. 데이터 필터링 (`get_queryset`) - 보안 필수

`ProjectPermission`은 특정 객체(`obj`)에 대한 접근 권한만 체크합니다. 목록 조회(`list`) 시 권한이 없는 프로젝트의 데이터가 노출되지 않도록 `get_queryset`에서 필터링해야
합니다.

```python
def get_queryset(self):
    user = self.request.user
    # 관리자는 전체 조회 가능
    if user.is_superuser or user.work_manager:
        return self.queryset
    # 사용자가 멤버로 포함된 프로젝트의 데이터만 반환
    return self.queryset.filter(project__members__user=user)
```

### B. 권한 코드 동기화

프론트엔드(`app/vue/src/store/constants/permissions.ts`)와 백엔드 DB(`work.models.project.Permission`)에 저장된 권한 코드는 반드시 일치해야 합니다.

### C. 커스텀 액션 처리

커스텀 액션(예: `@action`)을 사용하는 경우에도 `required_permission`에서 해당 액션명을 케이스로 처리하십시오.

```python
    @property


def required_permission(self):
    if self.action == 'my_custom_action':
        return 'issue.special_perm'
    ...
```
