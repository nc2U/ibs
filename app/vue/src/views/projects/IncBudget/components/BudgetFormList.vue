<script lang="ts" setup>
import { computed } from 'vue'
import { write_project } from '@/utils/pageAuth'
import { useProject } from '@/store/pinia/project'
import { TableSecondary } from '@/utils/cssMixins'
import { type ProIncBudget } from '@/store/types/project'
import IncBudget from './IncBudget.vue'

const emit = defineEmits(['on-update', 'on-delete'])

const proStore = useProject()
const proIncBudgetList = computed(() => proStore.proIncBudgetList)

const onUpdateOrder = (payload: ProIncBudget) => emit('on-update', payload)
const onDeleteOrder = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTable hover responsive>
    <colgroup>
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 11%" />
      <col style="width: 11%" />
      <col v-if="write_project" style="width: 8%" />
    </colgroup>
    <CTableHead :color="TableSecondary" class="text-center">
      <CTableRow>
        <CTableHeaderCell>계정과목</CTableHeaderCell>
        <CTableHeaderCell>차수 그룹명</CTableHeaderCell>
        <CTableHeaderCell>타입명</CTableHeaderCell>
        <CTableHeaderCell>항목 명칭</CTableHeaderCell>
        <CTableHeaderCell>단위 세대 (평균)단가</CTableHeaderCell>
        <CTableHeaderCell>수량</CTableHeaderCell>
        <CTableHeaderCell>기초 수입 예산</CTableHeaderCell>
        <CTableHeaderCell>현황 수입 예산</CTableHeaderCell>
        <CTableHeaderCell v-if="write_project">비 고</CTableHeaderCell>
      </CTableRow>
    </CTableHead>
    <CTableBody v-if="proIncBudgetList.length > 0">
      <IncBudget
        v-for="budget in proIncBudgetList"
        :key="budget.pk"
        :budget="budget"
        @on-update="onUpdateOrder"
        @on-delete="onDeleteOrder"
      />
    </CTableBody>

    <CTableBody v-else>
      <CTableRow>
        <CTableDataCell :colspan="write_project ? 10 : 9" class="text-center p-5 text-danger">
          등록된 데이터가 없습니다.
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
