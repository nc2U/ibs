<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { usePerms } from '@/composables/usePerms.ts'
import { useAccount } from '@/store/pinia/account.ts'
import type { InboundLetter } from '@/store/types/docs'
import type { InboundLetterFilter } from '@/store/pinia/docs'
import Pagination from '@/components/Pagination'
import DatePicker from '@/components/DatePicker/DatePicker.vue'

const props = defineProps<{
  company: number
  letterList: InboundLetter[]
  letterCount: number
  letterFilter: InboundLetterFilter
  viewRoute: string
  departments: { value: number; label: string }[]
}>()

const emit = defineEmits<{
  listFilter: [payload: InboundLetterFilter]
  pageSelect: [page: number]
}>()

const { can, PERM } = usePerms()
const accStore = useAccount()
const canDocsCreate = computed(() => accStore.isStaff && can(PERM.DOCS_CREATE))

const router = useRouter()

const search = ref('')
const dateFrom = ref('')
const dateTo = ref('')
const status = ref('')
const dept = ref<number | ''>('')
const ordering = ref('-received_date')

const limit = computed(() => props.letterFilter.limit || 10)
const pages = computed(() => Math.ceil(props.letterCount / (limit.value as number)))

watch(
  () => props.letterFilter,
  filter => {
    search.value = filter.search || ''
    dateFrom.value = filter.received_date_from || ''
    dateTo.value = filter.received_date_to || ''
    status.value = filter.status || ''
    dept.value = filter.recipient_dept || ''
    ordering.value = filter.ordering || '-received_date'
  },
  { immediate: true },
)

const onFilter = () => {
  emit('listFilter', {
    search: search.value,
    received_date_from: dateFrom.value,
    received_date_to: dateTo.value,
    status: status.value as any,
    recipient_dept: dept.value,
    ordering: ordering.value,
    page: 1,
  })
}

const resetFilter = () => {
  search.value = ''
  dateFrom.value = ''
  dateTo.value = ''
  status.value = ''
  dept.value = ''
  ordering.value = '-received_date'
  emit('listFilter', {
    search: '',
    received_date_from: '',
    received_date_to: '',
    status: '',
    recipient_dept: '',
    ordering: '-received_date',
    page: 1,
  })
}

const goToCreate = () => {
  router.push({ name: `${props.viewRoute} - 작성` })
}

const goToView = (pk: number) => {
  router.push({ name: `${props.viewRoute} - 보기`, params: { letterId: pk } })
}

const formatDate = (dateStr: string | undefined | null) => {
  if (!dateStr) return '-'
  return dateStr.substring(0, 10)
}

const getDDayBadgeColor = (dDay: number | null | undefined) => {
  if (dDay === null || dDay === undefined) return 'secondary'
  if (dDay < 0) return 'danger'
  if (dDay === 0) return 'warning'
  if (dDay <= 3) return 'danger'
  if (dDay <= 7) return 'warning'
  return 'info'
}

const getDDayText = (dDay: number | null | undefined) => {
  if (dDay === null || dDay === undefined) return ''
  if (dDay < 0) return `D+${Math.abs(dDay)}`
  if (dDay === 0) return 'D-Day'
  return `D-${dDay}`
}
</script>

<template>
  <div>
    <!-- Filter Section -->
    <CRow class="mb-3">
      <CCol md="2">
        <CFormLabel>접수일 (시작)</CFormLabel>
        <DatePicker v-model="dateFrom" placeholder="시작일" @update:model-value="onFilter" />
      </CCol>
      <CCol md="2">
        <CFormLabel>접수일 (종료)</CFormLabel>
        <DatePicker v-model="dateTo" placeholder="종료일" @update:model-value="onFilter" />
      </CCol>
      <CCol md="2">
        <CFormLabel>처리 상태</CFormLabel>
        <CFormSelect v-model="status" @change="onFilter">
          <option value="">전체 상태</option>
          <option value="received">접수</option>
          <option value="in_progress">처리중</option>
          <option value="replied">회신완료</option>
          <option value="closed">종결</option>
        </CFormSelect>
      </CCol>
      <CCol md="2">
        <CFormLabel>배부 부서</CFormLabel>
        <CFormSelect v-model="dept" @change="onFilter">
          <option value="">전체 부서</option>
          <option v-for="d in departments" :key="d.value" :value="d.value">
            {{ d.label }}
          </option>
        </CFormSelect>
      </CCol>
      <CCol md="2">
        <CFormLabel>정렬</CFormLabel>
        <CFormSelect v-model="ordering" @change="onFilter">
          <option value="-received_date">접수일 최신순</option>
          <option value="received_date">접수일 오래된순</option>
          <option value="reply_due_date">회신기한 임박순</option>
          <option value="-created">등록일시 최신순</option>
          <option value="receipt_number">접수번호순</option>
        </CFormSelect>
      </CCol>
      <CCol md="2">
        <CFormLabel>검색</CFormLabel>
        <CInputGroup>
          <CFormInput
            v-model="search"
            placeholder="접수번호, 발신처, 제목..."
            @keyup.enter="onFilter"
          />
          <v-btn color="light" @click="onFilter" flat>
            <v-icon icon="mdi-magnify" size="small" />
          </v-btn>
          <v-btn color="light" @click="resetFilter" flat>
            <v-icon icon="mdi-refresh" size="small" />
          </v-btn>
        </CInputGroup>
      </CCol>
    </CRow>

    <!-- Action Bar -->
    <CRow class="mb-3">
      <CCol class="d-flex justify-content-between align-items-center">
        <div class="d-flex align-items-center gap-2">
          <span class="text-muted">총 {{ letterCount }}건</span>
        </div>
        <v-btn v-if="canDocsCreate" color="primary" @click="goToCreate">
          <v-icon icon="mdi-plus" size="small" class="me-1" />
          수신 공문 접수
        </v-btn>
      </CCol>
    </CRow>

    <!-- List Table -->
    <CTable hover responsive bordered>
      <CTableHead color="light">
        <CTableRow>
          <CTableHeaderCell class="text-center" style="width: 130px">접수번호</CTableHeaderCell>
          <CTableHeaderCell class="text-center" style="width: 140px"
            >발신처 문서번호</CTableHeaderCell
          >
          <CTableHeaderCell class="text-center" style="width: 140px">발신처</CTableHeaderCell>
          <CTableHeaderCell>제목</CTableHeaderCell>
          <CTableHeaderCell class="text-center" style="width: 105px">접수일자</CTableHeaderCell>
          <CTableHeaderCell class="text-center" style="width: 130px"
            >회신기한 (D-Day)</CTableHeaderCell
          >
          <CTableHeaderCell class="text-center" style="width: 110px">배부 부서</CTableHeaderCell>
          <CTableHeaderCell class="text-center" style="width: 90px">담당자</CTableHeaderCell>
          <CTableHeaderCell class="text-center" style="width: 85px">상태</CTableHeaderCell>
          <CTableHeaderCell class="text-center" style="width: 60px">스캔</CTableHeaderCell>
        </CTableRow>
      </CTableHead>
      <CTableBody>
        <CTableRow
          v-for="item in letterList"
          :key="item.pk"
          style="cursor: pointer"
          @click="goToView(item.pk as number)"
        >
          <CTableDataCell class="text-center">
            <span class="text-primary fw-semibold">{{ item.receipt_number }}</span>
          </CTableDataCell>
          <CTableDataCell class="text-center">
            <small class="text-muted">{{ item.document_number }}</small>
          </CTableDataCell>
          <CTableDataCell class="text-center">
            <span class="fw-semibold">{{ item.sender_name }}</span>
          </CTableDataCell>
          <CTableDataCell>
            {{ item.title }}
            <v-icon
              v-if="item.has_attachments"
              icon="mdi-paperclip"
              size="small"
              class="text-muted ms-1"
              title="첨부파일 있음"
            />
          </CTableDataCell>
          <CTableDataCell class="text-center">
            {{ formatDate(item.received_date) }}
          </CTableDataCell>
          <CTableDataCell class="text-center">
            <template v-if="item.reply_due_date">
              <div>{{ formatDate(item.reply_due_date) }}</div>
              <CBadge
                v-if="item.status !== 'closed' && item.status !== 'replied'"
                :color="getDDayBadgeColor(item.d_day)"
                class="mt-1"
                style="font-size: 0.75rem"
              >
                {{ getDDayText(item.d_day) }}
              </CBadge>
            </template>
            <span v-else class="text-muted">-</span>
          </CTableDataCell>
          <CTableDataCell class="text-center">
            <span v-if="item.recipient_dept_name" class="badge bg-light text-dark border">
              {{ item.recipient_dept_name }}
            </span>
            <span v-else class="text-muted">-</span>
          </CTableDataCell>
          <CTableDataCell class="text-center">
            {{ item.recipient_manager_name || '-' }}
          </CTableDataCell>
          <CTableDataCell class="text-center">
            <CBadge v-if="item.status === 'received'" color="info">접수</CBadge>
            <CBadge v-else-if="item.status === 'in_progress'" color="warning">처리중</CBadge>
            <CBadge v-else-if="item.status === 'replied'" color="primary">회신완료</CBadge>
            <CBadge v-else-if="item.status === 'closed'" color="secondary">종결</CBadge>
            <CBadge v-else color="secondary">{{ item.status_desc || item.status }}</CBadge>
          </CTableDataCell>
          <CTableDataCell class="text-center">
            <CBadge v-if="item.has_scan || item.scan_file" color="success">
              <v-icon icon="mdi-file-pdf-box" size="small" />
            </CBadge>
            <span v-else class="text-muted">-</span>
          </CTableDataCell>
        </CTableRow>
        <CTableRow v-if="letterList.length === 0">
          <CTableDataCell colspan="10" class="text-center text-muted py-5">
            등록된 수신 공문이 없습니다.
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
