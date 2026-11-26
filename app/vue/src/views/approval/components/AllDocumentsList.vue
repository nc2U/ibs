<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useApproval } from '@/store/pinia/approval'
import { useCompany } from '@/store/pinia/company'
import { TableSecondary } from '@/utils/cssMixins'
import { message } from '@/utils/helper'
import type { DocumentStatus, SecurityLevel } from '@/store/types/approval'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import Pagination from '@/components/Pagination'
import {
  DOC_STATUS_CHIP_COLOR,
  DOC_STATUS_LABEL,
  SECURITY_LEVEL_META,
  fmtDate,
  getUserDisplayName,
} from '../utils/approvalMeta'

const ITEMS_PER_PAGE = 10

const router = useRouter()
const approvalStore = useApproval()
const companyStore = useCompany()

const { allDocumentList, allDocumentsCount, docCategoryList, docTypeList } =
  storeToRefs(approvalStore)
const { allDepartList, company } = storeToRefs(companyStore)

// 로딩 상태
const loading = ref(false)
const isResetting = ref(false)
const loadedDeptComId = ref<number | null>(null)

// 필터 상태
const filterCategory = ref<string>('')
const filterDocType = ref<string>('')
const filterStatus = ref<DocumentStatus | ''>('')
const filterSecurityLevel = ref<SecurityLevel | ''>('')
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

// 카테고리 변경 시 문서유형 초기화 및 재조회
const onCategoryChange = () => {
  filterDocType.value = ''
  onSearch()
}

const fetchList = async (page = 1) => {
  if (filterStartDate.value && filterEndDate.value && filterStartDate.value > filterEndDate.value) {
    message('warning', '기간 확인', '조회 종료일은 시작일과 같거나 이후여야 합니다.')
    return
  }
  loading.value = true
  currentPage.value = page
  try {
    await approvalStore.fetchAllDocuments({
      page,
      category: filterCategory.value ? Number(filterCategory.value) : null,
      doc_type: filterDocType.value ? Number(filterDocType.value) : null,
      status: filterStatus.value || undefined,
      security_level: filterSecurityLevel.value || undefined,
      department: filterDepartment.value ? Number(filterDepartment.value) : null,
      start_date: filterStartDate.value || undefined,
      end_date: filterEndDate.value || undefined,
      search: searchText.value.trim() || undefined,
    })
  } finally {
    loading.value = false
  }
}

const onSearch = () => {
  fetchList(1)
}

// 기간 선택 변경 감지 (초기화 중에는 중복 호출 방지)
watch([filterStartDate, filterEndDate], () => {
  if (isResetting.value) return
  onSearch()
})

// 회사 변경 시 부서 목록만 동기화하고, 사용자가 회사를 전환한 경우에만 부서 필터 초기화 및 재조회
watch(
  () => company.value?.pk,
  async (newComId, oldComId) => {
    if (!newComId || newComId === loadedDeptComId.value) return
    loadedDeptComId.value = newComId
    await companyStore.fetchAllDepartList(newComId)
    if (oldComId) {
      filterDepartment.value = ''
      await fetchList(1)
    }
  },
)

const resetFilter = async () => {
  isResetting.value = true
  filterCategory.value = ''
  filterDocType.value = ''
  filterStatus.value = ''
  filterSecurityLevel.value = ''
  filterDepartment.value = ''
  filterStartDate.value = ''
  filterEndDate.value = ''
  searchText.value = ''
  await Promise.resolve()
  isResetting.value = false
  await fetchList(1)
}

const goDetail = (id: number) => {
  router.push({ name: '전체 문서함 - 보기', params: { docId: id } })
}

const totalPages = computed(() => approvalStore.allDocumentPages(ITEMS_PER_PAGE))

onMounted(async () => {
  const comId = company.value?.pk || companyStore.initComId || 1
  loadedDeptComId.value = comId
  await Promise.all([
    approvalStore.fetchDocCategoryList(),
    approvalStore.fetchDocTypeList(),
    companyStore.fetchAllDepartList(comId),
    fetchList(1),
  ])
})
</script>

<template>
  <div class="all-documents-container">
    <!-- 검색 및 필터 패널 -->
    <CCallout class="mb-4 border-0 shadow-sm bg-more-light">
      <CRow>
        <CCol xl="7">
          <CRow class="g-2 align-items-center">
            <CCol lg="5">
              <CRow>
                <!-- 카테고리 -->
                <CCol xs="12" sm="6" class="mb-2">
                  <CFormSelect v-model="filterCategory" @change="onCategoryChange">
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
              <DatePicker v-model="filterStartDate" placeholder="시작일" />
              <span class="text-muted">~</span>
              <DatePicker v-model="filterEndDate" placeholder="종료일" />
            </CCol>

            <!-- 검색어 + 버튼 -->
            <CCol xs="12" lg="6">
              <CInputGroup>
                <CFormInput
                  v-model="searchText"
                  placeholder="문서번호, 제목, 기안자 검색..."
                  @keyup.enter="onSearch"
                />
                <CButton type="button" color="primary" variant="outline" @click="onSearch">
                  <v-icon icon="mdi-magnify" size="x-small" /> 검색
                </CButton>
                <CButton type="button" color="secondary" variant="outline" @click="resetFilter">
                  <v-icon icon="mdi-refresh" size="x-small" /> 초기화
                </CButton>
              </CInputGroup>
            </CCol>
          </CRow>
        </CCol>
      </CRow>
    </CCallout>

    <!-- 문서 현황 바 -->
    <div class="d-flex justify-content-between align-items-center mb-3">
      <div class="d-flex align-items-center gap-2">
        <h6 class="mb-0 fw-bold">전사 결재 문서 목록</h6>
        <v-chip color="info" variant="elevated" size="x-small">
          총 {{ allDocumentsCount }}건
        </v-chip>
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
        <CTableRow v-if="loading">
          <CTableDataCell colspan="9" class="text-center py-5 text-muted">
            <CSpinner size="sm" color="primary" class="me-2" />
            문서를 불러오는 중입니다...
          </CTableDataCell>
        </CTableRow>

        <CTableRow v-else-if="allDocumentList.length === 0">
          <CTableDataCell colspan="9" class="text-center py-5 text-muted">
            <v-icon icon="mdi-file-document-outline" size="large" class="mb-2" />
            <div>조회된 결재 문서가 없습니다.</div>
          </CTableDataCell>
        </CTableRow>

        <CTableRow
          v-for="(doc, idx) in allDocumentList"
          v-else
          :key="doc.id"
          class="cursor-pointer"
          @click="goDetail(doc.id)"
        >
          <!-- No -->
          <CTableDataCell class="text-center text-muted">
            {{ allDocumentsCount - (currentPage - 1) * ITEMS_PER_PAGE - idx }}
          </CTableDataCell>

          <!-- 문서번호 -->
          <CTableDataCell class="text-center fw-semibold font-monospace small">
            {{ doc.doc_number || '-' }}
          </CTableDataCell>

          <!-- 공개등급 -->
          <CTableDataCell class="text-center">
            <v-chip
              v-if="doc.security_level"
              :color="SECURITY_LEVEL_META[doc.security_level].color"
              variant="tonal"
              size="x-small"
            >
              {{ SECURITY_LEVEL_META[doc.security_level].shortLabel }}
            </v-chip>
            <span v-else class="text-muted small">-</span>
          </CTableDataCell>

          <!-- 카테고리 / 문서유형 -->
          <CTableDataCell>
            <span class="small text-muted me-2">{{ doc.category_name || '일반' }}</span>
            <span class="fw-semibold">{{ doc.doc_type_name }}</span>
          </CTableDataCell>

          <!-- 기안 부서 / 직책 -->
          <CTableDataCell class="text-center small">
            {{ doc.drafter_assignment_desc || doc.department_name || '-' }}
          </CTableDataCell>

          <!-- 기안자 -->
          <CTableDataCell class="text-center">
            {{ doc.drafter_name || getUserDisplayName(doc.drafter) }}
          </CTableDataCell>

          <!-- 제목 -->
          <CTableDataCell>
            <div class="d-flex align-items-center gap-1">
              <span class="fw-semibold text-primary text-decoration-none text-truncate">
                {{ doc.title }}
              </span>
              <v-icon
                v-if="doc.attachment_count && doc.attachment_count > 0"
                icon="mdi-paperclip"
                size="x-small"
                class="text-muted flex-shrink-0"
              />
              <v-chip
                v-if="doc.observer_count && doc.observer_count > 0"
                color="secondary"
                variant="tonal"
                size="x-small"
                class="flex-shrink-0"
              >
                참조 {{ doc.observer_count }}
              </v-chip>
            </div>
          </CTableDataCell>

          <!-- 상태 -->
          <CTableDataCell class="text-center">
            <v-chip :color="DOC_STATUS_CHIP_COLOR[doc.status]" variant="flat" size="x-small">
              {{ doc.status_desc || DOC_STATUS_LABEL[doc.status] }}
            </v-chip>
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
      v-if="allDocumentsCount > ITEMS_PER_PAGE"
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
