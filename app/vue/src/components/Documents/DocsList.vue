<script setup lang="ts">
import type { PropType } from 'vue'
import { useRouter } from 'vue-router'
import { useDocs } from '@/store/pinia/docs'
import { TableSecondary } from '@/utils/cssMixins'
import type { Docs as D } from '@/store/types/docs'
import Pagination from '@/components/Pagination'
import Docs from './components/Docs.vue'
import TopDocs from '@/components/Documents/components/TopDocs.vue'

defineProps({
  company: { type: Number, default: null },
  project: { type: Number, default: null },
  limit: { type: Number, default: 10 },
  page: { type: Number, default: 1 },
  noticeList: { type: Array as PropType<D[]>, default: () => [] },
  docsList: { type: Array as PropType<D[]>, default: () => [] },
  viewRoute: { type: String, required: true },
  isLawsuit: { type: Boolean, default: false },
  writeAuth: { type: Boolean, default: true },
})

const emit = defineEmits(['page-select'])

const router = useRouter()

const docsStore = useDocs()
const docsPages = (num: number) => docsStore.docsPages(num)
const pageSelect = (page: number) => emit('page-select', page)
</script>

<template>
  <CTable hover responsive align="middle">
    <colgroup v-if="isLawsuit">
      <col style="width: 6%" />
      <col style="width: 7%" />
      <col style="width: 9%" />
      <col style="width: 9%" />
      <col style="width: 20%" />
      <col style="width: 25%" />
      <col style="width: 8%" />
      <col style="width: 10%" />
      <col style="width: 6%" />
    </colgroup>
    <colgroup v-else>
      <col style="width: 8%" />
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 30%" />
      <col style="width: 10%" />
      <col style="width: 14%" />
      <col style="width: 8%" />
    </colgroup>

    <CTableHead>
      <CTableRow :color="TableSecondary" class="text-center border-top-1">
        <CTableHeaderCell scope="col">번호</CTableHeaderCell>
        <CTableHeaderCell scope="col">구분</CTableHeaderCell>
        <CTableHeaderCell scope="col">문서 발행일자</CTableHeaderCell>
        <CTableHeaderCell scope="col">문서 범주</CTableHeaderCell>
        <CTableHeaderCell v-if="isLawsuit" scope="col">사건명</CTableHeaderCell>
        <CTableHeaderCell scope="col">문서 제목</CTableHeaderCell>
        <CTableHeaderCell scope="col">등록자</CTableHeaderCell>
        <CTableHeaderCell scope="col">등록일시</CTableHeaderCell>
        <CTableHeaderCell scope="col">조회수</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <TopDocs
        v-for="docs in noticeList"
        :key="docs.pk"
        :docs="docs"
        :view-route="viewRoute"
        :is-lawsuit="isLawsuit"
      />
      <Docs
        v-for="docs in docsList"
        :key="docs.pk"
        :docs="docs"
        :view-route="viewRoute"
        :is-lawsuit="isLawsuit"
      />
    </CTableBody>
  </CTable>

  <CRow class="flex-lg-row flex-column-reverse">
    <CCol lg="8">
      <Pagination
        :active-page="page"
        :limit="8"
        :pages="docsPages(limit)"
        class="mt-3"
        @active-page-change="pageSelect"
      />
    </CCol>
    <CCol lg="4" class="text-right pt-3">
      <v-btn
        v-if="writeAuth"
        color="primary"
        class="px-5"
        :disabled="!company && !project"
        @click="router.push({ name: `${viewRoute} - 작성` })"
      >
        등록하기
      </v-btn>
    </CCol>
  </CRow>
</template>
