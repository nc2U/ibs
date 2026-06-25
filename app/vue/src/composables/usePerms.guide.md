# Permission Composable Guide (`usePerms`)

이 컴포저블은 프로젝트 내 UI 수준의 권한 제어를 위해 설계되었습니다. `Pinia` 스토어를 직접 호출하는 것보다 더 편리하고 간결한 API를 제공합니다.

## 사용 방법

### 1. 템플릿 (`<template>`)에서 사용
`v-if` 또는 `v-show`를 통해 특정 요소의 노출을 제어합니다.

```vue
<template>
  <button v-if="can(PERM.ISSUE_CREATE)">업무 생성</button>
  <button v-if="can(PERM.ISSUE_DELETE)" @click="handleDelete">업무 삭제</button>
</template>

<script setup>
import { usePerms } from '@/composables/usePerms';
const { can, PERM } = usePerms();
</script>
```

### 2. 스크립트 (`<script>`)에서 사용
비즈니스 로직 내에서 권한을 체크해야 할 때 사용합니다.

```javascript
const { can, PERM } = usePerms();

const doAction = () => {
  if (can(PERM.PROJECT_UPDATE)) {
    // 업데이트 로직 수행
  } else {
    message('warning', '권한 없음', '수정 권한이 없습니다.');
  }
};
```

### 3. 다중 권한 체크
배열을 전달하면, 모든 권한을 가지고 있을 때만 `true`를 반환합니다.

```javascript
// 두 권한을 모두 가지고 있어야 함
if (can([PERM.PROJECT_UPDATE, PERM.ISSUE_DELETE])) {
  // 관리자용 로직
}
```

## ⚠️ 중요 주의사항
- **UI 제어용:** 프론트엔드의 `can()` 함수는 사용자 경험(UX)을 위한 것입니다.
- **백엔드 검증 필수:** 사용자가 직접 API를 호출할 수 있으므로, **모든 API 요청은 반드시 백엔드(Django)에서 권한 검증을 다시 수행**해야 합니다.
