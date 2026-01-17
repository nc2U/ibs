<script lang="ts" setup>
import { computed } from 'vue'
import { write_project } from '@/utils/pageAuth'
import { useProject } from '@/store/pinia/project'
import { type ProOutBudget } from '@/store/types/project'
import { TableSecondary } from '@/utils/cssMixins'
import OutBudget from './OutBudget.vue'

const emit = defineEmits(['on-update', 'on-delete'])

const proStore = useProject()
const proOutBudgetList = computed(() => proStore.proOutBudgetList)

const onUpdateOrder = (payload: ProOutBudget) => emit('on-update', payload)
const onDeleteOrder = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTable hover responsive>
    <colgroup>
      <col style="width: 20%" />
      <col style="width: 20%" />
      <col style="width: 20%" />
      <col style="width: 20%" />
      <col v-if="write_project" style="width: 10%" />
    </colgroup>
    <CTableHead :color="TableSecondary" class="text-center">
      <CTableRow>
        <CTableHeaderCell>계정 과목</CTableHeaderCell>
        <CTableHeaderCell>산출 근거</CTableHeaderCell>
        <CTableHeaderCell>기초 지출 예산</CTableHeaderCell>
        <CTableHeaderCell>현황 지출 예산</CTableHeaderCell>
        <CTableHeaderCell v-if="write_project">비 고</CTableHeaderCell>
      </CTableRow>
    </CTableHead>
    <CTableBody v-if="proOutBudgetList.length > 0">
      <OutBudget
        v-for="budget in proOutBudgetList"
        :key="budget.pk"
        :budget="budget"
        @on-update="onUpdateOrder"
        @on-delete="onDeleteOrder"
      />
    </CTableBody>

    <CTableBody v-else>
      <CTableRow>
        <CTableDataCell :colspan="write_project ? 7 : 6" class="text-center p-5 text-danger">
          등록된 데이터가 없습니다.
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
