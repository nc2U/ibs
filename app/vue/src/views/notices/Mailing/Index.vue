<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { navMenu, pageTitle } from '@/views/notices/_menu/headermixin'
import { useNotice } from '@/store/pinia/notice'
import { useProject } from '@/store/pinia/project'
import { useContract } from '@/store/pinia/contract'
import { useProjectData } from '@/store/pinia/project_data'
import { usePerms } from '@/composables/usePerms'
import type { EmailNotice } from '@/store/types/notice'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import NoticeAuthGuard from '@/components/AuthGuard/NoticeAuthGuard.vue'
import QuillEditor from '@/components/QuillEditor/index.vue'
import Loading from '@/components/Loading/Index.vue'

const { can, PERM } = usePerms()
const canNoticeRead = computed(() => can(PERM.NOTICE_READ))

const loading = ref(false)
const activeTab = ref<'write' | 'history'>('write')

const noticeStore = useNotice()
const projStore = useProject()
const contractStore = useContract()
const pDataStore = useProjectData()

const project = computed(() => (projStore.project as any)?.pk)
const orderGroups = computed(() => contractStore.orderGroupList)
const buildingList = computed(() => pDataStore.buildingList)

// ── 1. 작성 폼 상태 ──
const filter = ref({
  order_group: '' as string | number,
  building: '' as string | number,
})

const form = ref({
  sender_name: '',
  sender_email: '',
  title: '',
  content: '',
})

// 수신 대상자 집계 상태
const recipientsData = computed(() => noticeStore.emailRecipientsData)
const showUnregisteredModal = ref(false)
const showRecipientManageModal = ref(false)

// 수신 대상자 목록 (편집 및 개별 선택 가능 상태)
export interface EditableRecipient {
  contractor_id: number | null
  name: string
  email: string
  unit_info: string
  order_group_name: string
  selected: boolean
  is_custom?: boolean // 직접 추가한 수신자인지 여부
}

const editableRecipients = ref<EditableRecipient[]>([])
const recipientSearch = ref('')

// 직접 추가 수신자 입력 상태
const manualName = ref('')
const manualEmail = ref('')

// recipientsData가 로드되면 editableRecipients 초기화
watch(
  () => recipientsData.value,
  data => {
    if (!data) {
      editableRecipients.value = []
      return
    }
    // 등록자 (선택 상태로 초기화)
    const registered: EditableRecipient[] = (data.recipients || []).map(r => ({
      contractor_id: r.contractor_id,
      name: r.name,
      email: r.email,
      unit_info: r.unit_info,
      order_group_name: r.order_group_name,
      selected: true,
      is_custom: false,
    }))
    // 미등록자 (미선택 상태, 이메일 빈칸으로 초기화)
    const unregistered: EditableRecipient[] = (data.unregistered_contractors || []).map(u => ({
      contractor_id: u.contractor_id,
      name: u.name,
      email: '',
      unit_info: u.unit_info,
      order_group_name: u.order_group_name,
      selected: false,
      is_custom: false,
    }))
    editableRecipients.value = [...registered, ...unregistered]
  },
  { immediate: true },
)

// 최종 발송 대상 목록 (선택되어 있고 이메일이 유효한 건)
const finalRecipients = computed(() => {
  return editableRecipients.value.filter(r => r.selected && r.email.trim().length > 0)
})

// 모달 검색 필터 적용 목록
const filteredEditableRecipients = computed(() => {
  const query = recipientSearch.value.trim().toLowerCase()
  if (!query) return editableRecipients.value
  return editableRecipients.value.filter(
    r =>
      r.name.toLowerCase().includes(query) ||
      r.email.toLowerCase().includes(query) ||
      r.unit_info.toLowerCase().includes(query) ||
      r.order_group_name.toLowerCase().includes(query),
  )
})

// 모달 전체 선택 / 해제
const isAllFilteredSelected = computed({
  get: () =>
    filteredEditableRecipients.value.length > 0 &&
    filteredEditableRecipients.value.every(r => r.selected),
  set: (val: boolean) => {
    filteredEditableRecipients.value.forEach(r => {
      r.selected = val
    })
  },
})

// 직접 수동 수신자 추가
const addManualRecipient = () => {
  const name = manualName.value.trim()
  const email = manualEmail.value.trim()
  if (!name) {
    alert('수신자 이름을 입력해 주세요.')
    return
  }
  if (!email || !email.includes('@')) {
    alert('올바른 이메일 주소를 입력해 주세요.')
    return
  }
  editableRecipients.value.unshift({
    contractor_id: null,
    name,
    email,
    unit_info: '직접 추가',
    order_group_name: '-',
    selected: true,
    is_custom: true,
  })
  manualName.value = ''
  manualEmail.value = ''
}

// 직접 추가 수신자 삭제
const removeManualRecipient = (idx: number) => {
  editableRecipients.value.splice(idx, 1)
}

// 대상자 집계 로드
const fetchRecipients = async () => {
  if (!project.value) return
  await noticeStore.fetchEmailRecipients({
    project: project.value,
    order_group: filter.value.order_group || undefined,
    building: filter.value.building || undefined,
  })
}

// 템플릿 변수 삽입 헬퍼
const insertVariable = (variableTag: string) => {
  if (!form.value.content || form.value.content === '<p><br></p>') {
    form.value.content = `<p>${variableTag}</p>`
  } else if (form.value.content.endsWith('</p>')) {
    form.value.content = form.value.content.replace(/<\/p>$/, `&nbsp;${variableTag}</p>`)
  } else {
    form.value.content += ` ${variableTag} `
  }
}

// 이메일 발송 실행
const isSending = ref(false)
const handleSendEmail = async () => {
  if (!project.value) {
    alert('프로젝트를 선택해 주세요.')
    return
  }
  if (!form.value.title.trim()) {
    alert('이메일 제목을 입력해 주세요.')
    return
  }
  if (!form.value.content.trim()) {
    alert('이메일 본문을 입력해 주세요.')
    return
  }
  const regCount = finalRecipients.value.length
  if (regCount === 0) {
    alert('선택된 유효한 수신자가 없습니다. 수신 대상자 목록에서 이메일을 확인해 주세요.')
    return
  }

  const confirmMsg = `총 ${regCount}명의 수신자에게 이메일을 발송하시겠습니까?\n발송 후에는 취소할 수 없습니다.`
  if (!confirm(confirmMsg)) return

  isSending.value = true
  try {
    const customList = finalRecipients.value.map(r => ({
      contractor_id: r.contractor_id,
      name: r.name,
      email: r.email.trim(),
      unit_info: r.unit_info,
    }))

    await noticeStore.sendEmailNotice({
      project: project.value,
      title: form.value.title.trim(),
      content: form.value.content,
      sender_name: form.value.sender_name.trim(),
      sender_email: form.value.sender_email.trim(),
      order_group: filter.value.order_group || undefined,
      building: filter.value.building || undefined,
      custom_recipients: customList,
    })
    // 폼 초기화 및 이력 탭으로 전환
    form.value.title = ''
    form.value.content = ''
    activeTab.value = 'history'
    await fetchHistory()
  } finally {
    isSending.value = false
  }
}

// ── 2. 발송 이력 상태 ──
const historyList = computed(() => noticeStore.emailNotices)
const historyCount = computed(() => noticeStore.emailNoticesCount)
const historyStatusFilter = ref('')

const fetchHistory = async () => {
  if (!project.value) return
  await noticeStore.fetchEmailNotices({
    project: project.value,
    status: historyStatusFilter.value || undefined,
  })
}

// 이력 상세 모달
const showDetailModal = ref(false)
const showRawHtml = ref(false)
const selectedNotice = computed(() => noticeStore.currentEmailNotice)

// 템플릿 변수를 시각적으로 돋보이게 스타일링한 HTML 반환
const formattedPreviewContent = computed(() => {
  const content = selectedNotice.value?.content || ''
  if (!content) return ''
  // {{ 변수 }} 머지 태그를 스타일이 적용된 뱃지 형태로 치환하여 미리보기 제공
  return content.replace(
    /(\{\{\s*[^}]+\s*\}\})/g,
    '<span class="badge bg-primary bg-opacity-10 text-primary border border-primary border-opacity-25 px-1 py-0 rounded font-monospace">$1</span>',
  )
})

const openDetail = async (noticeItem: EmailNotice) => {
  showRawHtml.value = false
  await noticeStore.fetchEmailNoticeDetail(noticeItem.id)
  showDetailModal.value = true
}

// 프로젝트 변경 시 재조회
watch(
  () => project.value,
  async newProj => {
    if (newProj) {
      loading.value = true
      try {
        await Promise.all([
          contractStore.fetchOrderGroupList(newProj),
          pDataStore.fetchBuildingList(newProj),
        ])
        if (activeTab.value === 'write') {
          await fetchRecipients()
        } else {
          await fetchHistory()
        }
      } finally {
        loading.value = false
      }
    }
  },
)

watch(
  () => activeTab.value,
  async newTab => {
    if (newTab === 'write') {
      await fetchRecipients()
    } else {
      await fetchHistory()
    }
  },
)

onBeforeMount(async () => {
  if (project.value) {
    loading.value = true
    try {
      await Promise.all([
        contractStore.fetchOrderGroupList(project.value),
        pDataStore.fetchBuildingList(project.value),
      ])
      await fetchRecipients()
    } finally {
      loading.value = false
    }
  }
})

// 상태 뱃지 색상
const getStatusBadgeColor = (status: string) => {
  switch (status) {
    case 'completed':
      return 'success'
    case 'sending':
      return 'info'
    case 'failed':
      return 'danger'
    default:
      return 'secondary'
  }
}
</script>

<template>
  <Loading v-model:active="loading" />

  <ContentHeader :page-title="pageTitle" :nav-menu="navMenu" selector="ProjectSelect" />

  <ContentBody>
    <NoticeAuthGuard :is-authorized="canNoticeRead">
      <!-- 메인 탭 (새 이메일 작성 및 발송 / 이메일 발송 이력 대장) -->
      <CCol class="mb-3">
        <CCardHeader>
          <CRow class="mt-3">
            <CCol>
              <v-tabs density="compact">
                <v-tab :active="activeTab === 'write'" variant="tonal" @click="activeTab = 'write'">
                  <v-icon icon="mdi-email-edit-outline" size="small" class="me-1" />
                  새 이메일 작성 및 발송
                </v-tab>
                <v-tab
                  :active="activeTab === 'history'"
                  variant="tonal"
                  :disabled="!canNoticeRead"
                  @click="activeTab = 'history'"
                >
                  <v-icon icon="mdi-history" size="small" class="me-1" />
                  이메일 발송 이력 대장
                  <v-chip
                    v-if="historyCount > 0"
                    color="primary"
                    shape="rounded-pill"
                    class="ms-1"
                    variant="flat"
                    size="x-small"
                  >
                    {{ historyCount }}
                  </v-chip>
                </v-tab>
              </v-tabs>
            </CCol>
          </CRow>
        </CCardHeader>

        <CCardBody>
          <!-- ═══════════════════════════════════════════════════
           TAB 1: 새 이메일 작성 및 발송
           ═══════════════════════════════════════════════════ -->
          <CCol v-if="activeTab === 'write'">
            <CRow class="row g-4">
              <!-- 좌측: 대상자 타겟팅 및 집계 카드 -->
              <CCol class="col-12 col-lg-4">
                <CCard class="shadow-sm mb-3">
                  <CCardHeader class="bg-light fw-bold py-2 d-flex align-items-center">
                    <v-icon icon="mdi-target-account" size="small" class="me-1 text-primary" />
                    발송 대상자 타겟팅
                  </CCardHeader>
                  <CCardBody>
                    <!-- 차수 선택 -->
                    <div class="mb-3">
                      <label class="form-label small fw-bold text-secondary">차수 선택</label>
                      <CFormSelect v-model="filter.order_group" @change="fetchRecipients">
                        <option value="">전체 차수</option>
                        <option v-for="og in orderGroups" :key="og.pk" :value="og.pk">
                          {{ og.name }}
                        </option>
                      </CFormSelect>
                    </div>

                    <!-- 동 선택 -->
                    <div class="mb-3">
                      <label class="form-label small fw-bold text-secondary">동 선택</label>
                      <CFormSelect v-model="filter.building" @change="fetchRecipients">
                        <option value="">전체 동</option>
                        <option v-for="bldg in buildingList" :key="bldg.pk" :value="bldg.pk">
                          {{ bldg.name }}동
                        </option>
                      </CFormSelect>
                    </div>

                    <hr class="my-3 text-muted" />

                    <!-- 수신 현황 통계 카드 -->
                    <div class="p-3 bg-light rounded-3 border">
                      <div class="d-flex justify-content-between align-items-center mb-3">
                        <span class="fw-bold">수신 대상자 설정</span>
                        <v-btn
                          color="primary"
                          variant="tonal"
                          size="small"
                          @click="showRecipientManageModal = true"
                        >
                          <v-icon icon="mdi-account-cog-outline" size="small" class="me-1" />
                          명단 확인 / 수정
                        </v-btn>
                      </div>

                      <div class="d-flex justify-content-between align-items-center mb-2">
                        <span>총 대상 계약자</span>
                        <strong class="font-monospace">
                          {{ recipientsData?.total_contractors || 0 }}명
                        </strong>
                      </div>
                      <div class="d-flex justify-content-between align-items-center mb-2">
                        <span>초기 등록자</span>
                        <span class="text-secondary font-monospace">
                          {{ recipientsData?.registered_count || 0 }}명
                        </span>
                      </div>
                      <div class="d-flex justify-content-between align-items-center mb-2">
                        <span class="fw-bold text-primary">최종 발송 예정</span>
                        <v-chip color="primary" shape="rounded-pill" variant="flat" size="small">
                          <strong>{{ finalRecipients.length }}명</strong>
                        </v-chip>
                      </div>

                      <div
                        v-if="(recipientsData?.unregistered_count || 0) > 0"
                        class="mt-3 text-end"
                      >
                        <v-btn
                          color="secondary"
                          variant="text"
                          size="small"
                          class="text-decoration-none p-0 small"
                          @click="showUnregisteredModal = true"
                        >
                          <v-icon icon="mdi-account-alert-outline" size="small" />
                          미등록자 명단 ({{ recipientsData?.unregistered_count || 0 }}명)
                        </v-btn>
                      </div>
                    </div>
                  </CCardBody>
                </CCard>

                <!-- 변수 치환 도우미 카드 -->
                <CCard class="shadow-sm">
                  <CCardHeader class="bg-light fw-bold py-2 d-flex align-items-center">
                    <v-icon icon="mdi-code-tags" size="small" class="me-1 text-primary" />
                    자동 치환 머지 태그
                  </CCardHeader>
                  <CCardBody class="small text-secondary">
                    <p class="mb-2">
                      본문 작성 시 클릭하면 해당 위치에 태그가 삽입되어 발송 시 계약자 정보로 자동
                      치환됩니다.
                    </p>
                    <div class="d-flex flex-wrap gap-1">
                      <v-btn
                        color="primary"
                        variant="outlined"
                        size="small"
                        class="font-monospace"
                        @click="insertVariable('{{ 계약자명 }}')"
                      >
                        + &#123;&#123; 계약자명 &#125;&#125;
                      </v-btn>
                      <v-btn
                        color="primary"
                        variant="outlined"
                        size="small"
                        class="font-monospace"
                        @click="insertVariable('{{ 동호수 }}')"
                      >
                        + &#123;&#123; 동호수 &#125;&#125;
                      </v-btn>
                      <v-btn
                        color="primary"
                        variant="outlined"
                        size="small"
                        class="font-monospace"
                        @click="insertVariable('{{ 프로젝트명 }}')"
                      >
                        + &#123;&#123; 프로젝트명 &#125;&#125;
                      </v-btn>
                    </div>
                  </CCardBody>
                </CCard>
              </CCol>

              <!-- 우측: 이메일 작성 폼 -->
              <div class="col-12 col-lg-8">
                <CCard class="shadow-sm">
                  <CCardHeader
                    class="bg-light fw-bold py-2 d-flex justify-content-between align-items-center"
                  >
                    <div class="d-flex align-items-center">
                      <v-icon icon="mdi-email-outline" size="small" class="me-1 text-primary" />
                      이메일 내용 작성
                    </div>
                    <div class="small text-muted">
                      예상 수신인:
                      <strong class="text-primary">
                        {{ recipientsData?.registered_count || 0 }}명
                      </strong>
                    </div>
                  </CCardHeader>

                  <CCardBody>
                    <!-- 발신자 정보 -->
                    <div class="row g-2 mb-3">
                      <div class="col-12 col-md-6">
                        <label class="form-label small fw-bold text-secondary">발신자 명</label>
                        <CFormInput v-model="form.sender_name" placeholder="예: IBS 분양사무소" />
                      </div>
                      <div class="col-12 col-md-6">
                        <label class="form-label small fw-bold text-secondary">
                          발신 이메일 주소
                        </label>
                        <CFormInput
                          v-model="form.sender_email"
                          type="email"
                          placeholder="미입력 시 시스템 기본 발신 주소 사용"
                        />
                      </div>
                    </div>

                    <!-- 이메일 제목 -->
                    <div class="mb-3">
                      <label class="form-label small fw-bold text-secondary required">
                        이메일 제목
                      </label>
                      <CFormInput
                        v-model="form.title"
                        placeholder="계약자 안내 공지 제목을 입력하세요."
                      />
                    </div>

                    <!-- 이메일 본문 (에디터) -->
                    <div class="mb-4">
                      <label class="form-label small fw-bold text-secondary">
                        이메일 본문 <span class="text-danger">*</span>
                      </label>
                      <QuillEditor
                        v-model:content="form.content"
                        :height="350"
                        placeholder="계약자에게 안내할 내용을 작성하세요. 상단 툴바를 통해 서식 및 정렬을 지정할 수 있습니다."
                      />
                    </div>

                    <!-- 하단 액션 버튼 -->
                    <div
                      class="d-flex justify-content-end align-items-center gap-2 border-top pt-3"
                    >
                      <span class="text-muted small me-2">
                        선택된 수신자
                        <strong>{{ finalRecipients.length }}</strong>
                        명에게 비동기(Celery) 대량 전송됩니다.
                      </span>
                      <v-btn
                        color="primary"
                        :disabled="isSending || finalRecipients.length === 0"
                        @click="handleSendEmail"
                      >
                        <v-icon icon="mdi-send" size="small" class="me-1" />
                        {{
                          isSending
                            ? '발송 접수 중...'
                            : `이메일 발송 실행 (${finalRecipients.length}명)`
                        }}
                      </v-btn>
                    </div>
                  </CCardBody>
                </CCard>
              </div>
            </CRow>
          </CCol>

          <!-- ═══════════════════════════════════════════════════
               TAB 2: 이메일 발송 이력 대장
               ═══════════════════════════════════════════════════ -->
          <CCol v-else-if="activeTab === 'history'">
            <CCard class="shadow-sm">
              <CCardHeader
                class="bg-more-light py-2 d-flex justify-content-between align-items-center"
              >
                <div class="fw-bold d-flex align-items-center">
                  <v-icon icon="mdi-history" size="small" class="me-1 text-primary" />
                  발송 이력 목록
                  <v-chip
                    color="primary"
                    variant="flat"
                    size="x-small"
                    shape="rounded-pill"
                    class="ms-2"
                  >
                    {{ historyList.length }}건
                  </v-chip>
                </div>

                <!-- 상태 필터 -->
                <div class="d-flex align-items-center gap-2">
                  <CFormSelect
                    v-model="historyStatusFilter"
                    size="sm"
                    style="width: 140px"
                    @change="fetchHistory"
                  >
                    <option value="">전체 상태</option>
                    <option value="completed">발송 완료</option>
                    <option value="sending">발송 중</option>
                    <option value="failed">발송 실패</option>
                  </CFormSelect>
                  <v-btn color="secondary" variant="outlined" size="small" @click="fetchHistory">
                    <v-icon icon="mdi-refresh" size="small" />
                  </v-btn>
                </div>
              </CCardHeader>

              <CCardBody class="p-0 table-responsive">
                <CTable hover align="middle" class="mb-0 text-center small">
                  <CTableHead color="light">
                    <CTableRow>
                      <CTableHeaderCell style="width: 60px">No</CTableHeaderCell>
                      <CTableHeaderCell style="width: 150px">등록/발송 일시</CTableHeaderCell>
                      <CTableHeaderCell class="text-start">메일 제목</CTableHeaderCell>
                      <CTableHeaderCell style="width: 120px">발송자</CTableHeaderCell>
                      <CTableHeaderCell style="width: 90px">총 대상</CTableHeaderCell>
                      <CTableHeaderCell style="width: 90px">성공</CTableHeaderCell>
                      <CTableHeaderCell style="width: 90px">실패</CTableHeaderCell>
                      <CTableHeaderCell style="width: 110px">상태</CTableHeaderCell>
                      <CTableHeaderCell style="width: 100px">상세</CTableHeaderCell>
                    </CTableRow>
                  </CTableHead>

                  <CTableBody>
                    <template v-if="historyList.length > 0">
                      <CTableRow v-for="(item, idx) in historyList" :key="item.id">
                        <CTableDataCell class="text-muted">{{ idx + 1 }}</CTableDataCell>
                        <CTableDataCell class="font-monospace">
                          {{ item.created ? item.created.substring(0, 16).replace('T', ' ') : '-' }}
                        </CTableDataCell>
                        <CTableDataCell class="text-start fw-bold">
                          {{ item.title }}
                        </CTableDataCell>
                        <CTableDataCell>{{ item.sent_by?.username || '-' }}</CTableDataCell>
                        <CTableDataCell class="font-monospace fw-bold">
                          {{ item.total_recipients }}명
                        </CTableDataCell>
                        <CTableDataCell class="font-monospace text-success fw-bold">
                          {{ item.success_count }}
                        </CTableDataCell>
                        <CTableDataCell class="font-monospace text-danger fw-bold">
                          {{ item.fail_count }}
                        </CTableDataCell>
                        <CTableDataCell>
                          <v-chip
                            :color="getStatusBadgeColor(item.status)"
                            shape="rounded-pill"
                            variant="flat"
                            size="x-small"
                          >
                            {{ item.status_display }}
                          </v-chip>
                        </CTableDataCell>
                        <CTableDataCell>
                          <v-btn
                            color="primary"
                            variant="tonal"
                            size="small"
                            @click="openDetail(item)"
                          >
                            상세보기
                          </v-btn>
                        </CTableDataCell>
                      </CTableRow>
                    </template>
                    <template v-else>
                      <CTableRow>
                        <CTableDataCell colspan="9" class="py-5 text-muted">
                          발송된 이메일 이력이 없습니다.
                        </CTableDataCell>
                      </CTableRow>
                    </template>
                  </CTableBody>
                </CTable>
              </CCardBody>
            </CCard>
          </CCol>
        </CCardBody>
      </CCol>

      <!-- ═══════════════════════════════════════════════════
           MODAL 0: 수신 대상자 명단 확인 / 이메일 수정 모달
           ═══════════════════════════════════════════════════ -->
      <CModal
        :visible="showRecipientManageModal"
        size="xl"
        scrollable
        @close="showRecipientManageModal = false"
      >
        <CModalHeader>
          <CModalTitle>
            <v-icon icon="mdi-account-cog" class="me-1 text-primary" />
            수신 대상자 명단 확인 및 이메일 수정 / 설정
          </CModalTitle>
        </CModalHeader>
        <CModalBody class="p-3">
          <!-- 상단 필터 & 직접 추가 영역 -->
          <div class="p-3 bg-light rounded border mb-3">
            <div class="row g-2 align-items-center">
              <div class="col-12 col-md-5">
                <CInputGroup size="sm">
                  <CInputGroupText>
                    <v-icon icon="mdi-magnify" size="small" />
                  </CInputGroupText>
                  <CFormInput
                    v-model="recipientSearch"
                    placeholder="계약자명 / 동호수 / 이메일 검색..."
                  />
                  <CButton
                    v-if="recipientSearch"
                    color="secondary"
                    variant="ghost"
                    type="button"
                    @click="recipientSearch = ''"
                  >
                    초기화
                  </CButton>
                </CInputGroup>
              </div>

              <!-- 직접 추가 인라인 폼 -->
              <div class="col-12 col-md-7">
                <div class="d-flex gap-2 justify-content-md-end">
                  <CFormInput
                    v-model="manualName"
                    size="sm"
                    style="max-width: 120px"
                    placeholder="성명/직책"
                  />
                  <CFormInput
                    v-model="manualEmail"
                    size="sm"
                    type="email"
                    style="max-width: 220px"
                    placeholder="추가할 이메일 주소"
                    @keydown.enter="addManualRecipient"
                  />
                  <v-btn color="primary" variant="tonal" size="small" @click="addManualRecipient">
                    <v-icon icon="mdi-plus" size="small" class="me-1" />
                    수기 추가
                  </v-btn>
                </div>
              </div>
            </div>
          </div>

          <!-- 상태 요약 안내 바 -->
          <div class="d-flex justify-content-between align-items-center px-1 mb-2 small">
            <div class="text-secondary">
              전체 <strong>{{ editableRecipients.length }}</strong
              >명 중
              <span class="text-primary fw-bold">{{ finalRecipients.length }}명 발송 선택됨</span>
              (검색 필터 결과: {{ filteredEditableRecipients.length }}명)
            </div>
            <div class="text-muted">
              ※ 이메일 입력창에서 주소를 직접 수정하거나 입력할 수 있습니다.
            </div>
          </div>

          <!-- 대상자 테이블 -->
          <div class="table-responsive border rounded" style="max-height: 50vh; overflow-y: auto">
            <CTable hover align="middle" class="mb-0 text-center small">
              <CTableHead color="light" class="position-sticky top-0" style="z-index: 2">
                <CTableRow>
                  <CTableHeaderCell style="width: 45px">
                    <CFormCheck
                      v-model="isAllFilteredSelected"
                      title="현재 검색 목록 전체 선택/해제"
                    />
                  </CTableHeaderCell>
                  <CTableHeaderCell style="width: 50px">No</CTableHeaderCell>
                  <CTableHeaderCell style="width: 120px">차수</CTableHeaderCell>
                  <CTableHeaderCell style="width: 130px">동 / 호수</CTableHeaderCell>
                  <CTableHeaderCell style="width: 130px">수신자명</CTableHeaderCell>
                  <CTableHeaderCell class="text-start"
                    >이메일 주소 (직접 수정 가능)</CTableHeaderCell
                  >
                  <CTableHeaderCell style="width: 100px">상태</CTableHeaderCell>
                </CTableRow>
              </CTableHead>
              <CTableBody>
                <template v-if="filteredEditableRecipients.length > 0">
                  <CTableRow
                    v-for="(r, idx) in filteredEditableRecipients"
                    :key="r.contractor_id ?? `custom-${idx}`"
                    :class="{ 'table-active': !r.selected }"
                  >
                    <CTableDataCell>
                      <input v-model="r.selected" type="checkbox" class="form-check-input" />
                    </CTableDataCell>
                    <CTableDataCell class="text-muted">{{ idx + 1 }}</CTableDataCell>
                    <CTableDataCell>{{ r.order_group_name }}</CTableDataCell>
                    <CTableDataCell class="fw-bold">{{ r.unit_info || '-' }}</CTableDataCell>
                    <CTableDataCell class="fw-bold">
                      {{ r.name }}
                      <v-chip
                        v-if="r.is_custom"
                        color="info"
                        size="x-small"
                        variant="outlined"
                        class="ms-1"
                      >
                        직접추가
                      </v-chip>
                    </CTableDataCell>
                    <CTableDataCell class="text-start">
                      <CFormInput
                        v-model="r.email"
                        size="sm"
                        type="email"
                        placeholder="이메일을 입력하세요 (미입력 시 발송 불가)"
                        :class="{ 'border-danger': r.selected && !r.email.trim() }"
                      />
                    </CTableDataCell>
                    <CTableDataCell>
                      <template v-if="r.is_custom">
                        <v-btn
                          color="danger"
                          variant="text"
                          size="x-small"
                          @click="removeManualRecipient(idx)"
                        >
                          삭제
                        </v-btn>
                      </template>
                      <template v-else-if="r.email.trim()">
                        <CBadge color="success" shape="rounded-pill">발송가능</CBadge>
                      </template>
                      <template v-else>
                        <CBadge color="secondary" shape="rounded-pill">미입력</CBadge>
                      </template>
                    </CTableDataCell>
                  </CTableRow>
                </template>
                <template v-else>
                  <CTableRow>
                    <CTableDataCell colspan="7" class="py-4 text-muted">
                      검색 조건에 맞는 수신 대상자가 없습니다.
                    </CTableDataCell>
                  </CTableRow>
                </template>
              </CTableBody>
            </CTable>
          </div>
        </CModalBody>
        <CModalFooter class="d-flex justify-content-between">
          <div class="small text-secondary">
            최종 발송 예정: <strong class="text-primary">{{ finalRecipients.length }}</strong
            >명
          </div>
          <v-btn color="primary" size="small" flat @click="showRecipientManageModal = false">
            설정 완료
          </v-btn>
        </CModalFooter>
      </CModal>

      <!-- ═══════════════════════════════════════════════════
           MODAL 1: 이메일 미등록 계약자 명단 모달
           ═══════════════════════════════════════════════════ -->
      <CModal
        :visible="showUnregisteredModal"
        size="lg"
        scrollable
        @close="showUnregisteredModal = false"
      >
        <CModalHeader>
          <CModalTitle>
            <v-icon icon="mdi-account-alert" class="me-1 text-warning" />
            이메일 미등록 계약자 명단 ({{ recipientsData?.unregistered_count || 0 }}명)
          </CModalTitle>
        </CModalHeader>
        <CModalBody class="p-0">
          <div class="p-3 bg-light border-bottom small text-secondary">
            이메일 주소가 등록되지 않아 이번 발송에서 제외되는 계약자입니다. SMS 또는 서면 우편
            발송을 통해 안내해 주세요.
          </div>
          <CTable hover align="middle" class="mb-0 text-center small">
            <CTableHead color="light">
              <CTableRow>
                <CTableHeaderCell style="width: 50px">No</CTableHeaderCell>
                <CTableHeaderCell>차수</CTableHeaderCell>
                <CTableHeaderCell>동 / 호수</CTableHeaderCell>
                <CTableHeaderCell>계약자명</CTableHeaderCell>
              </CTableRow>
            </CTableHead>
            <CTableBody>
              <CTableRow
                v-for="(unreg, uIdx) in recipientsData?.unregistered_contractors || []"
                :key="unreg.contractor_id"
              >
                <CTableDataCell class="text-muted">{{ uIdx + 1 }}</CTableDataCell>
                <CTableDataCell>{{ unreg.order_group_name || '-' }}</CTableDataCell>
                <CTableDataCell class="fw-bold">{{ unreg.unit_info || '-' }}</CTableDataCell>
                <CTableDataCell class="fw-bold">{{ unreg.name }}</CTableDataCell>
              </CTableRow>
            </CTableBody>
          </CTable>
        </CModalBody>
        <CModalFooter>
          <v-btn color="light" size="small" flat @click="showUnregisteredModal = false">닫기</v-btn>
        </CModalFooter>
      </CModal>

      <!-- ═══════════════════════════════════════════════════
           MODAL 2: 이메일 발송 상세 및 수신자별 로그 모달
           ═══════════════════════════════════════════════════ -->
      <CModal
        :visible="showDetailModal"
        size="xl"
        scrollable
        @close="showDetailModal = false"
        alignment="center"
      >
        <CModalHeader>
          <CModalTitle>
            <v-icon icon="mdi-email-check" class="me-1 text-primary" />
            이메일 발송 상세 내역
          </CModalTitle>
        </CModalHeader>
        <CModalBody v-if="selectedNotice">
          <!-- 메일 기본 정보 요약 -->
          <div class="row g-2 mb-4 p-3 bg-light rounded border small">
            <div class="col-12 col-md-8"><strong>제목:</strong> {{ selectedNotice.title }}</div>
            <div class="col-12 col-md-4 text-md-end">
              <strong>상태:</strong>
              <v-chip
                :color="getStatusBadgeColor(selectedNotice.status)"
                class="ms-1"
                variant="flat"
                size="x-small"
              >
                {{ selectedNotice.status_display }}
              </v-chip>
            </div>
            <div class="col-12 col-md-6 text-muted">
              발신자: {{ selectedNotice.sender_name || '-' }} &lt;{{
                selectedNotice.sender_email || '기본 주소'
              }}&gt;
            </div>
            <div class="col-12 col-md-6 text-md-end text-muted">
              등록:
              {{
                selectedNotice.created
                  ? selectedNotice.created.substring(0, 19).replace('T', ' ')
                  : '-'
              }}
            </div>
            <div class="col-12">
              <span class="fw-bold text-secondary">발송 통계:</span>
              총 {{ selectedNotice.total_recipients }}명 /
              <span class="text-success fw-bold">성공 {{ selectedNotice.success_count }}건</span> /
              <span class="text-danger fw-bold">실패 {{ selectedNotice.fail_count }}건</span>
            </div>
          </div>

          <!-- 본문 미리보기 아코디언 -->
          <CAccordion class="mb-4">
            <CAccordionItem :item-key="1">
              <CAccordionHeader>
                <div class="d-flex justify-content-between align-items-center w-100 pe-3">
                  <span class="small fw-bold">
                    <v-icon icon="mdi-file-document-outline" size="small" class="me-1 text-primary" />
                    발송 본문 서식 미리보기 (HTML)
                  </span>
                </div>
              </CAccordionHeader>
              <CAccordionBody>
                <div class="d-flex justify-content-end mb-2">
                  <v-btn
                    color="secondary"
                    variant="text"
                    size="x-small"
                    @click="showRawHtml = !showRawHtml"
                  >
                    <v-icon :icon="showRawHtml ? 'mdi-eye-outline' : 'mdi-code-tags'" size="small" class="me-1" />
                    {{ showRawHtml ? '서식 미리보기로 보기' : 'HTML 원문 코드 보기' }}
                  </v-btn>
                </div>

                <!-- HTML 서식 렌더링 뷰 (실제 수신자 메일 화면과 동일한 스타일) -->
                <div
                  v-if="!showRawHtml"
                  class="p-4 bg-white border rounded small email-rendered-view"
                  style="min-height: 120px; line-height: 1.6"
                  v-html="formattedPreviewContent"
                />

                <!-- 개발/검토용 원문 HTML 코드 뷰 -->
                <div
                  v-else
                  class="p-3 bg-light border rounded small font-monospace text-secondary"
                  style="white-space: pre-wrap; word-break: break-all"
                >
                  {{ selectedNotice.content }}
                </div>
              </CAccordionBody>
            </CAccordionItem>
          </CAccordion>

          <!-- 수신자별 전송 로그 테이블 -->
          <div class="fw-bold mb-2 small text-secondary">
            수신자별 전송 결과 ({{ selectedNotice.send_logs?.length || 0 }}건)
          </div>
          <CTable hover align="middle" class="mb-0 text-center small border">
            <CTableHead color="light">
              <CTableRow>
                <CTableHeaderCell style="width: 50px">No</CTableHeaderCell>
                <CTableHeaderCell style="width: 130px">동호수</CTableHeaderCell>
                <CTableHeaderCell style="width: 120px">계약자명</CTableHeaderCell>
                <CTableHeaderCell class="text-start">수신 이메일</CTableHeaderCell>
                <CTableHeaderCell style="width: 90px">결과</CTableHeaderCell>
                <CTableHeaderCell class="text-start">실패 사유 / 오류</CTableHeaderCell>
              </CTableRow>
            </CTableHead>
            <CTableBody>
              <CTableRow v-for="(log, lIdx) in selectedNotice.send_logs || []" :key="log.id">
                <CTableDataCell class="text-muted">{{ lIdx + 1 }}</CTableDataCell>
                <CTableDataCell>{{ log.unit_info || '-' }}</CTableDataCell>
                <CTableDataCell class="fw-bold">{{ log.recipient_name }}</CTableDataCell>
                <CTableDataCell class="text-start font-monospace">
                  {{ log.recipient_email }}
                </CTableDataCell>
                <CTableDataCell>
                  <v-chip
                    :color="
                      log.status === 'success'
                        ? 'success'
                        : log.status === 'fail'
                          ? 'danger'
                          : 'secondary'
                    "
                    variant="flat"
                    size="x-small"
                  >
                    {{
                      log.status === 'success' ? '성공' : log.status === 'fail' ? '실패' : '대기'
                    }}
                  </v-chip>
                </CTableDataCell>
                <CTableDataCell class="text-start text-danger small">
                  {{ log.error_message || '-' }}
                </CTableDataCell>
              </CTableRow>
            </CTableBody>
          </CTable>
        </CModalBody>
        <CModalFooter>
          <v-btn color="light" size="small" flat @click="showDetailModal = false">닫기</v-btn>
        </CModalFooter>
      </CModal>
    </NoticeAuthGuard>
  </ContentBody>
</template>
