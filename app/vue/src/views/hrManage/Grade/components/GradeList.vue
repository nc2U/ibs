<script lang="ts" setup>
import { computed } from 'vue'
import { useCompany } from '@/store/pinia/company'
import { TableSecondary } from '@/utils/cssMixins'
import { useAccount } from '@/store/pinia/account.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { type Grade as GradeType } from '@/store/types/company'
import Pagination from '@/components/Pagination'
import Grade from './Grade.vue'

const emit = defineEmits(['page-select', 'multi-submit', 'on-delete'])

const { can, PERM } = usePerms()
const accStore = useAccount()
const canHrWorkManage = computed(
  () => accStore.isStaff && (can(PERM.HR_WORK_CREATE) || can(PERM.HR_WORK_UPDATE)),
)

const comStore = useCompany()
const gradeList = computed(() => comStore.gradeList)
const gradesCount = computed(() => comStore.gradesCount)

const gradePages = (page: number) => comStore.gradePages(page)
const pageSelect = (page: number) => emit('page-select', page)
const multiSubmit = (payload: GradeType) => emit('multi-submit', payload)
const onDelete = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTable hover responsive bordered align="middle">
    <colgroup>
      <col style="width: 8%" />
      <col style="width: 12%" />
      <col style="width: 10%" />
      <col style="width: 30%" />
      <col style="width: 30%" />
      <col v-if="canHrWorkManage" style="width: 10%" />
    </colgroup>

    <CTableHead :color="TableSecondary">
      <CTableRow class="text-center" align="middle">
        <CTableHeaderCell scope="col">No</CTableHeaderCell>
        <CTableHeaderCell scope="col">직급명</CTableHeaderCell>
        <CTableHeaderCell scope="col">승급표준년수</CTableHeaderCell>
        <CTableHeaderCell scope="col">허용직위</CTableHeaderCell>
        <CTableHeaderCell scope="col">신입부여 기준</CTableHeaderCell>
        <CTableHeaderCell v-if="canHrWorkManage" scope="col">비고</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <Grade
        v-for="grade in gradeList"
        :key="grade.pk"
        :grade="grade"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
      />
    </CTableBody>
  </CTable>

  <Pagination
    v-if="gradesCount > 10"
    :active-page="1"
    :limit="8"
    :pages="gradePages(10)"
    class="mt-3"
    @active-page-change="pageSelect"
  />
</template>
