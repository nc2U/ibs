<script setup lang="ts">
import type { PropType } from 'vue'
import { useDocs } from '@/store/pinia/docs'
import { useAccount } from '@/store/pinia/account'
import { cutString, numFormat, timeFormat } from '@/utils/baseMixins'
import { TableSecondary } from '@/utils/cssMixins'
import type { TrashDocs } from '@/store/types/docs'
import Pagination from '@/components/Pagination'
import NoData from '@/components/NoData/Index.vue'

defineProps({
  trashDocsList: { type: Array as PropType<TrashDocs[]>, default: () => [] },
  trashDocsCount: { type: Number, default: 0 },
  viewRoute: { type: String, required: true },
  page: { type: Number, default: 1 },
})

const emit = defineEmits(['page-select', 'restore-docs', 'delete-docs'])

const docStore = useDocs()
const accStore = useAccount()

const trashDocsPages = (perPage: number) => docStore.trashDocsPages(perPage)
const pageSelect = (p: number) => emit('page-select', p)

const canManageItem = (doc: TrashDocs) =>
  !!accStore.superAuth ||
  !!accStore.workManager ||
  (!!doc.creator && doc.creator === accStore.userInfo?.username)
</script>

<template>
  <div class="d-flex justify-content-between align-items-center mb-3">
    <h6 class="mb-0 fw-bold">삭제된 문서 : 총 {{ numFormat(trashDocsCount) }}건</h6>
  </div>

  <CTable v-if="trashDocsList.length > 0" hover responsive align="middle">
    <colgroup>
      <col style="width: 6%" />
      <col style="width: 18%" />
      <col style="width: 12%" />
      <col style="width: 30%" />
      <col style="width: 18%" />
      <col style="width: 8%" />
      <col style="width: 8%" />
    </colgroup>

    <CTableHead>
      <CTableRow :color="TableSecondary" class="text-center border-top">
        <CTableHeaderCell scope="col">번호</CTableHeaderCell>
        <CTableHeaderCell scope="col">소속 · 분류</CTableHeaderCell>
        <CTableHeaderCell scope="col">구분</CTableHeaderCell>
        <CTableHeaderCell scope="col">제목</CTableHeaderCell>
        <CTableHeaderCell scope="col">삭제일시</CTableHeaderCell>
        <CTableHeaderCell scope="col">복원</CTableHeaderCell>
        <CTableHeaderCell scope="col">완전 삭제</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <CTableRow v-for="doc in trashDocsList" :key="doc.pk" class="text-center">
        <CTableDataCell>{{ doc.pk }}</CTableDataCell>
        <CTableDataCell class="text-start">
          {{ doc.project_name || '-' }}
          <span v-if="doc.cate_name" class="text-medium-emphasis"> · {{ doc.cate_name }}</span>
        </CTableDataCell>
        <CTableDataCell>{{ doc.type_name }}</CTableDataCell>
        <CTableDataCell class="text-start">
          <router-link :to="{ name: `${viewRoute} - 보기`, params: { docsId: doc.pk } }">
            {{ cutString(doc.title, 50) }}
          </router-link>
        </CTableDataCell>
        <CTableDataCell class="text-medium-emphasis">
          {{ timeFormat(doc.deleted ?? '') }}
        </CTableDataCell>
        <CTableDataCell>
          <v-btn
            v-if="canManageItem(doc)"
            density="compact"
            icon="mdi-delete-restore"
            size="small"
            variant="text"
            color="success"
            @click="emit('restore-docs', doc.pk)"
          />
          <span v-else class="text-medium-emphasis">-</span>
        </CTableDataCell>
        <CTableDataCell>
          <v-btn
            v-if="canManageItem(doc)"
            density="compact"
            icon="mdi-delete-forever-outline"
            size="small"
            variant="text"
            color="error"
            @click="emit('delete-docs', doc.pk)"
          />
          <span v-else class="text-medium-emphasis">-</span>
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>

  <NoData v-else />

  <CRow v-if="trashDocsPages(10) > 1" class="mt-3">
    <CCol>
      <Pagination
        :active-page="page"
        :limit="8"
        :pages="trashDocsPages(10)"
        @active-page-change="pageSelect"
      />
    </CCol>
  </CRow>
</template>
