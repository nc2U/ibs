<script setup lang="ts">
import type { Role } from '@/store/types/work_project'
import TopButton from '@/views/_Work/components/atomics/TopButton.vue'

defineProps<{ roleList: Role[]; workManager: boolean }>()
const emit = defineEmits(['show-modal', 'delete-role'])

const copyRole = (role: Role) => {
  const copied: Role = { ...role, pk: 0, name: '' }
  emit('show-modal', copied)
}
</script>

<template>
  <div class="d-flex justify-content-between align-items-center pt-3 mb-3">
    <CCol>
      <h5>{{ $route.name }}</h5>
    </CCol>
    <CCol class="text-right">
      <span v-if="workManager" class="mr-2 form-text">
        <TopButton name="새 역할" @click="emit('show-modal')" />
      </span>
    </CCol>
  </div>

  <CTable hover responsive align="middle">
    <CTableHead color="light">
      <CTableRow>
        <CTableHeaderCell scope="col">역할</CTableHeaderCell>
        <CTableHeaderCell scope="col" class="text-center">업무할당 가능 여부</CTableHeaderCell>
        <CTableHeaderCell scope="col" class="text-center">업무 보기 권한</CTableHeaderCell>
        <CTableHeaderCell scope="col" class="text-center">사용자 보기 권한</CTableHeaderCell>
        <CTableHeaderCell scope="col"></CTableHeaderCell>
      </CTableRow>
    </CTableHead>
    <CTableBody>
      <CTableRow v-for="role in roleList" :key="role.pk">
        <CTableHeaderCell scope="row">
          <a
            href="javascript:void(0)"
            class="text-decoration-none"
            @click="emit('show-modal', role)"
          >
            {{ role.name }}
          </a>
        </CTableHeaderCell>
        <CTableDataCell class="text-center">
          <CIcon v-if="role.assignable" name="cil-check" class="text-success" />
        </CTableDataCell>
        <CTableDataCell class="text-center">
          {{ role.issue_visible }}
        </CTableDataCell>
        <CTableDataCell class="text-center"> {{ role.user_visible }}</CTableDataCell>
        <CTableDataCell class="text-end">
          <v-btn
            color="info"
            size="x-small"
            class="me-1"
            :disabled="!workManager"
            @click="copyRole(role)"
          >
            복사
          </v-btn>
          <v-btn
            v-if="role.pk > 2"
            color="success"
            size="x-small"
            class="me-1"
            :disabled="!workManager"
            @click="emit('show-modal', role)"
          >
            수정
          </v-btn>
          <v-btn
            v-if="role.pk > 2"
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
