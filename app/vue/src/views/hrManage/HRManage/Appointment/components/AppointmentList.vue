<script lang="ts" setup>
import { computed } from 'vue'
import { usePerms } from '@/composables/usePerms.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { TableSecondary } from '@/utils/cssMixins.ts'
import { type PersonnelOrder as PersonnelOrderType } from '@/store/types/company.ts'
import Pagination from '@/components/Pagination'
import Appointment from './Appointment.vue'

withDefaults(
  defineProps<{
    activePage?: number
  }>(),
  { activePage: 1 },
)

const emit = defineEmits<{
  (e: 'page-select', page: number): void
  (e: 'multi-submit', payload: PersonnelOrderType, done?: (ok: boolean) => void): void
  (e: 'on-delete', pk: number, done?: (ok: boolean) => void): void
}>()

const { canGlobal, PERM } = usePerms()
const canHrWorkManage = computed(
  () => canGlobal(PERM.HQ_HR_WORK_CREATE) || canGlobal(PERM.HQ_HR_WORK_UPDATE),
)

const companyStore = useCompany()
const personnelOrderList = computed(() => companyStore.personnelOrderList)
const personnelOrdersCount = computed(() => companyStore.personnelOrdersCount)

const personnelOrderPages = (page: number) => companyStore.personnelOrderPages(page)
const pageSelect = (page: number) => emit('page-select', page)
const multiSubmit = (payload: PersonnelOrderType, done?: (ok: boolean) => void) =>
  emit('multi-submit', payload, done)
const onDelete = (pk: number, done?: (ok: boolean) => void) => emit('on-delete', pk, done)
</script>

<template>
  <CTable hover responsive bordered align="middle">
    <colgroup>
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 11%" />
      <col style="width: 10%" />
      <col style="width: 18%" />
      <col style="width: 18%" />
      <col style="width: 16%" />
      <col v-if="canHrWorkManage" style="width: 7%" />
    </colgroup>

    <CTableHead :color="TableSecondary">
      <CTableRow class="text-center" align="middle">
        <CTableHeaderCell scope="col">발령일자</CTableHeaderCell>
        <CTableHeaderCell scope="col">발령구분</CTableHeaderCell>
        <CTableHeaderCell scope="col">문서번호</CTableHeaderCell>
        <CTableHeaderCell scope="col">대상직원</CTableHeaderCell>
        <CTableHeaderCell scope="col">발령 전 상태</CTableHeaderCell>
        <CTableHeaderCell scope="col">발령 후 상태</CTableHeaderCell>
        <CTableHeaderCell scope="col">발령 사유/내용</CTableHeaderCell>
        <CTableHeaderCell v-if="canHrWorkManage" scope="col">관리</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <CTableRow v-if="personnelOrderList.length === 0" class="text-center">
        <CTableDataCell :colspan="canHrWorkManage ? 8 : 7" class="py-4 text-muted">
          조회된 인사 발령 내역이 없습니다.
        </CTableDataCell>
      </CTableRow>
      <Appointment
        v-for="order in personnelOrderList"
        :key="order.pk"
        :order="order"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
      />
    </CTableBody>
  </CTable>

  <Pagination
    v-if="personnelOrdersCount > 10"
    :active-page="activePage"
    :limit="8"
    :pages="personnelOrderPages(10)"
    class="mt-3"
    @active-page-change="pageSelect"
  />
</template>
