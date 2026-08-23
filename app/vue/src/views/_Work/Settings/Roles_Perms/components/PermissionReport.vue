<script setup lang="ts">
import { useWork } from '@/store/pinia/work_project'
import type { Role, GroupedPermissions } from '@/store/types/work_project'

const props = defineProps<{
  roleList: Role[]
  groupedPermissions: GroupedPermissions | null
  workManager: boolean
}>()

const workStore = useWork()

const categoryLabel = (cat: string) => {
  const labels: Record<string, string> = {
    work_core: '업무 관리 관련 권한 (work_core)',
    ibs_hq_manage: '본사 관리 관련 권한 (ibs_hq_manage)',
    ibs_pm_manage: '프로젝트 관리 관련 권한 (ibs_pm_manage)',
  }
  return labels[cat] || cat
}

const getRolesByCategory = (category: string) => {
  return props.roleList.filter(r => {
    return (r.category || 'work_core') === category
  })
}

const sortLabel = (sort: string) => {
  const labels: Record<string, string> = {
    project: '프로젝트',
    meeting: '회의',
    issue: '업무',
    news: '공지',
    docs: '문서',
    forum: '게시판',
    calendar: '캘린더',
    contract: '계약 관리',
    payment: '수납 관리',
    notice: '고지 관리',
    ledger: '자금/원장 관리',
    site: '사업 부지 관리',
    hr_work: '인사 관리',
  }
  return labels[sort] || sort
}

const hasPermission = (role: Role, permissionPk: number) => {
  return role.permissions.includes(permissionPk)
}

const togglePermission = async (role: Role, permissionPk: number) => {
  const newPermissions = [...role.permissions]
  const index = newPermissions.indexOf(permissionPk)
  if (index === -1) {
    newPermissions.push(permissionPk)
  } else {
    newPermissions.splice(index, 1)
  }
  await workStore.patchRole({ pk: role.pk, permissions: newPermissions })
}
</script>

<template>
  <div class="space-y-5">
    <!-- 1. 협업 및 업무 관리 권한 (work_core) 테이블 -->
    <div class="pt-4 mb-5">
      <h6 class="fw-bold text-success mb-3">
        <v-icon icon="mdi-account-group-outline" size="small" class="mr-2" />
        {{ categoryLabel('work_core') }}
      </h6>
      <div class="table-responsive">
        <table class="table table-bordered table-hover align-middle">
          <thead class="table-light">
            <tr>
              <th scope="col" class="sticky-col-header" style="min-width: 200px">권한</th>
              <th
                v-for="role in getRolesByCategory('work_core')"
                :key="role.pk"
                scope="col"
                class="text-center"
                style="min-width: 100px"
              >
                {{ role.name }}
              </th>
            </tr>
          </thead>
          <tbody>
            <template v-for="(perms, sort) in groupedPermissions?.work_core" :key="sort">
              <tr class="table-secondary">
                <td
                  :colspan="getRolesByCategory('work_core').length + 1"
                  class="fw-bold ps-3"
                >
                  {{ sortLabel(sort as string) }}
                </td>
              </tr>
              <tr v-for="perm in perms" :key="perm.pk">
                <td class="ps-4">
                  <div class="fw-semibold">{{ perm.name }}</div>
                  <small class="text-muted">{{ perm.description }}</small>
                </td>
                <td
                  v-for="role in getRolesByCategory('work_core')"
                  :key="role.pk"
                  class="text-center"
                >
                  <CFormCheck
                    :id="`perm-${role.pk}-${perm.pk}`"
                    :checked="hasPermission(role, perm.pk)"
                    :disabled="!workManager"
                    @change="togglePermission(role, perm.pk)"
                  />
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 2. 본사 관리 권한 (ibs_hq_manage) 테이블 -->
    <div v-if="getRolesByCategory('ibs_hq_manage').length > 0" class="mb-5">
      <h6 class="fw-bold text-warning mb-3">
        <v-icon icon="mdi-domain" size="small" class="mr-2" />
        {{ categoryLabel('ibs_hq_manage') }}
      </h6>
      <div class="table-responsive">
        <table class="table table-bordered table-hover align-middle">
          <thead class="table-light">
            <tr>
              <th scope="col" class="sticky-col-header" style="min-width: 200px">권한</th>
              <th
                v-for="role in getRolesByCategory('ibs_hq_manage')"
                :key="role.pk"
                scope="col"
                class="text-center"
                style="min-width: 100px"
              >
                {{ role.name }}
                <v-chip v-if="role.is_confidential" color="danger" size="x-small" class="ms-1">보안</v-chip>
              </th>
            </tr>
          </thead>
          <tbody>
            <template v-for="(perms, sort) in groupedPermissions?.ibs_hq_manage" :key="sort">
              <tr class="table-secondary">
                <td
                  :colspan="getRolesByCategory('ibs_hq_manage').length + 1"
                  class="fw-bold ps-3"
                >
                  {{ sortLabel(sort as string) }}
                </td>
              </tr>
              <tr v-for="perm in perms" :key="perm.pk">
                <td class="ps-4">
                  <div class="fw-semibold">{{ perm.name }}</div>
                  <small class="text-muted">{{ perm.description }}</small>
                </td>
                <td
                  v-for="role in getRolesByCategory('ibs_hq_manage')"
                  :key="role.pk"
                  class="text-center"
                >
                  <CFormCheck
                    :id="`perm-${role.pk}-${perm.pk}`"
                    :checked="hasPermission(role, perm.pk)"
                    :disabled="!workManager"
                    @change="togglePermission(role, perm.pk)"
                  />
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 3. 프로젝트 관리 권한 (ibs_pm_manage) 테이블 -->
    <div>
      <h6 class="fw-bold text-primary mb-3">
        <v-icon icon="mdi-database-outline" size="small" class="mr-2" />
        {{ categoryLabel('ibs_pm_manage') }}
      </h6>
      <div class="table-responsive">
        <table class="table table-bordered table-hover align-middle">
          <thead class="table-light">
            <tr>
              <th scope="col" class="sticky-col-header" style="min-width: 200px">권한</th>
              <th
                v-for="role in getRolesByCategory('ibs_pm_manage')"
                :key="role.pk"
                scope="col"
                class="text-center"
                style="min-width: 100px"
              >
                {{ role.name }}
              </th>
            </tr>
          </thead>
          <tbody>
            <template v-for="(perms, sort) in groupedPermissions?.ibs_pm_manage" :key="sort">
              <tr class="table-secondary">
                <td
                  :colspan="getRolesByCategory('ibs_pm_manage').length + 1"
                  class="fw-bold ps-3"
                >
                  {{ sortLabel(sort as string) }}
                </td>
              </tr>
              <tr v-for="perm in perms" :key="perm.pk">
                <td class="ps-4">
                  <div class="fw-semibold">{{ perm.name }}</div>
                  <small class="text-muted">{{ perm.description }}</small>
                </td>
                <td
                  v-for="role in getRolesByCategory('ibs_pm_manage')"
                  :key="role.pk"
                  class="text-center"
                >
                  <CFormCheck
                    :id="`perm-${role.pk}-${perm.pk}`"
                    :checked="hasPermission(role, perm.pk)"
                    :disabled="!workManager"
                    @change="togglePermission(role, perm.pk)"
                  />
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sticky-col-header {
  position: sticky;
  left: 0;
  z-index: 10;
  background-color: inherit;
}

.table-responsive {
  max-height: calc(100vh - 250px);
  overflow: auto;
}

thead th {
  position: sticky;
  top: 0;
  z-index: 20;
}

thead th.sticky-col-header {
  z-index: 30;
}
</style>
