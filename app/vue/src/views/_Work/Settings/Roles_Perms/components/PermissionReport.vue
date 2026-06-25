<script setup lang="ts">
import { computed } from 'vue'
import { useWork } from '@/store/pinia/work_project'
import type { Role, Permission } from '@/store/types/work_project'

const props = defineProps<{
  roleList: Role[]
  permissionList: Permission[]
  workManager: boolean
}>()

const workStore = useWork()

const permissionGroups = computed(() => {
  const groups: Record<string, Permission[]> = {}
  props.permissionList.forEach(p => {
    if (!groups[p.module]) groups[p.module] = []
    groups[p.module].push(p)
  })
  return groups
})

const sortLabel = (sort: string) => {
  const labels: Record<string, string> = {
    project: '프로젝트',
    meeting: '회의',
    issue: '업무',
    news: '공지',
    docs: '문서',
    forum: '게시판',
    calendar: '달력',
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
  <div class="table-responsive">
    <table class="table table-bordered table-hover align-middle">
      <thead class="table-light">
        <tr>
          <th scope="col" class="sticky-col-header" style="min-width: 200px">권한</th>
          <th
            v-for="role in roleList"
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
        <template v-for="(perms, sort) in permissionGroups" :key="sort">
          <tr class="table-secondary">
            <td :colspan="roleList.length + 1" class="fw-bold">
              {{ sortLabel(sort as string) }}
            </td>
          </tr>
          <tr v-for="perm in perms" :key="perm.pk">
            <td class="ps-4">
              <div class="fw-semibold">{{ perm.name }}</div>
              <small class="text-muted">{{ perm.description }}</small>
            </td>
            <td v-for="role in roleList" :key="role.pk" class="text-center">
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
  background-color: #f8f9fa !important;
}

thead th.sticky-col-header {
  z-index: 30;
}
</style>
