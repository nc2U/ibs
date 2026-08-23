<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useApproval } from '@/store/pinia/approval'
import { useCompany } from '@/store/pinia/company'
import { TableSecondary } from '@/utils/cssMixins'
import type { DocumentStatus } from '@/store/types/approval'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import Pagination from '@/components/Pagination'

const router = useRouter()
const approvalStore = useApproval()
const companyStore = useCompany()

const { allDocumentList, allDocumentsCount, docCategoryList, docTypeList } =
  storeToRefs(approvalStore)
const { allDepartList } = storeToRefs(companyStore)

// 필터 상태
const filterCategory = ref<string>('')
const filterDocType = ref<string>('')
const filterStatus = ref<DocumentStatus | ''>('')
const filterSecurityLevel = ref<string>('')
const filterDepartment = ref<string>('')
const filterStartDate = ref('')
const filterEndDate = ref('')
const searchText = ref('')
const currentPage = ref(1)

// 선택된 카테고리에 해당하는 문서 유형 필터링
const filteredDocTypes = computed(() => {
  if (!filterCategory.value) return docTypeList.value
  return docTypeList.value.filter(dt => String(dt.category) === filterCategory.value)
})

watch(filterCategory, () => {
  filterDocType.value = ''
  onSearch()
})

const STATUS_LABEL: Record<DocumentStatus, string> = {
  draft: '임시저장',
  pending: '결재중',
  approved: '승인완료',
  rejected: '반려',
  cancelled: '취소',
}

const STATUS_COLOR: Record<DocumentStatus, string> = {
  draft: 'secondary',
  pending: 'warning',
  approved: 'success',
  rejected: 'danger',
  cancelled: 'dark',
}

const fmtDate = (d: string | null) => {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('ko-KR')
}

const fetchList = async (page = 1) => {
  currentPage.value = page
  await approvalStore.fetchAllDocuments({
    page,
    category: filterCategory.value ? Number(filterCategory.value) : null,
    doc_type: filterDocType.value ? Number(filterDocType.value) : null,
    status: filterStatus.value || undefined,
    security_level: filterSecurityLevel.value || undefined,
    department: filterDepartment.value ? Number(filterDepartment.value) : null,
    start_date: filterStartDate.value || undefined,
    end_date: filterEndDate.value || undefined,
    search: searchText.value || undefined,
  })
}

const onSearch = () => {
  fetchList(1)
}

const resetFilter = () => {
  filterCategory.value = ''
  filterDocType.value = ''
  filterStatus.value = ''
  filterSecurityLevel.value = ''
  filterDepartment.value = ''
  filterStartDate.value = ''
  filterEndDate.value = ''
  searchText.value = ''
  fetchList(1)
}

const goDetail = (id: number) => {
  router.push({ name: '전체 문서함 - 보기', params: { docId: id } })
}

const totalPages = computed(() => approvalStore.allDocumentPages(10))

onMounted(async () => {
  await Promise.all([
    approvalStore.fetchDocCategoryList(),
    approvalStore.fetchDocTypeList(),
    companyStore.fetchAllDepartList(1),
  ])
  await fetchList(1)
})
</script>

<template>
  <div class="all-documents-container">
    <!-- 검색 및 필터 패널 -->
    <CCallout class="mb-4 border-0 shadow-sm bg-light">
      <CRow>
        <CCol xl="7">
          <CRow class="g-2 align-items-center">
            <CCol lg="5">
              <CRow>
                <!-- 카테고리 -->
                <CCol xs="12" sm="6" class="mb-2">
                  <CFormSelect v-model="filterCategory" @change="onSearch">
                    <option value="">전체 카테고리</option>
                    <option v-for="cat in docCategoryList" :key="cat.id" :value="String(cat.id)">
                      {{ cat.name }}
                    </option>
                  </CFormSelect>
                </CCol>

                <!-- 문서 유형 -->
                <CCol xs="12" sm="6" class="mb-2">
                  <CFormSelect v-model="filterDocType" @change="onSearch">
                    <option value="">전체 문서유형</option>
                    <option v-for="dt in filteredDocTypes" :key="dt.id" :value="String(dt.id)">
                      {{ dt.name }}
                    </option>
                  </CFormSelect>
                </CCol>
              </CRow>
            </CCol>

            <CCol lg="7">
              <CRow>
                <!-- 공개 등급 -->
                <CCol xs="12" sm="6" lg="4" class="mb-2">
                  <CFormSelect v-model="filterSecurityLevel" @change="onSearch">
                    <option value="">전체 공개등급</option>
                    <option value="1">🔒 1등급 (비공개)</option>
                    <option value="2">👥 2등급 (부서공개)</option>
                    <option value="3">🌐 3등급 (전사공개)</option>
                  </CFormSelect>
                </CCol>

                <!-- 결재 상태 -->
                <CCol xs="12" sm="6" lg="4" class="mb-2">
                  <CFormSelect v-model="filterStatus" @change="onSearch">
                    <option value="">전체 상태</option>
                    <option value="pending">결재중</option>
                    <option value="approved">승인완료</option>
                    <option value="rejected">반려</option>
                    <option value="cancelled">취소</option>
                    <option value="draft">임시저장</option>
                  </CFormSelect>
                </CCol>

                <!-- 기안 부서 -->
                <CCol xs="12" sm="6" lg="4" class="mb-2">
                  <CFormSelect v-model="filterDepartment" @change="onSearch">
                    <option value="">전체 부서</option>
                    <option v-for="dept in allDepartList" :key="dept.pk" :value="String(dept.pk)">
                      {{ dept.name }}
                    </option>
                  </CFormSelect>
                </CCol>
              </CRow>
            </CCol>
          </CRow>
        </CCol>
        <CCol xl="5">
          <CRow class="g-2 align-items-center">
            <!-- 기안일자 기간 -->
            <CCol xs="12" lg="6" class="d-flex align-items-center gap-1">
              <DatePicker v-model="filterStartDate" @change="onSearch" />
              <span class="text-muted">~</span>
              <DatePicker v-model="filterEndDate" @change="onSearch" />
            </CCol>

            <!-- 검색어 + 버튼 -->
            <CCol xs="12" lg="6">
              <CInputGroup>
                <CFormInput
                  v-model="searchText"
                  placeholder="문서번호, 제목, 기안자 검색..."
                  @keyup.enter="onSearch"
                />
                <CInputGroupText @click="onSearch">
                  <v-icon icon="mdi-magnify" size="x-small" /> 검색
                </CInputGroupText>
                <CInputGroupText @click="resetFilter">
                  <v-icon icon="mdi-refresh" size="x-small" /> 초기화
                </CInputGroupText>
              </CInputGroup>
            </CCol>
          </CRow>
        </CCol>
      </CRow>

      <CRow>
        <!--        <CCol color="warning" class="p-2 pl-3">-->
        <!--          <strong> 문서 건수 조회 결과 : {{ numFormat(docsCount, 0, 0) }} 건 </strong>-->
        <!--        </CCol>-->
        <!--        <CCol v-if="!formsCheck" class="text-right mb-0">-->
        <!--          <v-btn color="info" size="small" @click="resetForm"> 검색조건 초기화</v-btn>-->
        <!--        </CCol>-->
      </CRow>
    </CCallout>

    <!-- 문서 현황 바 -->
    <div class="d-flex justify-content-between align-items-center mb-3">
      <div class="d-flex align-items-center gap-2">
        <h6 class="mb-0 fw-bold">전사 결재 문서 목록</h6>
        <CBadge color="primary" shape="rounded-pill">총 {{ allDocumentsCount }}건</CBadge>
      </div>
    </div>

    <!-- 문서 목록 테이블 -->
    <CTable hover responsive bordered align="middle">
      <colgroup>
        <col style="width: 6%" />
        <col style="width: 14%" />
        <col style="width: 8%" />
        <col style="width: 10%" />
        <col style="width: 10%" />
        <col style="width: 10%" />
        <col style="width: 22%" />
        <col style="width: 10%" />
        <col style="width: 10%" />
      </colgroup>

      <CTableHead :color="TableSecondary">
        <CTableRow class="text-center">
          <CTableHeaderCell scope="col">No</CTableHeaderCell>
          <CTableHeaderCell scope="col">문서번호</CTableHeaderCell>
          <CTableHeaderCell scope="col">공개등급</CTableHeaderCell>
          <CTableHeaderCell scope="col">카테고리 / 유형</CTableHeaderCell>
          <CTableHeaderCell scope="col">기안 부서 / 직책</CTableHeaderCell>
          <CTableHeaderCell scope="col">기안자</CTableHeaderCell>
          <CTableHeaderCell scope="col">제목</CTableHeaderCell>
          <CTableHeaderCell scope="col">상태</CTableHeaderCell>
          <CTableHeaderCell scope="col">기안일시</CTableHeaderCell>
        </CTableRow>
      </CTableHead>

      <CTableBody>
        <CTableRow v-if="allDocumentList.length === 0">
          <CTableDataCell colspan="9" class="text-center py-5 text-muted">
            <v-icon icon="mdi-file-document-outline" size="large" class="mb-2" />
            <div>조회된 결재 문서가 없습니다.</div>
          </CTableDataCell>
        </CTableRow>

        <CTableRow
          v-for="(doc, idx) in allDocumentList"
          :key="doc.id"
          class="cursor-pointer"
          @click="goDetail(doc.id)"
        >
          <!-- No -->
          <CTableDataCell class="text-center text-muted">
            {{ allDocumentsCount - (currentPage - 1) * 10 - idx }}
          </CTableDataCell>

          <!-- 문서번호 -->
          <CTableDataCell class="text-center fw-semibold font-monospace small">
            {{ doc.doc_number || '-' }}
          </CTableDataCell>

          <!-- 공개등급 -->
          <CTableDataCell class="text-center">
            <CBadge
              :color="
                doc.security_level === '1'
                  ? 'danger'
                  : doc.security_level === '2'
                    ? 'primary'
                    : 'success'
              "
              variant="outline"
              class="small"
            >
              {{
                doc.security_level === '1'
                  ? '🔒 1등급'
                  : doc.security_level === '2'
                    ? '👥 2등급'
                    : '🌐 3등급'
              }}
            </CBadge>
          </CTableDataCell>

          <!-- 카테고리 / 문서유형 -->
          <CTableDataCell>
            <span class="small text-muted mr-2">{{ doc.category_name || '일반' }}</span>
            <span class="fw-semibold">{{ doc.doc_type_name }}</span>
          </CTableDataCell>

          <!-- 기안 부서 / 직책 -->
          <CTableDataCell class="text-center small">
            {{ doc.drafter_assignment_desc || doc.department_name || '-' }}
          </CTableDataCell>

          <!-- 기안자 -->
          <CTableDataCell class="text-center">
            {{ doc.drafter_name || doc.drafter?.username }}
          </CTableDataCell>

          <!-- 제목 -->
          <CTableDataCell>
            <div class="d-flex align-items-center gap-1">
              <span class="fw-semibold text-primary text-decoration-none">
                {{ doc.title }}
              </span>
              <v-icon
                v-if="doc.attachment_count && doc.attachment_count > 0"
                icon="mdi-paperclip"
                size="x-small"
                class="text-muted"
              />
              <CBadge
                v-if="doc.observer_count && doc.observer_count > 0"
                color="light"
                text-color="dark"
                class="border small py-0 px-1"
              >
                참조 {{ doc.observer_count }}
              </CBadge>
            </div>
          </CTableDataCell>

          <!-- 상태 -->
          <CTableDataCell class="text-center">
            <CBadge :color="STATUS_COLOR[doc.status]" shape="rounded-pill">
              {{ doc.status_desc || STATUS_LABEL[doc.status] }}
            </CBadge>
          </CTableDataCell>

          <!-- 기안일시 -->
          <CTableDataCell class="text-center text-muted">
            {{ fmtDate(doc.submitted_at || doc.created_at) }}
          </CTableDataCell>
        </CTableRow>
      </CTableBody>
    </CTable>

    <!-- 페이지네이션 -->
    <Pagination
      v-if="allDocumentsCount > 10"
      :active-page="currentPage"
      :limit="8"
      :pages="totalPages"
      class="mt-3"
      @active-page-change="fetchList"
    />
  </div>
</template>

<style scoped>
.cursor-pointer {
  cursor: pointer;
}
.cursor-pointer:hover {
  background-color: rgba(var(--v-theme-primary), 0.04);
}
</style>
