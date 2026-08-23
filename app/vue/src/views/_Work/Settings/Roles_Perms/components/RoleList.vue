<script setup lang="ts">
import type { Role } from '@/store/types/work_project'

defineProps<{ roleList: Role[]; workManager: boolean }>()
const emit = defineEmits(['show-modal', 'delete-role'])

const copyRole = (role: Role) => {
  const copied: Role = { ...role, pk: 0, name: '' }
  emit('show-modal', copied)
}
</script>

<template>
  <CTable hover responsive align="middle" class="border-top">
    <CTableHead color="light">
      <CTableRow>
        <CTableHeaderCell scope="col">구분</CTableHeaderCell>
        <CTableHeaderCell scope="col">역할</CTableHeaderCell>
        <CTableHeaderCell scope="col" class="text-center">업무 할당 가능 여부</CTableHeaderCell>
        <CTableHeaderCell scope="col" class="text-center">업무 보기 권한</CTableHeaderCell>
        <CTableHeaderCell scope="col" class="text-center">사용자 보기 권한</CTableHeaderCell>
        <CTableHeaderCell scope="col"></CTableHeaderCell>
      </CTableRow>
    </CTableHead>
    <CTableBody>
      <CTableRow v-for="role in roleList" :key="role.pk">
        <CTableDataCell>
          <span
            :class="
              role.category === 'ibs_hq_manage'
                ? 'text-warning'
                : role.category === 'ibs_pm_manage'
                  ? 'text-primary'
                  : 'text-success'
            "
          >
            <v-icon
              :icon="
                role.category === 'ibs_hq_manage'
                  ? 'mdi-domain'
                  : role.category === 'ibs_pm_manage'
                    ? 'mdi-database-outline'
                    : 'mdi-account-group-outline'
              "
              size="small"
              class="mr-1"
            />
            {{
              role.category === 'ibs_hq_manage'
                ? '본사'
                : role.category === 'ibs_pm_manage'
                  ? '프로젝트'
                  : '업무관리'
            }}
          </span>
        </CTableDataCell>
        <CTableHeaderCell scope="row">
          <a
            href="javascript:void(0)"
            class="text-decoration-none fw-bold"
            @click="emit('show-modal', role)"
          >
            {{ role.name }}
          </a>
          <v-chip v-if="role.is_confidential" color="danger" size="x-small" class="ms-1">보안</v-chip>
        </CTableHeaderCell>
        <CTableDataCell class="text-center">
          <CIcon v-if="role.assignable" name="cil-check" class="text-success" />
        </CTableDataCell>
        <CTableDataCell class="text-center">
          {{ role.issue_visible_desc }}
        </CTableDataCell>
        <CTableDataCell class="text-center"> {{ role.user_visible_desc }}</CTableDataCell>
        <CTableDataCell class="text-end">
          <v-btn
            color="light"
            size="x-small"
            class="me-1"
            :disabled="!workManager"
            @click="copyRole(role)"
            flat
          >
            복사
          </v-btn>
          <v-btn
            color="success"
            size="x-small"
            class="me-1"
            :disabled="!workManager"
            @click="emit('show-modal', role)"
          >
            수정
          </v-btn>
          <v-btn
            color="warning"
            size="x-small"
            :disabled="!workManager"
            @click="emit('delete-role', role.pk)"
          >
            삭제
          </v-btn>
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
