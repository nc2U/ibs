<script lang="ts" setup>
import { computed } from 'vue'
import { useSite } from '@/store/pinia/project_site'
import { write_project_site } from '@/utils/pageAuth'
import { type Relation, type SiteOwner as Owner } from '@/store/types/project'
import { TableInfo, TableSuccess, TableSecondary } from '@/utils/cssMixins'
import SiteOwner from '@/views/projects/SiteOwner/components/SiteOwner.vue'
import Pagination from '@/components/Pagination'

import { type PropType } from 'vue'

const props = defineProps({
  isReturned: { type: Boolean },
  limit: { type: Number, default: 10 },
  highlightId: { type: Number, default: null },
  currentPage: { type: Number, default: 1 },
})
const emit = defineEmits(['relation-patch', 'page-select', 'on-delete', 'multi-submit'])

const siteStore = useSite()
const siteOwnerList = computed(() => siteStore.siteOwnerList)
const siteOwnerCount = computed(() => siteStore.siteOwnerCount)

const ownerPages = (num: number) => Math.ceil(siteOwnerCount.value / num)
const pageSelect = (page: number) => emit('page-select', page)
const relationPatch = (payload: Relation) => emit('relation-patch', payload)
const multiSubmit = (payload: Owner) => emit('multi-submit', payload)
const onDelete = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTable hover responsive bordered align="middle">
    <colgroup>
      <col style="width: 6%" />
      <col style="width: 9%" />
      <col style="width: 10%" />
      <col style="width: 12%" />
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 9%" />
      <col style="width: 10%" />
      <col style="width: 6%" />
      <col v-if="write_project_site" style="width: 4%" />
      <col v-if="write_project_site" style="width: 4%" />
    </colgroup>

    <CTableHead :color="TableSecondary">
      <CTableRow class="text-center">
        <CTableHeaderCell colspan="5" :color="TableInfo"> 소유자 관련 정보</CTableHeaderCell>
        <CTableHeaderCell :colspan="write_project_site ? 7 : 5" :color="TableSuccess">
          소유권 관련 정보
        </CTableHeaderCell>
      </CTableRow>
      <CTableRow class="text-center" align="middle">
        <CTableHeaderCell rowspan="2" scope="col">소유구분</CTableHeaderCell>
        <CTableHeaderCell rowspan="2" scope="col">소유자</CTableHeaderCell>
        <CTableHeaderCell rowspan="2" scope="col">생년월일</CTableHeaderCell>
        <CTableHeaderCell rowspan="2" scope="col">주연락처</CTableHeaderCell>
        <CTableHeaderCell rowspan="2" scope="col">소유부지</CTableHeaderCell>
        <CTableHeaderCell rowspan="2" scope="col">소유지분(%)</CTableHeaderCell>
        <CTableHeaderCell colspan="2" scope="col">
          소유면적 <span v-if="isReturned">(환지면적 기준)</span>
        </CTableHeaderCell>
        <CTableHeaderCell rowspan="2" scope="col"> 소유권 취득일</CTableHeaderCell>
        <CTableHeaderCell rowspan="2" scope="col">사용동의</CTableHeaderCell>
        <CTableHeaderCell v-if="write_project_site" rowspan="2" colspan="2" scope="col">
          비고
        </CTableHeaderCell>
      </CTableRow>
      <CTableRow class="text-center">
        <CTableHeaderCell scope="col">m<sup>2</sup></CTableHeaderCell>
        <CTableHeaderCell scope="col">평</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <SiteOwner
        v-for="sOwner in siteOwnerList"
        :key="sOwner.pk as number"
        :owner="sOwner"
        :is-returned="isReturned"
        :is-highlight="props.highlightId === sOwner.pk"
        @relation-patch="relationPatch"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
      />
      <CTableRow v-if="!siteOwnerList.length">
        <CTableDataCell colspan="13" class="text-center p-5 text-danger">
          등록된 데이터가 없습니다.
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>

  <Pagination
    v-if="siteOwnerCount > 10"
    :active-page="props.currentPage"
    :limit="8"
    :pages="ownerPages(limit)"
    class="mt-3"
    @active-page-change="pageSelect"
  />
</template>
