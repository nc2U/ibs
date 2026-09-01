<script lang="ts" setup>
import { computed } from 'vue'
import { usePerms } from '@/composables/usePerms.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { TableSecondary } from '@/utils/cssMixins.ts'
import { type PromotionCandidate as PromotionCandidateType } from '@/store/types/company.ts'
import Pagination from '@/components/Pagination'
import Candidate from './Candidate.vue'

const emit = defineEmits(['page-select', 'multi-submit', 'on-delete'])

const { canGlobal, PERM } = usePerms()
const canHrWorkManage = computed(
  () => canGlobal(PERM.HQ_HR_WORK_CREATE) || canGlobal(PERM.HQ_HR_WORK_UPDATE),
)

const companyStore = useCompany()
const promotionCandidateList = computed(() => companyStore.promotionCandidateList)
const promotionCandidatesCount = computed(() => companyStore.promotionCandidatesCount)

const promotionCandidatePages = (page: number) => companyStore.promotionCandidatePages(page)
const pageSelect = (page: number) => emit('page-select', page)
const multiSubmit = (payload: PromotionCandidateType) => emit('multi-submit', payload)
const onDelete = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTable hover responsive bordered align="middle">
    <colgroup>
      <col style="width: 8%" />
      <col style="width: 12%" />
      <col style="width: 16%" />
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 11%" />
      <col style="width: 18%" />
      <col v-if="canHrWorkManage" style="width: 5%" />
    </colgroup>

    <CTableHead :color="TableSecondary">
      <CTableRow class="text-center" align="middle">
        <CTableHeaderCell scope="col">심사연도</CTableHeaderCell>
        <CTableHeaderCell scope="col">대상직원</CTableHeaderCell>
        <CTableHeaderCell scope="col">승급 대상 직급</CTableHeaderCell>
        <CTableHeaderCell scope="col">현직급 체류</CTableHeaderCell>
        <CTableHeaderCell scope="col">평가 점수</CTableHeaderCell>
        <CTableHeaderCell scope="col">심사 상태</CTableHeaderCell>
        <CTableHeaderCell scope="col">승진 발령일</CTableHeaderCell>
        <CTableHeaderCell scope="col">인사위원회 심의 의견</CTableHeaderCell>
        <CTableHeaderCell v-if="canHrWorkManage" scope="col">관리</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <Candidate
        v-for="candidate in promotionCandidateList"
        :key="candidate.pk"
        :candidate="candidate"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
      />
      <CTableRow v-if="promotionCandidateList.length === 0">
        <CTableDataCell :colspan="canHrWorkManage ? 9 : 8" class="text-center text-muted py-4">
          조회된 승급 심사 대상 내역이 없습니다.
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>

  <Pagination
    v-if="promotionCandidatesCount > 10"
    :active-page="1"
    :limit="8"
    :pages="promotionCandidatePages(10)"
    class="mt-3"
    @active-page-change="pageSelect"
  />
</template>
