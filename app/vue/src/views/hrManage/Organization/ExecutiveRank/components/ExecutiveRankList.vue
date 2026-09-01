<script lang="ts" setup>
import { computed } from 'vue'
import { useCompany } from '@/store/pinia/company.ts'
import { TableSecondary } from '@/utils/cssMixins.ts'
import { useAccount } from '@/store/pinia/account.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { type ExecutiveRank as ExecutiveRankType } from '@/store/types/company.ts'
import Pagination from '@/components/Pagination'
import ExecutiveRank from './ExecutiveRank.vue'

const emit = defineEmits(['page-select', 'multi-submit', 'on-delete'])

const { can, PERM } = usePerms()
const accStore = useAccount()
const canHrWorkManage = computed(
  () => accStore.isStaff && (can(PERM.HQ_HR_WORK_CREATE) || can(PERM.HQ_HR_WORK_UPDATE)),
)

const companyStore = useCompany()
const executiveRankList = computed(() => companyStore.executiveRankList)
const executiveRanksCount = computed(() => companyStore.executiveRanksCount)

const executiveRankPages = (page: number) => companyStore.executiveRankPages(page)
const pageSelect = (page: number) => emit('page-select', page)
const multiSubmit = (payload: ExecutiveRankType) => emit('multi-submit', payload)
const onDelete = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTable hover responsive bordered align="middle">
    <colgroup>
      <col style="width: 8%" />
      <col style="width: 15%" />
      <col style="width: 20%" />
      <col style="width: 50%" />
      <col v-if="canHrWorkManage" style="width: 7%" />
    </colgroup>

    <CTableHead :color="TableSecondary">
      <CTableRow class="text-center" align="middle">
        <CTableHeaderCell scope="col">서열</CTableHeaderCell>
        <CTableHeaderCell scope="col">코드</CTableHeaderCell>
        <CTableHeaderCell scope="col">임원 직위명</CTableHeaderCell>
        <CTableHeaderCell scope="col">역할/관장 설명</CTableHeaderCell>
        <CTableHeaderCell v-if="canHrWorkManage" scope="col">비고</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <ExecutiveRank
        v-for="executiveRank in executiveRankList"
        :key="executiveRank.pk"
        :executive-rank="executiveRank"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
      />
    </CTableBody>
  </CTable>

  <Pagination
    v-if="executiveRanksCount > 10"
    :active-page="1"
    :limit="8"
    :pages="executiveRankPages(10)"
    class="mt-3"
    @active-page-change="pageSelect"
  />
</template>
