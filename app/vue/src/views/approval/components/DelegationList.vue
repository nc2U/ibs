<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useApproval } from '@/store/pinia/approval'
import { useAccount } from '@/store/pinia/account'
import type { ApprovalDelegation } from '@/store/types/approval'
import {
  CBadge,
  CCard,
  CCardBody,
  CCardHeader,
  CButton,
  CModal,
  CModalHeader,
  CModalTitle,
  CModalBody,
  CModalFooter,
  CForm,
  CFormInput,
  CFormTextarea,
  CFormSwitch,
} from '@coreui/vue'

const approvalStore = useApproval()
const accStore = useAccount()

const { delegationList } = storeToRefs(approvalStore)
const { usersList, userInfo } = storeToRefs(accStore)
const { fetchDelegationList, createDelegation, updateDelegation, deleteDelegation } = approvalStore
const { fetchUsersList } = accStore

const isModalOpen = ref(false)
const editingId = ref<number | null>(null)
const formValidated = ref(false)

const form = ref({
  delegatee_id: '' as number | '',
  start_date: '',
  end_date: '',
  reason: '',
  is_active: true,
})

const availableUsers = computed(() =>
  usersList.value
    .filter(
      u => u.pk !== userInfo.value?.pk && u.is_active && (u.has_staff || u.is_superuser),
    )
    .map(u => ({
      value: u.pk,
      title: u.profile?.name ? `${u.profile.name} (${u.username})` : u.username,
    })),
)

onMounted(async () => {
  await Promise.all([fetchDelegationList(), fetchUsersList()])
})

const openCreateModal = () => {
  editingId.value = null
  const today = new Date().toISOString().split('T')[0]
  const nextWeek = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
  form.value = {
    delegatee_id: '',
    start_date: today,
    end_date: nextWeek,
    reason: '',
    is_active: true,
  }
  formValidated.value = false
  isModalOpen.value = true
}

const openEditModal = (item: ApprovalDelegation) => {
  editingId.value = item.id ?? null
  form.value = {
    delegatee_id: item.delegatee?.id ?? (item.delegatee_id || ''),
    start_date: item.start_date,
    end_date: item.end_date,
    reason: item.reason ?? '',
    is_active: item.is_active,
  }
  formValidated.value = false
  isModalOpen.value = true
}

const handleSubmit = async () => {
  if (!form.value.delegatee_id || !form.value.start_date || !form.value.end_date) {
    formValidated.value = true
    return
  }

  const payload: Partial<ApprovalDelegation> = {
    delegatee_id: Number(form.value.delegatee_id),
    start_date: form.value.start_date,
    end_date: form.value.end_date,
    reason: form.value.reason,
    is_active: form.value.is_active,
  }

  if (editingId.value) {
    await updateDelegation(editingId.value, payload)
  } else {
    await createDelegation(payload)
  }

  isModalOpen.value = false
}

const handleDelete = async (id: number) => {
  if (confirm('해당 결재 위임 설정을 삭제하시겠습니까?')) {
    await deleteDelegation(id)
  }
}

const toggleActive = async (item: ApprovalDelegation) => {
  if (item.id) {
    await updateDelegation(item.id, { is_active: !item.is_active })
  }
}
</script>

<template>
  <div>
    <!-- 상단 안내 배너 -->
    <v-alert
      type="info"
      variant="tonal"
      density="comfortable"
      class="mb-4 text-body-2"
      icon="mdi-account-switch"
    >
      <strong>부재 및 결재 위임(대결·代決) 안내:</strong><br />
      출장, 휴가, 병가 등으로 결재 처리가 어려울 때 본인의 결재 권한을 특정 직원에게 지정된 기간 동안 위임할 수 있습니다.<br />
      위임 기간 중에는 대결자가 대신 결재(승인/반려)를 수행하며, 모든 결재 내역에 대결 사실이 공식 기록됩니다.
    </v-alert>

    <CCard class="mb-4">
      <CCardHeader class="d-flex justify-content-between align-items-center py-3">
        <h6 class="mb-0 fw-bold">
          <v-icon icon="mdi-shield-account-outline" class="me-1" color="primary" />
          결재 권한 위임(대결) 설정 목록
        </h6>
        <CButton color="primary" size="sm" @click="openCreateModal">
          <v-icon icon="mdi-plus" size="16" class="me-1" />
          신규 대결자 지정
        </CButton>
      </CCardHeader>

      <CCardBody class="p-0">
        <v-table hover density="comfortable">
          <thead>
            <tr class="bg-light">
              <th class="text-center" style="width: 70px">No</th>
              <th class="text-start" style="width: 160px">위임자 (원권한자)</th>
              <th class="text-start" style="width: 160px">수임자 (대결자)</th>
              <th class="text-center" style="width: 220px">위임 기간</th>
              <th class="text-start">부재 및 위임 사유</th>
              <th class="text-center" style="width: 120px">상태</th>
              <th class="text-center" style="width: 140px">관리</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="delegationList.length === 0">
              <td colspan="7" class="text-center py-5 text-muted">
                등록된 결재 위임 내역이 없습니다.
              </td>
            </tr>
            <tr v-for="(item, idx) in delegationList" :key="item.id">
              <td class="text-center text-muted small">{{ idx + 1 }}</td>
              <td class="fw-semibold">
                {{ item.delegator?.full_name ?? item.delegator?.username }}
                <v-chip v-if="item.delegator?.id === userInfo?.pk" size="x-small" color="primary" class="ms-1">본인</v-chip>
              </td>
              <td class="fw-semibold text-primary">
                {{ item.delegatee?.full_name ?? item.delegatee?.username }}
                <v-chip v-if="item.delegatee?.id === userInfo?.pk" size="x-small" color="success" class="ms-1">수임(대결)</v-chip>
              </td>
              <td class="text-center small">
                {{ item.start_date }} ~ {{ item.end_date }}
              </td>
              <td class="small text-truncate" style="max-width: 250px">
                {{ item.reason || '-' }}
              </td>
              <td class="text-center">
                <CBadge v-if="item.is_valid_now" color="success">진행중 (유효)</CBadge>
                <CBadge v-else-if="item.is_active" color="info">대기 / 예정</CBadge>
                <CBadge v-else color="secondary">비활성 (해제)</CBadge>
              </td>
              <td class="text-center">
                <div class="d-flex justify-content-center gap-1">
                  <v-btn
                    size="x-small"
                    variant="text"
                    :color="item.is_active ? 'warning' : 'success'"
                    :title="item.is_active ? '위임 일시정지' : '위임 활성화'"
                    @click="toggleActive(item)"
                  >
                    {{ item.is_active ? '해제' : '활성' }}
                  </v-btn>
                  <v-btn
                    size="x-small"
                    variant="text"
                    color="primary"
                    title="수정"
                    @click="openEditModal(item)"
                  >
                    수정
                  </v-btn>
                  <v-btn
                    size="x-small"
                    variant="text"
                    color="error"
                    title="삭제"
                    @click="handleDelete(item.id!)"
                  >
                    삭제
                  </v-btn>
                </div>
              </td>
            </tr>
          </tbody>
        </v-table>
      </CCardBody>
    </CCard>

    <!-- 대결자 등록 / 수정 모달 -->
    <CModal :visible="isModalOpen" backdrop="static" @close="isModalOpen = false">
      <CModalHeader>
        <CModalTitle class="h6 mb-0 fw-bold">
          {{ editingId ? '결재 위임(대결) 설정 수정' : '신규 결재 위임(대결) 지정' }}
        </CModalTitle>
      </CModalHeader>
      <CModalBody>
        <CForm :validated="formValidated">
          <!-- 대결자 선택 -->
          <div class="mb-3">
            <label class="form-label small fw-semibold">대결자 (수임자) 선택 <span class="text-danger">*</span></label>
            <v-select
              v-model="form.delegatee_id"
              :items="availableUsers"
              item-title="title"
              item-value="value"
              placeholder="대결을 위임할 직원을 선택하세요"
              density="compact"
              variant="outlined"
              hide-details
            />
            <div v-if="formValidated && !form.delegatee_id" class="text-danger small mt-1">
              대결자를 선택해 주세요.
            </div>
          </div>

          <!-- 위임 기간 -->
          <div class="row g-2 mb-3">
            <div class="col-6">
              <label class="form-label small fw-semibold">위임 시작일 <span class="text-danger">*</span></label>
              <CFormInput
                v-model="form.start_date"
                type="date"
                size="sm"
                required
              />
            </div>
            <div class="col-6">
              <label class="form-label small fw-semibold">위임 종료일 <span class="text-danger">*</span></label>
              <CFormInput
                v-model="form.end_date"
                type="date"
                size="sm"
                required
              />
            </div>
          </div>

          <!-- 위임 사유 -->
          <div class="mb-3">
            <label class="form-label small fw-semibold">부재 및 위임 사유</label>
            <CFormTextarea
              v-model="form.reason"
              rows="2"
              size="sm"
              placeholder="예: 하기 휴가로 인한 결재 권한 위임, 해외 출장 등"
            />
          </div>

          <!-- 활성화 토글 -->
          <div class="d-flex align-items-center justify-content-between p-2 bg-light rounded">
            <span class="small fw-semibold">대결 권한 즉시 활성화</span>
            <CFormSwitch
              v-model="form.is_active"
              id="delegationActiveSwitch"
            />
          </div>
        </CForm>
      </CModalBody>
      <CModalFooter>
        <CButton color="secondary" size="sm" @click="isModalOpen = false">취소</CButton>
        <CButton color="primary" size="sm" @click="handleSubmit">
          {{ editingId ? '수정 저장' : '위임 등록' }}
        </CButton>
      </CModalFooter>
    </CModal>
  </div>
</template>
