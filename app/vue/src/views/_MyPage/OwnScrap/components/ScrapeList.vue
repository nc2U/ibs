<script setup lang="ts">
import type { PropType } from 'vue'
import { numFormat } from '@/utils/baseMixins'
import { TableSecondary } from '@/utils/cssMixins'
import { useAccount } from '@/store/pinia/account'
import type { Scrape as S } from '@/store/types/accounts'
import Scrape from './Scrape.vue'
import Pagination from '@/components/Pagination'

defineProps({
  scrapeList: { type: Array as PropType<S[]>, default: () => [] },
  scrapeCount: { type: Number, default: 0 },
  viewRoute: { type: String, required: true },
  page: { type: Number, default: 1 },
})

const emit = defineEmits(['page-select', 'patch-title', 'del-scrape'])

const accStore = useAccount()
const scrapePages = (pages: number) => accStore.scrapePages(pages)
const pageSelect = (page: number) => emit('page-select', page)

const patchTitle = (pk: number, title: string) => emit('patch-title', pk, title)
const delScrape = (pk: number) => emit('del-scrape', pk)
</script>

<template>
  <h5>스크랩 : 총 {{ numFormat(scrapeCount) }}건</h5>

  <v-divider />

  <CTable hover responsive align="middle">
    <colgroup>
      <col style="width: 5%" />
      <col style="width: 20%" />
      <col style="width: 35%" />
      <col style="width: 20%" />
      <col style="width: 10%" />
      <col style="width: 10%" />
    </colgroup>

    <CTableHead>
      <CTableRow :color="TableSecondary" class="text-center border-top-1">
        <CTableHeaderCell scope="col">번호</CTableHeaderCell>
        <CTableHeaderCell scope="col">게시판</CTableHeaderCell>
        <CTableHeaderCell scope="col">제목</CTableHeaderCell>
        <CTableHeaderCell scope="col">보관일시</CTableHeaderCell>
        <CTableHeaderCell scope="col">제목수정</CTableHeaderCell>
        <CTableHeaderCell scope="col">보관취소</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <Scrape
        v-for="scrape in scrapeList"
        :key="scrape.pk"
        :scrape="scrape"
        :view-route="viewRoute"
        @patch-title="patchTitle"
        @del-scrape="delScrape"
      />
    </CTableBody>
  </CTable>

  <CRow class="flex-lg-row flex-column-reverse">
    <CCol lg="8">
      <Pagination
        :active-page="page"
        :limit="8"
        :pages="scrapePages(10)"
        class="mt-3"
        @active-page-change="pageSelect"
      />
    </CCol>
  </CRow>
</template>
