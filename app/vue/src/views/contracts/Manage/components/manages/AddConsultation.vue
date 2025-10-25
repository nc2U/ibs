<script lang="ts" setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useContract } from '@/store/pinia/contract.ts'
import type { ConsultationLog } from '@/store/types/contract'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import { CCardBody } from '@coreui/vue'
import { cutString } from '@/utils/baseMixins.ts'

const route = useRoute()
const contStore = useContract()

// 계약자 ID
const contractorId = computed(() =>
  route.params.contractorId ? parseInt(route.params.contractorId as string, 10) : null,
)

// Store 데이터
const consultationLogList = computed(() => contStore.consultationLogList)
const pagination = computed(() => contStore.consultationLogPagination)

// 로딩 상태
const isLoading = ref(false)

// 폼 데이터
const formData = ref<Partial<ConsultationLog>>({
  consultation_date: new Date().toISOString().split('T')[0],
  channel: 'phone',
  category: 'question',
  title: '',
  content: '',
  status: '1',
  priority: 'normal',
  follow_up_required: false,
  follow_up_note: '',
  completion_date: null,
  is_important: false,
})

// 폼 제출
const submitForm = async () => {
  if (!contractorId.value) return
  if (!(formData.value.title as string)?.trim()) {
    alert('상담 제목을 입력해주세요.')
    return
  }

  try {
    await contStore.createConsultationLog({
      ...formData.value,
      contractor: contractorId.value,
    })
    resetForm()
  } catch (error) {
    console.error('상담 내역 등록 실패:', error)
  }
}

// 폼 초기화
const resetForm = () => {
  formData.value = {
    consultation_date: new Date().toISOString().split('T')[0],
    channel: 'phone',
    category: 'question',
    title: '',
    content: '',
    status: '1',
    priority: 'normal',
    follow_up_required: false,
    follow_up_note: '',
    completion_date: null,
    is_important: false,
  }
}

// 필터 상태
const statusFilter = ref<string>('')

// 필터링된 리스트
const filteredList = computed(() => {
  if (!statusFilter.value) return consultationLogList.value
  return consultationLogList.value.filter(log => log.status === statusFilter.value)
})

// 확장된 행 추적
const expandedRow = ref<number | null>(null)

// 행 확장 토글
const toggleRow = (pk: number) => {
  expandedRow.value = expandedRow.value === pk ? null : pk
}

// 수정 모드
const editingLog = ref<ConsultationLog | null>(null)

// 수정 시작
const startEdit = (log: ConsultationLog) => {
  editingLog.value = { ...log }
}

// 수정 취소
const cancelEdit = () => {
  editingLog.value = null
  expandedRow.value = null
}

// 수정 저장
const saveEdit = async () => {
  if (!editingLog.value || !editingLog.value.pk) return

  try {
    await contStore.updateConsultationLog(editingLog.value.pk, editingLog.value)
    editingLog.value = null
    expandedRow.value = null
  } catch (error) {
    console.error('수정 실패:', error)
  }
}

// 삭제
const deleteLog = async (pk: number) => {
  if (!contractorId.value) return
  if (!confirm('상담 내역을 삭제하시겠습니까?')) return

  try {
    await contStore.deleteConsultationLog(pk, contractorId.value)
  } catch (error) {
    console.error('삭제 실패:', error)
  }
}

// 페이지 변경
const onPageChange = (page: number) => {
  if (!contractorId.value) return
  loadData(page)
}

// 데이터 로드
const loadData = async (page = 1) => {
  if (!contractorId.value) return

  try {
    isLoading.value = true
    await contStore.fetchConsultationLogs(contractorId.value, {
      page,
      status: statusFilter.value || undefined,
    })
  } catch (error) {
    console.error('데이터 로드 실패:', error)
  } finally {
    isLoading.value = false
  }
}

// 상태별 색상
const getStatusColor = (status: string) => {
  switch (status) {
    case '1':
      return 'warning'
    case '2':
      return 'primary'
    case '3':
      return 'success'
    case '4':
      return 'secondary'
    default:
      return 'default'
  }
}

// 상태 필터 변경 시 데이터 새로고침
watch(statusFilter, () => {
  if (contractorId.value) {
    loadData(1)
  }
})

// Watch: contractorId 변경 시 데이터 로드
watch(
  contractorId,
  newId => {
    if (newId) {
      loadData()
    } else {
      contStore.consultationLogList = []
    }
  },
  { immediate: true },
)

onMounted(() => {
  if (contractorId.value) {
    loadData()
  }
})
</script>

<template>
  <CCardBody>
    <!-- 인라인 등록 폼 -->
    <CCard class="mb-3">
      <CCardBody>
        <CRow class="g-2">
          <CCol :md="4">
            <CFormLabel>상담일자</CFormLabel>
            <DatePicker v-model="formData.consultation_date" />
          </CCol>
          <CCol :md="2">
            <CFormLabel>채널</CFormLabel>
            <CFormSelect v-model="formData.channel" size="sm">
              <option value="visit">방문</option>
              <option value="phone">전화</option>
              <option value="email">이메일</option>
              <option value="sms">문자</option>
              <option value="kakao">카카오톡</option>
              <option value="other">기타</option>
            </CFormSelect>
          </CCol>
          <CCol :md="2">
            <CFormLabel>유형</CFormLabel>
            <CFormSelect v-model="formData.category" size="sm">
              <option value="payment">납부상담</option>
              <option value="contract">계약상담</option>
              <option value="change">변경상담</option>
              <option value="complaint">민원/불만</option>
              <option value="question">문의</option>
              <option value="succession">승계상담</option>
              <option value="release">해지상담</option>
              <option value="document">서류관련</option>
              <option value="etc">기타</option>
            </CFormSelect>
          </CCol>
          <CCol :md="2">
            <CFormLabel>처리상태</CFormLabel>
            <CFormSelect v-model="formData.status" size="sm">
              <option value="1">처리대기</option>
              <option value="2">처리중</option>
              <option value="3">처리완료</option>
              <option value="4">보류</option>
            </CFormSelect>
          </CCol>
          <CCol :md="2">
            <CFormLabel>중요도</CFormLabel>
            <CFormSelect v-model="formData.priority" size="sm">
              <option value="low">낮음</option>
              <option value="normal">보통</option>
              <option value="high">높음</option>
              <option value="urgent">긴급</option>
            </CFormSelect>
          </CCol>
        </CRow>
        <CRow class="g-2 mt-0">
          <CCol :md="12">
            <CFormInput v-model="formData.title" size="sm" placeholder="상담 제목" />
          </CCol>

          <CCol :md="12">
            <CFormTextarea v-model="formData.content" rows="3" placeholder="상담 내용" />
          </CCol>
        </CRow>

        <CRow class="mt-3">
          <CCol class="text-end">
            <v-btn color="primary" size="small" @click="submitForm">
              <v-icon icon="mdi-plus" size="18" class="me-1" />
              등록
            </v-btn>
          </CCol>
        </CRow>
      </CCardBody>
    </CCard>

    <!-- 필터 영역 -->
    <div class="mb-3 d-flex gap-2">
      <v-chip
        :color="statusFilter === '' ? 'primary' : 'default'"
        @click="statusFilter = ''"
        size="small"
      >
        전체
      </v-chip>
      <v-chip
        :color="statusFilter === '1' ? 'warning' : 'default'"
        @click="statusFilter = '1'"
        size="small"
      >
        처리대기
      </v-chip>
      <v-chip
        :color="statusFilter === '2' ? 'primary' : 'default'"
        @click="statusFilter = '2'"
        size="small"
      >
        처리중
      </v-chip>
      <v-chip
        :color="statusFilter === '3' ? 'success' : 'default'"
        @click="statusFilter = '3'"
        size="small"
      >
        처리완료
      </v-chip>
      <v-chip
        :color="statusFilter === '4' ? 'secondary' : 'default'"
        @click="statusFilter = '4'"
        size="small"
      >
        보류
      </v-chip>
    </div>

    <!-- 로딩 상태 -->
    <div v-if="isLoading" class="text-center py-5">
      <v-progress-circular indeterminate color="primary" />
      <div class="mt-2">데이터 로딩 중...</div>
    </div>

    <!-- 계약자 미선택 -->
    <div v-else-if="!contractorId" class="text-center py-5 text-muted">계약자를 선택해주세요.</div>

    <!-- 상담 내역이 없음 -->
    <div v-else-if="filteredList.length === 0" class="text-center py-5 text-muted">
      <v-icon icon="mdi-message-text-outline" size="large" class="mb-2" />
      <div>상담 내역이 없습니다.</div>
    </div>

    <!-- 상담 내역 리스트 -->
    <CTable v-else hover responsive>
      <colgroup>
        <col width="20%" />
        <col width="10%" />
        <col width="10%" />
        <col width="32%" />
        <col width="10%" />
        <col width="18%" />
      </colgroup>
      <CTableHead>
        <CTableRow class="text-center">
          <CTableHeaderCell>상담일자</CTableHeaderCell>
          <CTableHeaderCell>채널</CTableHeaderCell>
          <CTableHeaderCell>유형</CTableHeaderCell>
          <CTableHeaderCell>제목</CTableHeaderCell>
          <CTableHeaderCell>처리상태</CTableHeaderCell>
          <CTableHeaderCell>작업</CTableHeaderCell>
        </CTableRow>
      </CTableHead>
      <CTableBody>
        <template v-for="log in filteredList" :key="log.pk">
          <!-- 메인 행 -->
          <CTableRow @click="toggleRow(log.pk!)" class="pointer">
            <CTableDataCell class="text-center">
              <div class="d-flex align-items-center justify-content-center gap-1">
                <v-icon v-if="log.is_important" icon="mdi-star" color="warning" size="18" />
                {{ log.consultation_date }}
              </div>
            </CTableDataCell>
            <CTableDataCell class="text-center">
              <v-chip size="x-small">{{ log.channel_display }}</v-chip>
            </CTableDataCell>
            <CTableDataCell class="text-center">
              <v-chip size="x-small">{{ log.category_display }}</v-chip>
            </CTableDataCell>
            <CTableDataCell>{{ cutString(log.title, 11) }}</CTableDataCell>
            <CTableDataCell class="text-center">
              <v-chip :color="getStatusColor(log.status)" size="small">
                {{ log.status_display }}
              </v-chip>
            </CTableDataCell>
            <CTableDataCell class="text-center">
              <v-btn
                size="x-small"
                icon="mdi-pencil"
                variant="text"
                color="success"
                @click.stop="startEdit(log)"
              />
              <v-btn
                size="x-small"
                icon="mdi-delete"
                variant="text"
                color="grey"
                @click.stop="deleteLog(log.pk!)"
              />
            </CTableDataCell>
          </CTableRow>

          <!-- 확장 행 -->
          <CTableRow v-if="expandedRow === log.pk">
            <CTableDataCell colspan="6" class="bg-yellow-lighten-5">
              <!-- 수정 모드 -->
              <div v-if="editingLog && editingLog.pk === log.pk" class="p-3">
                <CRow class="g-2">
                  <CCol :md="3">
                    <CFormLabel>상담일자</CFormLabel>
                    <CFormInput v-model="editingLog.consultation_date" type="date" size="sm" />
                  </CCol>
                  <CCol :md="2">
                    <CFormLabel>채널</CFormLabel>
                    <CFormSelect v-model="editingLog.channel" size="sm">
                      <option value="visit">방문</option>
                      <option value="phone">전화</option>
                      <option value="email">이메일</option>
                      <option value="sms">문자</option>
                      <option value="kakao">카카오톡</option>
                      <option value="other">기타</option>
                    </CFormSelect>
                  </CCol>
                  <CCol :md="2">
                    <CFormLabel>유형</CFormLabel>
                    <CFormSelect v-model="editingLog.category" size="sm">
                      <option value="payment">납부상담</option>
                      <option value="contract">계약상담</option>
                      <option value="change">변경상담</option>
                      <option value="complaint">민원/불만</option>
                      <option value="question">문의</option>
                      <option value="succession">승계상담</option>
                      <option value="release">해지상담</option>
                      <option value="document">서류관련</option>
                      <option value="etc">기타</option>
                    </CFormSelect>
                  </CCol>
                  <CCol :md="2">
                    <CFormLabel>처리상태</CFormLabel>
                    <CFormSelect v-model="editingLog.status" size="sm">
                      <option value="1">처리대기</option>
                      <option value="2">처리중</option>
                      <option value="3">처리완료</option>
                      <option value="4">보류</option>
                    </CFormSelect>
                  </CCol>
                  <CCol :md="3">
                    <CFormLabel>중요도</CFormLabel>
                    <CFormSelect v-model="editingLog.priority" size="sm">
                      <option value="low">낮음</option>
                      <option value="normal">보통</option>
                      <option value="high">높음</option>
                      <option value="urgent">긴급</option>
                    </CFormSelect>
                  </CCol>
                </CRow>

                <CRow class="g-2 mt-2">
                  <CCol :md="12">
                    <CFormLabel>제목</CFormLabel>
                    <CFormInput v-model="editingLog.title" size="sm" />
                  </CCol>
                </CRow>

                <CRow class="g-2 mt-2">
                  <CCol :md="12">
                    <CFormLabel>내용</CFormLabel>
                    <CFormTextarea v-model="editingLog.content" rows="4" size="sm" />
                  </CCol>
                </CRow>

                <CRow class="g-2 mt-2">
                  <CCol :md="12">
                    <CFormLabel>후속조치 내용</CFormLabel>
                    <CFormTextarea v-model="editingLog.follow_up_note" rows="2" size="sm" />
                  </CCol>
                </CRow>

                <CRow class="mt-3">
                  <CCol class="text-end">
                    <v-btn color="secondary" size="small" @click="cancelEdit" class="me-2">
                      취소
                    </v-btn>
                    <v-btn color="success" size="small" @click="saveEdit">저장</v-btn>
                  </CCol>
                </CRow>
              </div>

              <!-- 상세보기 모드 -->
              <div v-else class="p-3">
                <CRow>
                  <CCol :md="12" class="mb-2">
                    <strong>[{{ log.title }}]</strong>
                  </CCol>
                </CRow>
                <CRow>
                  <CCol :md="12" class="mb-2">
                    <div class="mt-1">{{ log.content || '내용 없음' }}</div>
                  </CCol>
                </CRow>
                <CRow v-if="log.follow_up_note" class="mt-2">
                  <CCol :md="12">
                    <strong>후속조치:</strong>
                    <div class="mt-1">{{ log.follow_up_note }}</div>
                  </CCol>
                </CRow>
                <CRow class="mt-2">
                  <CCol :md="6">
                    <small class="text-muted">
                      담당자: {{ log.consultant?.username || '미지정' }}
                    </small>
                  </CCol>
                  <CCol :md="6" class="text-end">
                    <small class="text-muted">등록: {{ log.created }}</small>
                  </CCol>
                </CRow>
              </div>
            </CTableDataCell>
          </CTableRow>
        </template>
      </CTableBody>
    </CTable>

    <!-- 페이지네이션 -->
    <div v-if="pagination.count > 0" class="d-flex justify-content-center mt-3">
      <v-pagination
        :length="Math.ceil(pagination.count / pagination.pageSize)"
        :model-value="pagination.page"
        @update:model-value="onPageChange"
        :total-visible="7"
        size="small"
      />
    </div>
  </CCardBody>
</template>
