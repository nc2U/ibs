<script lang="ts" setup>
import { computed } from 'vue'
import { useSite } from '@/store/pinia/project_site'
import { TableSecondary } from '@/utils/cssMixins'
import { write_project_site } from '@/utils/pageAuth'
import { type Site as S } from '@/store/types/project'
import Site from '@/views/projects/SiteList/components/Site.vue'
import Pagination from '@/components/Pagination'

const props = defineProps({
  isReturned: { type: Boolean },
  limit: { type: Number, default: 10 },
  highlightId: { type: Number, default: null },
  currentPage: { type: Number, default: 1 },
})
const emit = defineEmits(['page-select', 'on-delete', 'multi-submit'])

const siteStore = useSite()
// const siteList = computed<S[]>(() => siteStore.getSiteList)
const siteList = computed<S[]>(() => siteStore.siteList)
const siteCount = computed(() => siteStore.siteCount)

const sitePages = (num: number) => Math.ceil(siteCount.value / num)
const pageSelect = (page: number) => emit('page-select', page)
const multiSubmit = (payload: S) => emit('multi-submit', payload)
const onDelete = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTable hover responsive bordered align="middle">
    <colgroup>
      <col style="width: 5%" />
      <col style="width: 6%" />
      <col style="width: 7%" />
      <col style="width: 5%" />
      <col style="width: 8%" />
      <col style="width: 8%" />
      <col v-if="isReturned" style="width: 7%" />
      <col v-if="isReturned" style="width: 7%" />
      <col style="width: 30%" />
      <col style="width: 5%" />
      <col style="width: 7%" />
      <col v-if="write_project_site" style="width: 6%" />
    </colgroup>

    <CTableHead :color="TableSecondary">
      <CTableRow class="text-center" align="middle">
        <CTableHeaderCell rowspan="2" scope="col">No</CTableHeaderCell>
        <CTableHeaderCell rowspan="2" scope="col">행정동</CTableHeaderCell>
        <CTableHeaderCell rowspan="2" scope="col">지번</CTableHeaderCell>
        <CTableHeaderCell rowspan="2" scope="col">지목</CTableHeaderCell>
        <CTableHeaderCell colspan="2" scope="col">공부상 면적</CTableHeaderCell>
        <CTableHeaderCell v-if="isReturned" colspan="2" scope="col"> 환지 면적</CTableHeaderCell>
        <CTableHeaderCell rowspan="2" scope="col">소유자 목록</CTableHeaderCell>
        <CTableHeaderCell rowspan="2" scope="col">등기부 등본</CTableHeaderCell>
        <CTableHeaderCell rowspan="2" scope="col">등본 발급일</CTableHeaderCell>
        <CTableHeaderCell v-if="write_project_site" rowspan="2" scope="col">비고</CTableHeaderCell>
      </CTableRow>
      <CTableRow class="text-center">
        <CTableHeaderCell scope="col">m<sup>2</sup></CTableHeaderCell>
        <CTableHeaderCell scope="col">평</CTableHeaderCell>
        <CTableHeaderCell v-if="isReturned" scope="col"> m<sup>2</sup></CTableHeaderCell>
        <CTableHeaderCell v-if="isReturned" scope="col">평</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <Site
        v-for="site in siteList"
        :key="site.pk as number"
        :site="site"
        :is-returned="props.isReturned"
        :is-highlight="props.highlightId === site.pk"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
      />
      <CTableRow v-if="!siteList.length">
        <CTableDataCell colspan="13" class="text-center p-5 text-danger">
          등록된 데이터가 없습니다.
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>

  <Pagination
    v-if="siteCount > 10"
    :active-page="props.currentPage"
    :limit="8"
    :pages="sitePages(limit)"
    class="mt-3"
    @active-page-change="pageSelect"
  />
</template>
