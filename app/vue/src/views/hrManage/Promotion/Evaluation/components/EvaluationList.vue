<script lang="ts" setup>
import { computed } from 'vue'
import { usePerms } from '@/composables/usePerms.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { TableSecondary } from '@/utils/cssMixins.ts'
import { type StaffEvaluation as StaffEvaluationType } from '@/store/types/company.ts'
import Pagination from '@/components/Pagination'
import Evaluation from './Evaluation.vue'

const emit = defineEmits(['page-select', 'multi-submit', 'on-delete'])

const { canGlobal, PERM } = usePerms()
const canHrWorkManage = computed(
  () => canGlobal(PERM.HQ_HR_WORK_CREATE) || canGlobal(PERM.HQ_HR_WORK_UPDATE),
)

const companyStore = useCompany()
const staffEvaluationList = computed(() => companyStore.staffEvaluationList)
const staffEvaluationsCount = computed(() => companyStore.staffEvaluationsCount)

const staffEvaluationPages = (page: number) => companyStore.staffEvaluationPages(page)
const pageSelect = (page: number) => emit('page-select', page)
const multiSubmit = (payload: StaffEvaluationType) => emit('multi-submit', payload)
const onDelete = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTable hover responsive bordered align="middle">
    <colgroup>
      <col style="width: 8%" />
      <col style="width: 8%" />
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 8%" />
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 20%" />
      <col style="width: 11%" />
      <col v-if="canHrWorkManage" style="width: 5%" />
    </colgroup>

    <CTableHead :color="TableSecondary">
      <CTableRow class="text-center" align="middle">
        <CTableHeaderCell scope="col">평가연도</CTableHeaderCell>
        <CTableHeaderCell scope="col">평가주기</CTableHeaderCell>
        <CTableHeaderCell scope="col">피평가자</CTableHeaderCell>
        <CTableHeaderCell scope="col">평가등급</CTableHeaderCell>
        <CTableHeaderCell scope="col">환산점수</CTableHeaderCell>
        <CTableHeaderCell scope="col">1차 평가자</CTableHeaderCell>
        <CTableHeaderCell scope="col">2차 확인자</CTableHeaderCell>
        <CTableHeaderCell scope="col">주요 업적 요약</CTableHeaderCell>
        <CTableHeaderCell scope="col">종합 의견</CTableHeaderCell>
        <CTableHeaderCell v-if="canHrWorkManage" scope="col">관리</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <Evaluation
        v-for="evaluation in staffEvaluationList"
        :key="evaluation.pk"
        :evaluation="evaluation"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
      />
      <CTableRow v-if="staffEvaluationList.length === 0">
        <CTableDataCell :colspan="canHrWorkManage ? 10 : 9" class="text-center text-muted py-4">
          조회된 인사/업적 평가 내역이 없습니다.
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>

  <Pagination
    v-if="staffEvaluationsCount > 10"
    :active-page="1"
    :limit="8"
    :pages="staffEvaluationPages(10)"
    class="mt-3"
    @active-page-change="pageSelect"
  />
</template>
