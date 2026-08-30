<script lang="ts" setup>
import { computed } from 'vue'
import { useCompany } from '@/store/pinia/company.ts'
import { TableSecondary } from '@/utils/cssMixins.ts'
import { useAccount } from '@/store/pinia/account.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { type Position as PositionType } from '@/store/types/company.ts'
import Pagination from '@/components/Pagination'
import Position from './Position.vue'

const emit = defineEmits(['page-select', 'multi-submit', 'on-delete'])

const { can, PERM } = usePerms()
const accStore = useAccount()
const canHrWorkManage = computed(
  () => accStore.isStaff && (can(PERM.HQ_HR_WORK_CREATE) || can(PERM.HQ_HR_WORK_UPDATE)),
)

const companyStore = useCompany()
const positionList = computed(() => companyStore.positionList)
const positionsCount = computed(() => companyStore.positionsCount)

const positionPages = (page: number) => companyStore.positionPages(page)
const pageSelect = (page: number) => emit('page-select', page)
const multiSubmit = (payload: PositionType) => emit('multi-submit', payload)
const onDelete = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTable hover responsive bordered align="middle">
    <colgroup>
      <col style="width: 8%" />
      <col style="width: 12%" />
      <col style="width: 30%" />
      <col style="width: 40%" />
      <col v-if="canHrWorkManage" style="width: 10%" />
    </colgroup>

    <CTableHead :color="TableSecondary">
      <CTableRow class="text-center" align="middle">
        <CTableHeaderCell scope="col">No</CTableHeaderCell>
        <CTableHeaderCell scope="col">직위명</CTableHeaderCell>
        <CTableHeaderCell scope="col">직급</CTableHeaderCell>
        <CTableHeaderCell scope="col">설명</CTableHeaderCell>
        <CTableHeaderCell v-if="canHrWorkManage" scope="col">비고</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <Position
        v-for="position in positionList"
        :key="position.pk"
        :position="position"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
      />
    </CTableBody>
  </CTable>

  <Pagination
    v-if="positionsCount > 10"
    :active-page="1"
    :limit="8"
    :pages="positionPages(10)"
    class="mt-3"
    @active-page-change="pageSelect"
  />
</template>
