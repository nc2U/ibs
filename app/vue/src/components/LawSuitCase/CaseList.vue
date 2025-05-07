<script setup lang="ts">
import type { PropType } from 'vue'
import { useRouter } from 'vue-router'
import { useDocs } from '@/store/pinia/docs'
import type { SuitCase } from '@/store/types/docs'
import { TableSecondary } from '@/utils/cssMixins'
import Pagination from '@/components/Pagination'
import Case from './components/Case.vue'

defineProps({
  company: { type: Number, default: null },
  limit: { type: Number, default: 10 },
  page: { type: Number, required: true },
  caseList: { type: Array as PropType<SuitCase[]>, default: () => [] },
  viewRoute: { type: String, required: true },
  writeAuth: { type: Boolean, default: true },
})

const emit = defineEmits(['page-select', 'agency-filter', 'agency-search', 'related-filter'])

const router = useRouter()

const docStore = useDocs()

const agencyFilter = (court: string) => emit('agency-filter', court)
const agencySearch = (agent: string) => emit('agency-search', agent)
const relatedFilter = (related: number) => emit('related-filter', related)

const casePages = (num: number) => docStore.casePages(num)
const pageSelect = (page: number) => emit('page-select', page)
</script>

<template>
  <CTable hover responsive align="middle">
    <colgroup>
      <col style="width: 10%" />
      <col style="width: 5%" />
      <col style="width: 6%" />
      <col style="width: 7%" />
      <col style="width: 8%" />
      <col style="width: 15%" />
      <col style="width: 13%" />
      <col style="width: 13%" />
      <col style="width: 12%" />
      <col style="width: 11%" />
    </colgroup>

    <CTableHead>
      <CTableRow :color="TableSecondary" class="text-center border-top-1">
        <CTableHeaderCell scope="col">구분</CTableHeaderCell>
        <CTableHeaderCell scope="col">종류</CTableHeaderCell>
        <CTableHeaderCell scope="col">심급</CTableHeaderCell>
        <CTableHeaderCell scope="col">관할법원 / 처리기관</CTableHeaderCell>
        <CTableHeaderCell scope="col">관련사건</CTableHeaderCell>
        <CTableHeaderCell scope="col">사건명</CTableHeaderCell>
        <CTableHeaderCell scope="col">원고 (채권자)</CTableHeaderCell>
        <CTableHeaderCell scope="col">피고 (채무자)</CTableHeaderCell>
        <CTableHeaderCell scope="col">제3채무자</CTableHeaderCell>
        <CTableHeaderCell scope="col">종결일자</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <Case
        v-for="suitcase in caseList"
        :key="suitcase.pk as number"
        :suit-case="suitcase"
        :view-route="viewRoute"
        @agency-filter="agencyFilter"
        @agency-search="agencySearch"
        @related-filter="relatedFilter"
      />
    </CTableBody>
  </CTable>

  <CRow class="flex-lg-row flex-column-reverse">
    <CCol lg="8">
      <Pagination
        :active-page="page"
        :limit="8"
        :pages="casePages(limit)"
        class="mt-3"
        @active-page-change="pageSelect"
      />
    </CCol>
    <CCol lg="4" class="text-right pt-3">
      <v-btn
        v-if="writeAuth"
        color="primary"
        class="px-5"
        :disabled="!company"
        @click="router.push({ name: `${viewRoute} - 작성` })"
      >
        등록하기
      </v-btn>
    </CCol>
  </CRow>
</template>
