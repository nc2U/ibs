<script lang="ts" setup>
import { computed } from 'vue'
import { useSite } from '@/store/pinia/project_site'
import { TableSecondary } from '@/utils/cssMixins'
import { write_project_site } from '@/utils/pageAuth'
import { type SiteContract as siteCont } from '@/store/types/project'
import SiteContract from './SiteContract.vue'
import Pagination from '@/components/Pagination'

import { type PropType } from 'vue'

const props = defineProps({
  limit: { type: Number, default: 10 },
  highlightId: { type: Number, default: null },
  currentPage: { type: Number, default: 1 },
})
const emit = defineEmits(['page-select', 'on-delete', 'multi-submit'])

const siteStore = useSite()
const siteContList = computed(() => siteStore.siteContList)
const siteContCount = computed(() => siteStore.siteContCount)

const siteContPages = (num: number) => Math.ceil(siteContCount.value / num)
const pageSelect = (page: number) => emit('page-select', page)
const multiSubmit = (payload: siteCont) => emit('multi-submit', payload)
const onDelete = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTable hover responsive bordered align="middle">
    <colgroup>
      <col style="width: 7%" />
      <col style="width: 12%" />
      <col style="width: 10%" />
      <col style="width: 8%" />
      <col style="width: 8%" />
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 6%" />
      <col style="width: 10%" />
      <col style="width: 6%" />
      <col style="width: 7%" />
      <col v-if="write_project_site" style="width: 7%" />
    </colgroup>

    <CTableHead :color="TableSecondary">
      <CTableRow class="text-center" align="middle">
        <CTableHeaderCell rowspan="2" scope="col"> 소유<br />구분</CTableHeaderCell>
        <CTableHeaderCell rowspan="2" scope="col">소유자</CTableHeaderCell>
        <CTableHeaderCell rowspan="2" scope="col">계약일</CTableHeaderCell>
        <CTableHeaderCell colspan="2" scope="col"> 총계약 면적</CTableHeaderCell>
        <CTableHeaderCell rowspan="2" scope="col"> 총매매<br />대금</CTableHeaderCell>
        <CTableHeaderCell rowspan="2" scope="col">계약금1</CTableHeaderCell>
        <CTableHeaderCell rowspan="2" scope="col"> 지급<br />여부</CTableHeaderCell>
        <CTableHeaderCell rowspan="2" scope="col">잔금</CTableHeaderCell>
        <CTableHeaderCell rowspan="2" scope="col"> 지급<br />여부</CTableHeaderCell>
        <CTableHeaderCell rowspan="2" scope="col"> 계약서</CTableHeaderCell>
        <CTableHeaderCell v-if="write_project_site" rowspan="2" scope="col">비고</CTableHeaderCell>
      </CTableRow>
      <CTableRow class="text-center">
        <CTableHeaderCell scope="col">m<sup>2</sup></CTableHeaderCell>
        <CTableHeaderCell scope="col">평</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <SiteContract
        v-for="cont in siteContList"
        :key="cont.pk as number"
        :contract="cont"
        :is-highlight="props.highlightId === cont.pk"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
      />
      <CTableRow v-if="!siteContList.length">
        <CTableDataCell colspan="13" class="text-center p-5 text-danger">
          등록된 데이터가 없습니다.
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>

  <Pagination
    v-if="siteContCount > 10"
    :active-page="props.currentPage"
    :limit="8"
    :pages="siteContPages(limit)"
    class="mt-3"
    @active-page-change="pageSelect"
  />
</template>
