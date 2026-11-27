<script lang="ts" setup>
import { computed } from 'vue'
import { useCompany } from '@/store/pinia/company.ts'
import { TableSecondary } from '@/utils/cssMixins.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { type Grade as GradeType } from '@/store/types/company.ts'
import Pagination from '@/components/Pagination'
import Grade from './Grade.vue'

withDefaults(
  defineProps<{
    activePage?: number
  }>(),
  { activePage: 1 },
)

const emit = defineEmits<{
  (e: 'page-select', page: number): void
  (e: 'multi-submit', payload: GradeType, done?: (ok: boolean) => void): void
  (e: 'on-delete', pk: number, done?: (ok: boolean) => void): void
}>()

const { canGlobal, PERM } = usePerms()
const canHrWorkManage = computed(
  () => canGlobal(PERM.HQ_HR_WORK_CREATE) || canGlobal(PERM.HQ_HR_WORK_UPDATE),
)

const comStore = useCompany()
const gradeList = computed(() => comStore.gradeList)
const gradesCount = computed(() => comStore.gradesCount)

const gradePages = (page: number) => comStore.gradePages(page)
const pageSelect = (page: number) => emit('page-select', page)
const multiSubmit = (payload: GradeType, done?: (ok: boolean) => void) =>
  emit('multi-submit', payload, done)
const onDelete = (pk: number, done?: (ok: boolean) => void) => emit('on-delete', pk, done)
</script>

<template>
  <CTable hover responsive bordered align="middle">
    <colgroup>
      <col style="width: 6%" />
      <col style="width: 10%" />
      <col style="width: 18%" />
      <col style="width: 12%" />
      <col style="width: 24%" />
      <col style="width: 22%" />
      <col v-if="canHrWorkManage" style="width: 8%" />
    </colgroup>

    <CTableHead :color="TableSecondary">
      <CTableRow class="text-center" align="middle">
        <CTableHeaderCell scope="col">No</CTableHeaderCell>
        <CTableHeaderCell scope="col">코드</CTableHeaderCell>
        <CTableHeaderCell scope="col">역할</CTableHeaderCell>
        <CTableHeaderCell scope="col">최소 근속기간(년)</CTableHeaderCell>
        <CTableHeaderCell scope="col">허용직위</CTableHeaderCell>
        <CTableHeaderCell scope="col">승급 기준</CTableHeaderCell>
        <CTableHeaderCell v-if="canHrWorkManage" scope="col">비고</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <CTableRow v-if="gradeList.length === 0" class="text-center">
        <CTableDataCell :colspan="canHrWorkManage ? 7 : 6" class="py-4 text-muted">
          등록된 직급 정보가 없습니다.
        </CTableDataCell>
      </CTableRow>
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
    :active-page="activePage"
    :limit="8"
    :pages="gradePages(10)"
    class="mt-3"
    @active-page-change="pageSelect"
  />
</template>
