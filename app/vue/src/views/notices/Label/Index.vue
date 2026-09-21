<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { navMenu, pageTitle } from '@/views/notices/_menu/headermixin'
import { useNotice } from '@/store/pinia/notice'
import { useProject } from '@/store/pinia/project'
import { useContract } from '@/store/pinia/contract'
import { useProjectData } from '@/store/pinia/project_data'
import { usePerms } from '@/composables/usePerms'
import { SPECS, type PrintOptions } from './types'
import type { PostLabel } from '@/store/types/notice'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import NoticeAuthGuard from '@/components/AuthGuard/NoticeAuthGuard.vue'
import PrintSheet from './components/PrintSheet.vue'
import Pagination from '@/components/Pagination'

const { can, PERM } = usePerms()
const canNoticeRead = computed(() => can(PERM.NOTICE_READ))

const loading = ref(false)
const noticeStore = useNotice()
const projStore = useProject()
const contractStore = useContract()
const pDataStore = useProjectData()

const project = computed(() => (projStore.project as any)?.pk)
const orderGroups = computed(() => contractStore.orderGroupList)
const buildingList = computed(() => pDataStore.buildingList)

// 필터 상태
const filter = ref({
  order_group: '' as string | number,
  building: '' as string | number,
  search: '',
  addressType: 'auto' as 'auto' | 'dm' | 'id',
})

// 인쇄 서식 옵션
const printOptions = ref<PrintOptions>({
  specCode: '3107',
  startOffset: 1,
  honorific: '귀하',
  showUnitInfo: true,
  addressType: 'auto',
  fontSize: 'base',
})

// 주소지 옵션 변경 시 printOptions와 동기화
watch(
  () => filter.value.addressType,
  newVal => {
    printOptions.value.addressType = newVal
  },
)

// 클라이언트 페이지네이션 상태
const curPage = ref(1)
const pageSize = ref(50)

// 선택된 라벨 항목 ID 배열
const selectedIds = ref<number[]>([])

// 미리보기 모달 상태
const showPreviewModal = ref(false)

// 데이터 로드
const postLabels = computed(() => noticeStore.postLabels)
const postLabelsCount = computed(() => noticeStore.postLabelsCount)

// 현재 페이지의 표시 아이템 목록
const totalPages = computed(() => Math.max(1, Math.ceil(postLabels.value.length / pageSize.value)))

const paginatedPostLabels = computed(() => {
  const start = (curPage.value - 1) * pageSize.value
  return postLabels.value.slice(start, start + pageSize.value)
})

const onPageChange = (page: number) => {
  curPage.value = page
}

const onPageSizeChange = () => {
  curPage.value = 1
}

const fetchLabels = async () => {
  if (!project.value) return
  loading.value = true
  try {
    await noticeStore.fetchPostLabels({
      project: project.value,
      order_group: filter.value.order_group || undefined,
      building: filter.value.building || undefined,
      search: filter.value.search.trim() || undefined,
      limit: 3000,
    })
    curPage.value = 1
    // 조회 완료 시 전체 선택 기본값
    selectedIds.value = postLabels.value.map(item => item.id)
  } finally {
    loading.value = false
  }
}

// 프로젝트 변경 시 재조회
watch(
  () => project.value,
  async newProj => {
    if (newProj) {
      await Promise.all([
        contractStore.fetchOrderGroupList(newProj),
        pDataStore.fetchBuildingList(newProj),
      ])
      await fetchLabels()
    }
  },
)

onBeforeMount(async () => {
  if (project.value) {
    await Promise.all([
      contractStore.fetchOrderGroupList(project.value),
      pDataStore.fetchBuildingList(project.value),
    ])
    await fetchLabels()
  }
})

// 현재 페이지 전원 선택 여부 (체크박스 헤더용)
const isPageAllSelected = computed({
  get: () => {
    if (paginatedPostLabels.value.length === 0) return false
    const set = new Set(selectedIds.value)
    return paginatedPostLabels.value.every(item => set.has(item.id))
  },
  set: (val: boolean) => {
    const set = new Set(selectedIds.value)
    if (val) {
      paginatedPostLabels.value.forEach(item => set.add(item.id))
    } else {
      paginatedPostLabels.value.forEach(item => set.delete(item.id))
    }
    selectedIds.value = Array.from(set)
  },
})

// 전체(검색된 모든 건) 선택/해제 토글
const isAllTotalSelected = computed(
  () => postLabels.value.length > 0 && selectedIds.value.length === postLabels.value.length,
)

const toggleSelectAllTotal = () => {
  if (isAllTotalSelected.value) {
    selectedIds.value = []
  } else {
    selectedIds.value = postLabels.value.map(item => item.id)
  }
}

// 선택된 아이템 목록
const selectedItems = computed(() => {
  const set = new Set(selectedIds.value)
  return postLabels.value.filter(item => set.has(item.id))
})

// 선택 라벨 출력(브라우저 print 트리거)
const handlePrint = () => {
  if (selectedItems.value.length === 0) {
    alert('출력할 라벨을 1개 이상 선택해 주세요.')
    return
  }
  window.print()
}

// 주소 텍스트 렌더링 헬퍼
const displayAddress = (item: PostLabel) => {
  if (filter.value.addressType === 'dm') {
    const addr23 = `${item.dm_address2 || ''} ${item.dm_address3 || ''}`.trim()
    return `[${item.dm_zipcode || '-'}] ${item.dm_address1} ${addr23}`.trim()
  }
  if (filter.value.addressType === 'id') {
    const addr23 = `${item.id_address2 || ''} ${item.id_address3 || ''}`.trim()
    return `[${item.id_zipcode || '-'}] ${item.id_address1} ${addr23}`.trim()
  }
  const addr23 = `${item.effective_address2 || ''} ${item.effective_address3 || ''}`.trim()
  return `[${item.effective_zipcode || '-'}] ${item.effective_address1} ${addr23}`.trim()
}
</script>

<template>
  <Loading v-model:active="loading" />
  <ContentHeader :page-title="pageTitle" :nav-menu="navMenu" selector="ProjectSelect" />
  <ContentBody>
    <NoticeAuthGuard :is-authorized="canNoticeRead">
      <!-- 1. 상단 컨트롤 패널 (필터 + 라벨 규격 설정) -->
      <CCard class="m-3 shadow-sm">
        <CCardBody>
          <div class="row g-3">
            <!-- 차수 필터 -->
            <div class="col-12 col-md-3">
              <label class="form-label fw-bold text-secondary">차수 구분</label>
              <CFormSelect v-model="filter.order_group" @change="fetchLabels">
                <option value="">전체 차수</option>
                <option v-for="og in orderGroups" :key="og.pk" :value="og.pk">
                  {{ og.name }}
                </option>
              </CFormSelect>
            </div>

            <!-- 동 필터 -->
            <div class="col-12 col-md-3">
              <label class="form-label fw-bold text-secondary">동 구분</label>
              <CFormSelect v-model="filter.building" @change="fetchLabels">
                <option value="">전체 동</option>
                <option v-for="bldg in buildingList" :key="bldg.pk" :value="bldg.pk">
                  {{ bldg.name }}동
                </option>
              </CFormSelect>
            </div>

            <!-- 검색어 -->
            <div class="col-12 col-md-4">
              <label class="form-label fw-bold text-secondary">
                검색어 (성명, 동호수, 우편번호)
              </label>
              <CInputGroup>
                <CFormInput
                  v-model="filter.search"
                  placeholder="계약자명 / 동호수 / 주소 검색..."
                  @keydown.enter="fetchLabels"
                />
                <CButton color="primary" type="button" @click="fetchLabels">
                  <v-icon icon="mdi-magnify" size="small" />
                  검색
                </CButton>
              </CInputGroup>
            </div>

            <!-- 주소지 선택 옵션 -->
            <div class="col-12 col-md-12 pt-2 border-top">
              <div class="d-flex flex-wrap align-items-center gap-4">
                <span class="fw-bold text-secondary">출력 주소 기준:</span>
                <CFormCheck
                  id="addr-auto"
                  v-model="filter.addressType"
                  type="radio"
                  name="addressType"
                  value="auto"
                  label="우편송부지 우선 (미등록 시 주민등록지 대체)"
                />
                <CFormCheck
                  id="addr-dm"
                  v-model="filter.addressType"
                  type="radio"
                  name="addressType"
                  value="dm"
                  label="우편송부지 전용"
                />
                <CFormCheck
                  id="addr-id"
                  v-model="filter.addressType"
                  type="radio"
                  name="addressType"
                  value="id"
                  label="주민등록지 전용"
                />
              </div>
            </div>
          </div>
        </CCardBody>
      </CCard>

      <!-- 2. 라벨지 규격 및 인쇄 옵션 패널 -->
      <CCard class="mx-3 mb-4 border-primary border-opacity-25 shadow-sm">
        <CCardHeader
          class="bg-primary bg-opacity-10 py-2 d-flex justify-content-between align-items-center"
        >
          <div class="fw-bold text-primary d-flex align-items-center">
            <v-icon icon="mdi-label-outline" size="small" class="me-1" />
            라벨 서식 및 인쇄 설정
          </div>
          <div class="text-muted">
            선택된 대상: <strong class="text-primary">{{ selectedIds.length }}</strong> /
            {{ postLabels.length }}명
          </div>
        </CCardHeader>
        <CCardBody class="py-3">
          <div class="row g-3 align-items-center">
            <!-- 라벨 규격 -->
            <div class="col-12 col-md-6 col-lg-4 col-xl-3">
              <label class="form-label fw-bold text-secondary mb-1"> 라벨지 규격 (Formtec) </label>
              <CFormSelect v-model="printOptions.specCode">
                <option v-for="spec in SPECS" :key="spec.code" :value="spec.code">
                  {{ spec.name }}
                </option>
              </CFormSelect>
            </div>

            <!-- 시작 위치 (Offset) -->
            <div class="col-6 col-lg-2">
              <label class="form-label fw-bold text-secondary mb-1"> 시작 위치 (잔여지) </label>
              <CFormSelect v-model.number="printOptions.startOffset">
                <option
                  v-for="idx in SPECS[printOptions.specCode]?.perPage || 16"
                  :key="idx"
                  :value="idx"
                >
                  {{ idx }}번째 칸부터
                </option>
              </CFormSelect>
            </div>

            <!-- 호칭 -->
            <div class="col-6 col-lg-2">
              <label class="form-label fw-bold text-secondary mb-1">수신인 호칭</label>
              <CFormSelect v-model="printOptions.honorific">
                <option value="귀하">귀하</option>
                <option value="님">님</option>
                <option value="앞">앞</option>
                <option value="">(표기 안 함)</option>
              </CFormSelect>
            </div>

            <!-- 폰트 크기 -->
            <div class="col-6 col-lg-2">
              <label class="form-label fw-bold text-secondary mb-1">글자 크기</label>
              <CFormSelect v-model="printOptions.fontSize">
                <option value="sm">작게 (8pt)</option>
                <option value="base">보통 (9.5pt)</option>
                <option value="lg">크게 (11pt)</option>
              </CFormSelect>
            </div>

            <!-- 동호수 표기 여부 -->
            <div class="col-6 col-lg-2 pt-lg-4">
              <CFormCheck
                id="show-unit"
                v-model="printOptions.showUnitInfo"
                label="동호수 라벨 표기"
              />
            </div>
          </div>
        </CCardBody>
      </CCard>

      <!-- 3. 명단 테이블 및 인쇄 액션 바 -->
      <CCard class="mx-3 shadow-sm">
        <CCardHeader
          class="bg-light py-2 d-flex flex-wrap justify-content-between align-items-center"
        >
          <div class="fw-bold d-flex align-items-center">
            <v-icon icon="mdi-account-group" size="small" class="me-1 text-primary" />
            라벨 출력 대상 목록
            <v-chip
              color="primary"
              shape="rounded-pill"
              class="ms-2"
              size="x-small"
              variant="outlined"
            >
              {{ selectedIds.length }} / {{ postLabels.length }}
            </v-chip>
          </div>

          <div class="d-flex flex-wrap align-items-center gap-2 mt-2 mt-md-0">
            <!-- 전체(검색 전체 건) 일괄 선택/해제 버튼 -->
            <v-btn
              :color="isAllTotalSelected ? 'blue-grey-lighten-1' : 'primary'"
              variant="outlined"
              size="small"
              :disabled="postLabels.length === 0"
              @click="toggleSelectAllTotal"
            >
              <v-icon
                :icon="
                  isAllTotalSelected
                    ? 'mdi-checkbox-blank-outline'
                    : 'mdi-checkbox-multiple-marked-outline'
                "
                size="small"
                class="me-1"
              />
              {{
                isAllTotalSelected ? '전체 선택 해제' : `검색 전체 선택 (${postLabels.length}건)`
              }}
            </v-btn>

            <!-- 미리보기 모달 버튼 -->
            <v-btn
              color="blue-grey-lighten-1"
              variant="flat"
              size="small"
              :disabled="selectedIds.length === 0"
              @click="showPreviewModal = true"
            >
              <v-icon icon="mdi-eye" size="small" class="me-1" />
              인쇄 미리보기
            </v-btn>

            <!-- 즉시 인쇄 버튼 -->
            <v-btn
              color="primary"
              size="small"
              :disabled="selectedIds.length === 0"
              @click="handlePrint"
            >
              <v-icon icon="mdi-printer" size="small" class="me-1" />
              선택 라벨 인쇄 ({{ selectedIds.length }}건)
            </v-btn>
          </div>
        </CCardHeader>

        <CCardBody class="p-0 table-responsive">
          <CTable hover align="middle" class="mb-0 text-center small">
            <CTableHead color="light">
              <CTableRow>
                <CTableHeaderCell style="width: 45px">
                  <CFormCheck v-model="isPageAllSelected" title="현재 페이지 전체 선택/해제" />
                </CTableHeaderCell>
                <CTableHeaderCell style="width: 60px">No</CTableHeaderCell>
                <CTableHeaderCell style="width: 120px">차수</CTableHeaderCell>
                <CTableHeaderCell style="width: 140px">동 / 호수</CTableHeaderCell>
                <CTableHeaderCell style="width: 120px">계약자명</CTableHeaderCell>
                <CTableHeaderCell style="width: 100px">우편번호</CTableHeaderCell>
                <CTableHeaderCell class="text-start">적용 주소</CTableHeaderCell>
                <CTableHeaderCell style="width: 110px">주소 구분</CTableHeaderCell>
              </CTableRow>
            </CTableHead>

            <CTableBody>
              <template v-if="paginatedPostLabels.length > 0">
                <CTableRow v-for="(item, idx) in paginatedPostLabels" :key="item.id">
                  <CTableDataCell>
                    <input
                      v-model="selectedIds"
                      type="checkbox"
                      :value="item.id"
                      class="form-check-input"
                    />
                  </CTableDataCell>
                  <CTableDataCell class="text-muted">
                    {{ (curPage - 1) * pageSize + idx + 1 }}
                  </CTableDataCell>
                  <CTableDataCell>{{ item.order_group_name || '-' }}</CTableDataCell>
                  <CTableDataCell class="fw-bold">
                    {{ item.unit_info || item.contract_serial || '-' }}
                  </CTableDataCell>
                  <CTableDataCell class="fw-bold text-primary">
                    {{ item.contractor_name }}
                  </CTableDataCell>
                  <CTableDataCell class="font-monospace fw-bold">
                    {{ item.effective_zipcode || '-' }}
                  </CTableDataCell>
                  <CTableDataCell class="text-start text-truncate" style="max-width: 360px">
                    {{ displayAddress(item) }}
                  </CTableDataCell>
                  <CTableDataCell>
                    <CBadge :color="item.has_dm_address ? 'info' : 'secondary'" variant="outline">
                      {{ item.has_dm_address ? '우편송부지' : '주민등록지' }}
                    </CBadge>
                  </CTableDataCell>
                </CTableRow>
              </template>
              <template v-else>
                <CTableRow>
                  <CTableDataCell colspan="8" class="py-5 text-muted">
                    <div class="mb-2">
                      <v-icon icon="mdi-alert-circle-outline" size="large" class="text-secondary" />
                    </div>
                    조회된 계약자 라벨 데이터가 없습니다. 프로젝트를 선택하거나 검색 조건을 확인해
                    주세요.
                  </CTableDataCell>
                </CTableRow>
              </template>
            </CTableBody>
          </CTable>
        </CCardBody>

        <CCardFooter
          v-if="postLabels.length > 0"
          class="bg-white py-2 d-flex flex-wrap justify-content-between align-items-center"
        >
          <!-- 표시 개수 선택 -->
          <div class="d-flex align-items-center gap-2 text-secondary small">
            <span>페이지당 표시:</span>
            <CFormSelect
              v-model.number="pageSize"
              size="sm"
              style="width: 100px"
              @change="onPageSizeChange"
            >
              <option :value="30">30개</option>
              <option :value="50">50개</option>
              <option :value="100">100개</option>
              <option :value="200">200개</option>
            </CFormSelect>
            <span class="ms-2">
              (총 <strong>{{ postLabels.length.toLocaleString() }}</strong
              >건 중 {{ (curPage - 1) * pageSize + 1 }} -
              {{ Math.min(curPage * pageSize, postLabels.length) }}건 표시)
            </span>
          </div>

          <!-- 페이지네이션 컨트롤 -->
          <div class="mt-2 mt-sm-0">
            <Pagination
              :active-page="curPage"
              :limit="7"
              :pages="totalPages"
              @active-page-change="onPageChange"
            />
          </div>
        </CCardFooter>
      </CCard>

      <!-- 4. 인쇄 전용 숨김 시트 (브라우저 print() 호출 시 이 영역만 1:1로 렌더링됨) -->
      <div class="d-none d-print-block">
        <PrintSheet :items="selectedItems" :options="printOptions" />
      </div>

      <!-- 5. 인쇄 미리보기 모달 다이얼로그 -->
      <CModal size="xl" :visible="showPreviewModal" scrollable @close="showPreviewModal = false">
        <CModalHeader>
          <CModalTitle>
            <v-icon icon="mdi-printer-eye" class="me-1 text-primary" />
            우편 라벨 인쇄 미리보기 (A4 용지 실측 뷰)
          </CModalTitle>
        </CModalHeader>
        <CModalBody class="p-0 bg-slate-100" style="max-height: 75vh; overflow-y: auto">
          <PrintSheet :items="selectedItems" :options="printOptions" />
        </CModalBody>
        <CModalFooter>
          <div class="me-auto text-muted small">
            규격: <strong>{{ SPECS[printOptions.specCode]?.name }}</strong> | 총
            {{ selectedItems.length }}개 라벨
          </div>
          <v-btn color="secondary" variant="outlined" @click="showPreviewModal = false">
            닫기
          </v-btn>
          <v-btn color="primary" @click="handlePrint">
            <v-icon icon="mdi-printer" size="small" class="me-1" />
            이대로 인쇄하기
          </v-btn>
        </CModalFooter>
      </CModal>
    </NoticeAuthGuard>
  </ContentBody>
</template>

<style scoped>
/* 화면에서는 인쇄 시트 영역 완전 숨김 */
@media screen {
  .d-print-block {
    display: none !important;
  }
}

/* 인쇄 모드 시 화면의 모든 UI 숨기고 인쇄 시트만 표출 */
@media print {
  body * {
    visibility: hidden;
  }
  .d-print-block,
  .d-print-block * {
    visibility: visible;
  }
  .d-print-block {
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
    display: block !important;
  }
}
</style>
