<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import type { OfficialLetter } from '@/store/types/docs'
import type { LetterFilter } from '@/store/pinia/docs'
import Pagination from '@/components/Pagination'
import DatePicker from '@/components/DatePicker/DatePicker.vue'

const props = defineProps<{
  company: number
  letterList: OfficialLetter[]
  letterCount: number
  letterFilter: LetterFilter
  viewRoute: string
  writeAuth: boolean
}>()

const emit = defineEmits<{
  listFilter: [payload: LetterFilter]
  pageSelect: [page: number]
}>()

const router = useRouter()

const search = ref('')
const dateFrom = ref('')
const dateTo = ref('')
const ordering = ref('-created')

const limit = computed(() => props.letterFilter.limit || 10)
const pages = computed(() => Math.ceil(props.letterCount / (limit.value as number)))

watch(
  () => props.letterFilter,
  filter => {
    search.value = filter.search || ''
    dateFrom.value = filter.issue_date_from || ''
    dateTo.value = filter.issue_date_to || ''
    ordering.value = filter.ordering || '-created'
  },
  { immediate: true },
)

const onFilter = () => {
  emit('listFilter', {
    search: search.value,
    issue_date_from: dateFrom.value,
    issue_date_to: dateTo.value,
    ordering: ordering.value,
    page: 1,
  })
}

const resetFilter = () => {
  search.value = ''
  dateFrom.value = ''
  dateTo.value = ''
  ordering.value = '-created'
  emit('listFilter', {
    search: '',
    issue_date_from: '',
    issue_date_to: '',
    ordering: '-created',
    page: 1,
  })
}

const goToCreate = () => {
  router.push({ name: `${props.viewRoute} - 작성` })
}

const goToView = (pk: number) => {
  router.push({ name: `${props.viewRoute} - 보기`, params: { letterId: pk } })
}

const formatDate = (dateStr: string | undefined) => {
  if (!dateStr) return '-'
  return dateStr.substring(0, 10)
}
</script>

<template>
  <div>
    <!-- Filter Section -->
    <CRow class="mb-3">
      <CCol md="3">
        <CFormLabel>발신일 (시작)</CFormLabel>
        <DatePicker v-model="dateFrom" placeholder="시작일" @update:model-value="onFilter" />
      </CCol>
      <CCol md="3">
        <CFormLabel>발신일 (종료)</CFormLabel>
        <DatePicker v-model="dateTo" placeholder="종료일" @update:model-value="onFilter" />
      </CCol>
      <CCol md="3">
        <CFormLabel>정렬</CFormLabel>
        <CFormSelect v-model="ordering" @change="onFilter">
          <option value="-created">최신순</option>
          <option value="created">오래된순</option>
          <option value="-issue_date">발신일 최신순</option>
          <option value="issue_date">발신일 오래된순</option>
          <option value="document_number">문서번호순</option>
        </CFormSelect>
      </CCol>
      <CCol md="3">
        <CFormLabel>검색</CFormLabel>
        <CInputGroup>
          <CFormInput
            v-model="search"
            placeholder="문서번호, 제목, 수신처..."
            @keyup.enter="onFilter"
          />
          <CButton color="primary" @click="onFilter">
            <CIcon name="cilSearch" />
          </CButton>
          <CButton color="secondary" @click="resetFilter">
            <CIcon name="cilReload" />
          </CButton>
        </CInputGroup>
      </CCol>
    </CRow>

    <!-- Action Bar -->
    <CRow class="mb-3">
      <CCol class="d-flex justify-content-between align-items-center">
        <span class="text-muted">총 {{ letterCount }}건</span>
        <CButton v-if="writeAuth" color="primary" @click="goToCreate">
          <CIcon name="cilPlus" class="me-1" />
          공문 작성
        </CButton>
      </CCol>
    </CRow>

    <!-- List Table -->
    <CTable hover responsive bordered>
      <CTableHead color="light">
        <CTableRow>
          <CTableHeaderCell class="text-center" style="width: 120px">문서번호</CTableHeaderCell>
          <CTableHeaderCell>제목</CTableHeaderCell>
          <CTableHeaderCell class="text-center" style="width: 150px">수신처</CTableHeaderCell>
          <CTableHeaderCell class="text-center" style="width: 110px">발신일</CTableHeaderCell>
          <CTableHeaderCell class="text-center" style="width: 100px">작성자</CTableHeaderCell>
          <CTableHeaderCell class="text-center" style="width: 80px">PDF</CTableHeaderCell>
        </CTableRow>
      </CTableHead>
      <CTableBody>
        <CTableRow
          v-for="letter in letterList"
          :key="letter.pk"
          style="cursor: pointer"
          @click="goToView(letter.pk as number)"
        >
          <CTableDataCell class="text-center">
            <span class="text-primary fw-semibold">{{ letter.document_number }}</span>
          </CTableDataCell>
          <CTableDataCell>{{ letter.title }}</CTableDataCell>
          <CTableDataCell class="text-center">{{ letter.recipient_name }}</CTableDataCell>
          <CTableDataCell class="text-center">{{ formatDate(letter.issue_date) }}</CTableDataCell>
          <CTableDataCell class="text-center">{{ letter.creator?.username || '-' }}</CTableDataCell>
          <CTableDataCell class="text-center">
            <CBadge v-if="letter.pdf_file" color="success">
              <CIcon name="cilFile" />
            </CBadge>
            <CBadge v-else color="secondary">-</CBadge>
          </CTableDataCell>
        </CTableRow>
        <CTableRow v-if="letterList.length === 0">
          <CTableDataCell colspan="6" class="text-center text-muted py-5">
            등록된 공문이 없습니다.
          </CTableDataCell>
        </CTableRow>
      </CTableBody>
    </CTable>

    <!-- Pagination -->
    <Pagination
      v-if="pages > 1"
      :active-page="letterFilter.page || 1"
      :pages="pages"
      class="mt-3"
      @active-page-change="(p: number) => emit('pageSelect', p)"
    />
  </div>
</template>
