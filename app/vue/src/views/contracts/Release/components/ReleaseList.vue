<script lang="ts" setup>
import { computed } from 'vue'
import { TableSecondary } from '@/utils/cssMixins'
import { useContract } from '@/store/pinia/contract'
import Pagination from '@/components/Pagination'
import Release from '@/views/contracts/Release/components/Release.vue'

const props = defineProps<{
  highlightId?: number | null
  currentPage?: number
}>()

const emit = defineEmits(['page-select', 'call-form'])

const contractStore = useContract()
const contReleaseList = computed(() => contractStore.contReleaseList)
const releasePages = computed(() => contractStore.releasePages)

const pageSelect = (page: number) => emit('page-select', page)
const callForm = (contractor: number) => emit('call-form', contractor)
</script>

<template>
  <CTable hover responsive align="middle">
    <colgroup>
      <col style="width: 25%" />
      <col style="width: 10%" />
      <col style="width: 12%" />
      <col style="width: 10%" />
      <col style="width: 12%" />
      <col style="width: 9%" />
      <col style="width: 9%" />
      <col style="width: 9%" />
      <col style="width: 5%" />
    </colgroup>

    <CTableHead :color="TableSecondary" class="text-center">
      <CTableRow>
        <CTableHeaderCell>계약 해지자</CTableHeaderCell>
        <CTableHeaderCell>현재상태</CTableHeaderCell>
        <CTableHeaderCell>환불(예정)금액</CTableHeaderCell>
        <CTableHeaderCell>(환불)은행명</CTableHeaderCell>
        <CTableHeaderCell>(환불)계좌번호</CTableHeaderCell>
        <CTableHeaderCell>(환불)예금주</CTableHeaderCell>
        <CTableHeaderCell>해지신청일</CTableHeaderCell>
        <CTableHeaderCell>환불처리일</CTableHeaderCell>
        <CTableHeaderCell>비고</CTableHeaderCell>
      </CTableRow>
    </CTableHead>
    <CTableBody>
      <CTableRow
        v-for="release in contReleaseList"
        :key="release.pk"
        :color="highlightId === release.pk ? 'warning' : ''"
        :data-release-id="release.pk"
      >
        <Release
          :release="release"
          :highlight-id="highlightId || undefined"
          @call-form="callForm"
        />
      </CTableRow>
    </CTableBody>
  </CTable>

  <Pagination
    :active-page="props.currentPage || 1"
    :limit="8"
    :pages="releasePages(10)"
    class="mt-3"
    @active-page-change="pageSelect"
  />
</template>
