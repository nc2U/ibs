<script lang="ts" setup>
import { computed } from 'vue'
import { useProject } from '@/store/pinia/project'
import { usePerms } from '@/composables/usePerms'
import type { ProOutBudget } from '@/store/types/project'
import { TableSecondary } from '@/utils/cssMixins'
import OutBudget from './OutBudget.vue'

const emit = defineEmits<{
  (e: 'on-update', payload: ProOutBudget): void
  (e: 'on-delete', pk: number): void
}>()

const { can, PERM } = usePerms()
const canProjectUpdate = computed(() => can(PERM.PROJECT_UPDATE))

const proStore = useProject()
const proOutBudgetList = computed(() => proStore.proOutBudgetList)

const onUpdateBudget = (payload: ProOutBudget) => emit('on-update', payload)
const onDeleteBudget = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTable hover responsive>
    <colgroup>
      <col :style="{ width: canProjectUpdate ? '20%' : '22%' }" />
      <col :style="{ width: canProjectUpdate ? '30%' : '34%' }" />
      <col :style="{ width: canProjectUpdate ? '20%' : '22%' }" />
      <col :style="{ width: canProjectUpdate ? '20%' : '22%' }" />
      <col v-if="canProjectUpdate" style="width: 10%" />
    </colgroup>
    <CTableHead :color="TableSecondary" class="text-center">
      <CTableRow>
        <CTableHeaderCell>계정 과목</CTableHeaderCell>
        <CTableHeaderCell>산출 근거</CTableHeaderCell>
        <CTableHeaderCell>기초 지출 예산</CTableHeaderCell>
        <CTableHeaderCell>현황 지출 예산</CTableHeaderCell>
        <CTableHeaderCell v-if="canProjectUpdate">비 고</CTableHeaderCell>
      </CTableRow>
    </CTableHead>
    <CTableBody v-if="proOutBudgetList.length > 0">
      <OutBudget
        v-for="budget in proOutBudgetList"
        :key="budget.pk"
        :budget="budget"
        @on-update="onUpdateBudget"
        @on-delete="onDeleteBudget"
      />
    </CTableBody>

    <CTableBody v-else>
      <CTableRow>
        <CTableDataCell :colspan="canProjectUpdate ? 5 : 4" class="text-center p-5 text-danger">
          등록된 데이터가 없습니다.
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
